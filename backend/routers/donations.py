from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from models import Donation, DonationCreate, BloodUnit, UnitStatus
from services import (
    get_current_user, generate_donation_id, generate_unit_id, generate_barcode_base64
)

router = APIRouter(prefix="/donations", tags=["Donations"])

@router.post("")
async def create_donation(donation_data: DonationCreate, current_user: dict = Depends(get_current_user)):
    screening = await db.screenings.find_one({"id": donation_data.screening_id}, {"_id": 0})
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")
    if screening["eligibility_status"] != "eligible":
        raise HTTPException(status_code=400, detail="Donor not eligible for donation")
    
    donation = Donation(**donation_data.model_dump())
    donation.donation_id = await generate_donation_id()
    donation.phlebotomist_id = current_user["id"]
    
    doc = donation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.donations.insert_one(doc)
    return {"status": "success", "donation_id": donation.donation_id, "id": donation.id}

@router.put("/{donation_id}/complete")
async def complete_donation(
    donation_id: str,
    volume: float,
    adverse_reaction: bool = False,
    adverse_reaction_details: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    donation = await db.donations.find_one(
        {"$or": [{"id": donation_id}, {"donation_id": donation_id}]},
        {"_id": 0}
    )
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    
    update_data = {
        "collection_end_time": datetime.now(timezone.utc).isoformat(),
        "volume_collected": volume,
        "adverse_reaction": adverse_reaction,
        "adverse_reaction_details": adverse_reaction_details,
        "status": "completed"
    }
    
    await db.donations.update_one(
        {"$or": [{"id": donation_id}, {"donation_id": donation_id}]},
        {"$set": update_data}
    )
    
    donor = await db.donors.find_one({"id": donation["donor_id"]}, {"_id": 0})
    if donor:
        await db.donors.update_one(
            {"id": donation["donor_id"]},
            {
                "$set": {
                    "last_donation_date": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$inc": {"total_donations": 1}
            }
        )
    
    unit_id = await generate_unit_id()
    screening = await db.screenings.find_one({"id": donation["screening_id"]}, {"_id": 0})
    
    blood_unit = BloodUnit(
        unit_id=unit_id,
        donor_id=donation["donor_id"],
        donation_id=donation["id"],
        bag_barcode=generate_barcode_base64(unit_id),
        sample_labels=[f"{unit_id}-S1", f"{unit_id}-S2"],
        blood_group=screening.get("preliminary_blood_group") if screening else None,
        collection_date=datetime.now(timezone.utc).isoformat().split("T")[0],
        volume=volume,
        created_by=current_user["id"]
    )
    
    unit_doc = blood_unit.model_dump()
    unit_doc['created_at'] = unit_doc['created_at'].isoformat()
    unit_doc['updated_at'] = unit_doc['updated_at'].isoformat()
    
    await db.blood_units.insert_one(unit_doc)
    
    return {
        "status": "success",
        "unit_id": unit_id,
        "barcode": blood_unit.bag_barcode
    }

@router.get("")
async def get_donations(
    donor_id: Optional[str] = None,
    date: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if donor_id:
        query["donor_id"] = donor_id
    if date:
        query["collection_start_time"] = {"$regex": f"^{date}"}
    if status:
        query["status"] = status
    
    donations = await db.donations.find(query, {"_id": 0}).to_list(1000)
    return donations
