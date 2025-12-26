from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from models import Screening, ScreeningCreate
from services import get_current_user

router = APIRouter(prefix="/screenings", tags=["Screening"])

@router.post("")
async def create_screening(screening_data: ScreeningCreate, current_user: dict = Depends(get_current_user)):
    donor = await db.donors.find_one({"id": screening_data.donor_id}, {"_id": 0})
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    
    screening = Screening(**screening_data.model_dump())
    screening.screened_by = current_user["id"]
    
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
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if donor_id:
        query["donor_id"] = donor_id
    if date:
        query["screening_date"] = date
    
    screenings = await db.screenings.find(query, {"_id": 0}).to_list(1000)
    return screenings

@router.get("/{screening_id}")
async def get_screening(screening_id: str, current_user: dict = Depends(get_current_user)):
    screening = await db.screenings.find_one({"id": screening_id}, {"_id": 0})
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")
    return screening
