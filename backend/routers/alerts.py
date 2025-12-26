from fastapi import APIRouter, Depends
from typing import Optional, List
from datetime import datetime, timezone, timedelta

import sys
sys.path.append('..')

from database import db
from services import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/summary")
async def get_alerts_summary(current_user: dict = Depends(get_current_user)):
    """Get summary of all active alerts"""
    now = datetime.now(timezone.utc)
    today = now.isoformat().split("T")[0]
    
    # Expiring items (within 7 days)
    expiring_7_days = now + timedelta(days=7)
    expiring_3_days = now + timedelta(days=3)
    
    # Count expiring units
    expiring_units_7 = await db.blood_units.count_documents({
        "status": "ready_to_use",
        "expiry_date": {"$lte": expiring_7_days.isoformat().split("T")[0], "$gt": today}
    })
    
    expiring_units_3 = await db.blood_units.count_documents({
        "status": "ready_to_use",
        "expiry_date": {"$lte": expiring_3_days.isoformat().split("T")[0], "$gt": today}
    })
    
    # Already expired
    expired_units = await db.blood_units.count_documents({
        "status": "ready_to_use",
        "expiry_date": {"$lt": today}
    })
    
    # Expiring components
    expiring_components_7 = await db.components.count_documents({
        "status": "ready_to_use",
        "expiry_date": {"$lte": expiring_7_days.isoformat().split("T")[0], "$gt": today}
    })
    
    # Low stock alerts (less than 5 units per blood group)
    low_stock_groups = []
    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    
    for bg in blood_groups:
        count = await db.blood_units.count_documents({
            "status": "ready_to_use",
            "$or": [{"blood_group": bg}, {"confirmed_blood_group": bg}]
        })
        if count < 5:
            low_stock_groups.append({"blood_group": bg, "count": count, "threshold": 5})
    
    # Pending donor requests
    pending_requests = await db.donor_requests.count_documents({"status": "pending"})
    
    # Quarantine items
    quarantine_count = await db.quarantine.count_documents({"disposition": None})
    
    # Pending QC validations
    pending_qc = await db.blood_units.count_documents({"status": "processing"})
    pending_qc += await db.components.count_documents({"status": "processing"})
    
    # Pending blood requests
    pending_blood_requests = await db.blood_requests.count_documents({"status": "pending"})
    urgent_requests = await db.blood_requests.count_documents({"status": "pending", "urgency": {"$in": ["urgent", "emergency"]}})
    
    return {
        "expiry_alerts": {
            "expired_units": expired_units,
            "expiring_within_3_days": expiring_units_3,
            "expiring_within_7_days": expiring_units_7,
            "expiring_components_7_days": expiring_components_7
        },
        "stock_alerts": {
            "low_stock_groups": low_stock_groups,
            "critical_count": len([g for g in low_stock_groups if g["count"] == 0])
        },
        "operational_alerts": {
            "pending_donor_requests": pending_requests,
            "quarantine_items": quarantine_count,
            "pending_qc_validations": pending_qc,
            "pending_blood_requests": pending_blood_requests,
            "urgent_blood_requests": urgent_requests
        },
        "total_critical_alerts": expired_units + len([g for g in low_stock_groups if g["count"] == 0]) + urgent_requests,
        "generated_at": now.isoformat()
    }

@router.get("/expiring-items")
async def get_expiring_items(
    days: int = 7,
    item_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed list of expiring items"""
    now = datetime.now(timezone.utc)
    expiry_date = (now + timedelta(days=days)).isoformat().split("T")[0]
    today = now.isoformat().split("T")[0]
    
    results = {"units": [], "components": []}
    
    if item_type in [None, "units"]:
        units = await db.blood_units.find({
            "status": "ready_to_use",
            "expiry_date": {"$lte": expiry_date, "$gte": today}
        }, {"_id": 0}).sort("expiry_date", 1).to_list(100)
        results["units"] = units
    
    if item_type in [None, "components"]:
        components = await db.components.find({
            "status": "ready_to_use",
            "expiry_date": {"$lte": expiry_date, "$gte": today}
        }, {"_id": 0}).sort("expiry_date", 1).to_list(100)
        results["components"] = components
    
    return results

@router.get("/low-stock")
async def get_low_stock_details(
    threshold: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed low stock information by blood group and component type"""
    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    component_types = ["prc", "plasma", "ffp", "platelets", "cryoprecipitate"]
    
    stock_details = []
    
    for bg in blood_groups:
        # Whole blood units
        unit_count = await db.blood_units.count_documents({
            "status": "ready_to_use",
            "$or": [{"blood_group": bg}, {"confirmed_blood_group": bg}]
        })
        
        stock_details.append({
            "blood_group": bg,
            "type": "whole_blood",
            "count": unit_count,
            "threshold": threshold,
            "is_low": unit_count < threshold,
            "is_critical": unit_count == 0
        })
        
        # Components by type
        for comp_type in component_types:
            comp_count = await db.components.count_documents({
                "status": "ready_to_use",
                "blood_group": bg,
                "component_type": comp_type
            })
            
            stock_details.append({
                "blood_group": bg,
                "type": comp_type,
                "count": comp_count,
                "threshold": threshold,
                "is_low": comp_count < threshold,
                "is_critical": comp_count == 0
            })
    
    # Filter to only low stock items
    low_stock_items = [item for item in stock_details if item["is_low"]]
    critical_items = [item for item in stock_details if item["is_critical"]]
    
    return {
        "low_stock_items": low_stock_items,
        "critical_items": critical_items,
        "summary": {
            "total_low_stock": len(low_stock_items),
            "total_critical": len(critical_items)
        }
    }

@router.get("/urgent-requests")
async def get_urgent_requests(current_user: dict = Depends(get_current_user)):
    """Get all urgent and emergency blood requests"""
    requests = await db.blood_requests.find({
        "status": "pending",
        "urgency": {"$in": ["urgent", "emergency"]}
    }, {"_id": 0}).sort([("urgency", -1), ("requested_date", 1)]).to_list(100)
    
    return {
        "urgent_requests": requests,
        "emergency_count": len([r for r in requests if r.get("urgency") == "emergency"]),
        "urgent_count": len([r for r in requests if r.get("urgency") == "urgent"])
    }
