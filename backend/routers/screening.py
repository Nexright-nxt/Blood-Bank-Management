from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from models import Screening, ScreeningCreate
from services import get_current_user
from middleware import ReadAccess, WriteAccess, OrgAccessHelper
from middleware.permissions import require_permission

router = APIRouter(prefix="/screenings", tags=["Screening"])

@router.post("")
async def create_screening(
    screening_data: ScreeningCreate, 
    current_user: dict = Depends(require_permission("screening", "create")),
    access: OrgAccessHelper = Depends(WriteAccess)
):
    donor = await db.donors.find_one(
        access.filter({"id": screening_data.donor_id}), 
        {"_id": 0}
    )
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    screening = Screening(**screening_data.model_dump())
    screening.screened_by = current_user["id"]
    screening.org_id = donor.get("org_id") or access.get_default_org_id()
    
    issues = []
    if screening.hemoglobin < 12.5:
        issues.append("Hemoglobin below minimum (12.5 g/dL)")
    if screening.weight < 45:
        issues.append("Weight below minimum (45 kg)")
    if screening.blood_pressure_systolic < 90 or screening.blood_pressure_systolic > 180:
        issues.append("Blood pressure systolic out of range (90-180)")
    if screening.blood_pressure_diastolic < 60 or screening.blood_pressure_diastolic > 100:
        issues.append("Blood pressure diastolic out of range (60-100)")
    if screening.pulse < 50 or screening.pulse > 100:
        issues.append("Pulse rate out of range (50-100)")
    if screening.temperature < 36.0 or screening.temperature > 37.5:
        issues.append("Temperature out of range (36.0-37.5)")
    if not screening.questionnaire_passed:
        issues.append("Health questionnaire not passed")
    
    if issues:
        screening.eligibility_status = "ineligible"
        screening.rejection_reason = "; ".join(issues)
    else:
        screening.eligibility_status = "eligible"
    
    doc = screening.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.screenings.insert_one(doc)
    return {
        "status": "success",
        "screening_id": screening.id,
        "eligibility_status": screening.eligibility_status,
        "rejection_reason": screening.rejection_reason
    }

@router.get("")
async def get_screenings(
    donor_id: Optional[str] = None,
    date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(require_permission("screening", "view")),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    query = {}
    if donor_id:
        query["donor_id"] = donor_id
    if date:
        query["screening_date"] = date
    if status:
        query["eligibility_status"] = status
    
    screenings = await db.screenings.find(access.filter(query), {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Enrich with donor info
    for screening in screenings:
        donor = await db.donors.find_one({"id": screening.get("donor_id")}, {"_id": 0, "full_name": 1, "donor_id": 1, "blood_group": 1})
        if donor:
            screening["donor_name"] = donor.get("full_name")
            screening["donor_code"] = donor.get("donor_id")
            screening["blood_group"] = donor.get("blood_group")
    
    return screenings


@router.get("/pending/donors")
async def get_pending_screening_donors(
    current_user: dict = Depends(require_permission("screening", "view")),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    """Get donors who need screening (registered but not screened today, or eligible to donate again)"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get all active donors for accessible orgs
    donors = await db.donors.find(
        access.filter({"status": "active"}),
        {"_id": 0}
    ).to_list(1000)
    
    pending_donors = []
    for donor in donors:
        # Check if already screened today
        today_screening = await db.screenings.find_one({
            "donor_id": donor["id"],
            "screening_date": today
        })
        
        if not today_screening:
            # Check last screening status
            last_screening = await db.screenings.find_one(
                {"donor_id": donor["id"]},
                {"_id": 0},
                sort=[("created_at", -1)]
            )
            
            pending_donors.append({
                "id": donor["id"],
                "donor_id": donor.get("donor_id"),
                "full_name": donor.get("full_name"),
                "blood_group": donor.get("blood_group"),
                "phone": donor.get("phone"),
                "last_screening_date": last_screening.get("screening_date") if last_screening else None,
                "last_screening_status": last_screening.get("eligibility_status") if last_screening else None,
            })
    
    return pending_donors


@router.get("/today/summary")
async def get_today_screening_summary(
    current_user: dict = Depends(require_permission("screening", "view")),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    """Get summary of today's screenings"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    total = await db.screenings.count_documents(access.filter({"screening_date": today}))
    eligible = await db.screenings.count_documents(access.filter({"screening_date": today, "eligibility_status": "eligible"}))
    ineligible = await db.screenings.count_documents(access.filter({"screening_date": today, "eligibility_status": "ineligible"}))
    
    return {
        "date": today,
        "total": total,
        "eligible": eligible,
        "ineligible": ineligible,
    }

@router.get("/{screening_id}")
async def get_screening(
    screening_id: str, 
    current_user: dict = Depends(require_permission("screening", "view")),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    screening = await db.screenings.find_one(access.filter({"id": screening_id}), {"_id": 0})
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")
    return screening
