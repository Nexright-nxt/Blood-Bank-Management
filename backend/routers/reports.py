from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone, timedelta
import csv
import io

import sys
sys.path.append('..')

from database import db
from services import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

def generate_csv(data: list, headers: list) -> io.StringIO:
    """Generate CSV from data"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in data:
        writer.writerow({k: row.get(k, '') for k in headers})
    output.seek(0)
    return output

@router.get("/daily-collections")
async def get_daily_collections_report(
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if not date:
        date = datetime.now(timezone.utc).isoformat().split("T")[0]
    
    donations = await db.donations.find({
        "collection_start_time": {"$regex": f"^{date}"}
    }, {"_id": 0}).to_list(1000)
    
    total_volume = sum(d.get("volume_collected", 0) or 0 for d in donations)
    
    by_type = {}
    for d in donations:
        dtype = d.get("donation_type", "unknown")
        if dtype not in by_type:
            by_type[dtype] = {"count": 0, "volume": 0}
        by_type[dtype]["count"] += 1
        by_type[dtype]["volume"] += d.get("volume_collected", 0) or 0
    
    # Get screenings for the day
    screenings = await db.screenings.find({
        "screening_date": date
    }, {"_id": 0}).to_list(1000)
    
    failed_screenings = [s for s in screenings if s.get("result") == "rejected"]
    
    adverse_reactions = [d for d in donations if d.get("adverse_reaction")]
    
    return {
        "date": date,
        "total_donations": len(donations),
        "total_volume": total_volume,
        "by_type": by_type,
        "rejections": len(failed_screenings),
        "failed_screenings": len(failed_screenings),
        "adverse_reactions_count": len(adverse_reactions),
        "adverse_reactions": adverse_reactions
    }

@router.get("/inventory-status")
async def get_inventory_status_report(current_user: dict = Depends(get_current_user)):
    # Blood units by status
    by_blood_group = {}
    for bg in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]:
        whole_blood = await db.blood_units.count_documents({
            "confirmed_blood_group": bg,
            "status": "ready_to_use"
        })
        components = await db.components.count_documents({
            "blood_group": bg,
            "status": "ready_to_use"
        })
        by_blood_group[bg] = {
            "whole_blood": whole_blood,
            "components": components
        }
    
    # Components by type
    by_component_type = {}
    for ctype in ["prc", "plasma", "ffp", "platelets", "cryoprecipitate"]:
        count = await db.components.count_documents({
            "component_type": ctype,
            "status": "ready_to_use"
        })
        by_component_type[ctype] = count
    
    return {
        "report_date": datetime.now(timezone.utc).isoformat(),
        "by_blood_group": by_blood_group,
        "by_component_type": by_component_type
    }

@router.get("/expiry-analysis")
async def get_expiry_analysis_report(current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    today = now.isoformat().split("T")[0]
    
    expired = await db.components.count_documents({
        "status": "ready_to_use",
        "expiry_date": {"$lt": today}
    })
    
    expiring_3_days = await db.components.count_documents({
        "status": "ready_to_use",
        "expiry_date": {
            "$gte": today,
            "$lte": (now + timedelta(days=3)).isoformat().split("T")[0]
        }
    })
    
    expiring_7_days = await db.components.count_documents({
        "status": "ready_to_use",
        "expiry_date": {
            "$gte": today,
            "$lte": (now + timedelta(days=7)).isoformat().split("T")[0]
        }
    })
    
    return {
        "report_date": now.isoformat(),
        "expired": expired,
        "expiring_in_3_days": expiring_3_days,
        "expiring_in_7_days": expiring_7_days
    }

@router.get("/discard-analysis")
async def get_discard_analysis_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if start_date:
        query["discard_date"] = {"$gte": start_date}
    if end_date:
        if "discard_date" in query:
            query["discard_date"]["$lte"] = end_date
        else:
            query["discard_date"] = {"$lte": end_date}
    
    discards = await db.discards.find(query, {"_id": 0}).to_list(1000)
    
    by_reason = {}
    for d in discards:
        reason = d.get("reason", "unknown")
        if reason not in by_reason:
            by_reason[reason] = 0
        by_reason[reason] += 1
    
    return {
        "total_discards": len(discards),
        "by_reason": by_reason,
        "period": {"start": start_date, "end": end_date}
    }

@router.get("/testing-outcomes")
async def get_testing_outcomes_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if start_date:
        query["test_date"] = {"$gte": start_date}
    if end_date:
        if "test_date" in query:
            query["test_date"]["$lte"] = end_date
        else:
            query["test_date"] = {"$lte": end_date}
    
    tests = await db.lab_tests.find(query, {"_id": 0}).to_list(1000)
    
    by_status = {}
    for t in tests:
        status = t.get("overall_status", "pending")
        if status not in by_status:
            by_status[status] = 0
        by_status[status] += 1
    
    reactive_details = {
        "hiv": len([t for t in tests if t.get("hiv_result") == "reactive"]),
        "hbsag": len([t for t in tests if t.get("hbsag_result") == "reactive"]),
        "hcv": len([t for t in tests if t.get("hcv_result") == "reactive"]),
        "syphilis": len([t for t in tests if t.get("syphilis_result") == "reactive"])
    }
    
    return {
        "total_tests": len(tests),
        "by_overall_status": by_status,
        "reactive_breakdown": reactive_details,
        "period": {"start": start_date, "end": end_date}
    }

# ==================== EXPORT ENDPOINTS ====================

@router.get("/export/donors")
async def export_donors(
    status: Optional[str] = None,
    blood_group: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export donors list as CSV"""
    query = {}
    if status:
        query["status"] = status
    if blood_group:
        query["blood_group"] = blood_group
    
    donors = await db.donors.find(query, {"_id": 0, "qr_code": 0}).to_list(10000)
    
    headers = ["donor_id", "full_name", "blood_group", "gender", "phone", "email", "status", "total_donations", "registration_channel"]
    csv_data = generate_csv(donors, headers)
    
    return StreamingResponse(
        iter([csv_data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=donors_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/export/inventory")
async def export_inventory(
    status: Optional[str] = None,
    blood_group: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export inventory as CSV"""
    query = {}
    if status:
        query["status"] = status
    if blood_group:
        query["blood_group"] = blood_group
    
    components = await db.components.find(query, {"_id": 0}).to_list(10000)
    
    headers = ["component_id", "component_type", "blood_group", "volume", "status", "storage_location", "expiry_date", "created_at"]
    csv_data = generate_csv(components, headers)
    
    return StreamingResponse(
        iter([csv_data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=inventory_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/export/donations")
async def export_donations(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export donations as CSV"""
    query = {}
    if start_date:
        query["collection_start_time"] = {"$gte": start_date}
    if end_date:
        if "collection_start_time" in query:
            query["collection_start_time"]["$lte"] = end_date
        else:
            query["collection_start_time"] = {"$lte": end_date}
    
    donations = await db.donations.find(query, {"_id": 0}).to_list(10000)
    
    headers = ["donation_id", "donor_id", "donation_type", "volume_collected", "collection_start_time", "phlebotomist", "status"]
    csv_data = generate_csv(donations, headers)
    
    return StreamingResponse(
        iter([csv_data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=donations_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/export/discards")
async def export_discards(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export discards as CSV"""
    query = {}
    if start_date:
        query["discard_date"] = {"$gte": start_date}
    if end_date:
        if "discard_date" in query:
            query["discard_date"]["$lte"] = end_date
        else:
            query["discard_date"] = {"$lte": end_date}
    
    discards = await db.discards.find(query, {"_id": 0}).to_list(10000)
    
    headers = ["discard_id", "component_id", "reason", "reason_details", "discard_date", "category", "authorized"]
    csv_data = generate_csv(discards, headers)
    
    return StreamingResponse(
        iter([csv_data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=discards_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@router.get("/export/requests")
async def export_requests(
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export blood requests as CSV"""
    query = {}
    if status:
        query["status"] = status
    if start_date:
        query["requested_date"] = {"$gte": start_date}
    if end_date:
        if "requested_date" in query:
            query["requested_date"]["$lte"] = end_date
        else:
            query["requested_date"] = {"$lte": end_date}
    
    requests = await db.blood_requests.find(query, {"_id": 0}).to_list(10000)
    
    headers = ["request_id", "request_type", "requester_name", "hospital_name", "blood_group", "product_type", "quantity", "urgency", "status", "requested_date"]
    csv_data = generate_csv(requests, headers)
    
    return StreamingResponse(
        iter([csv_data.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=requests_export_{datetime.now().strftime('%Y%m%d')}.csv"}
    )
