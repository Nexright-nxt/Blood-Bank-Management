from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from models import UnitStatus, ScreeningResult
from services import get_current_user

router = APIRouter(prefix="/quarantine", tags=["Quarantine"])

def enrich_quarantine_item(item: dict) -> dict:
    """Add missing fields to quarantine item for frontend compatibility"""
    if not item:
        return item
    
    # Ensure unit_component_id is set (frontend expects this)
    if not item.get("unit_component_id") and item.get("component_id"):
        item["unit_component_id"] = item["component_id"]
    
    # Ensure reason is set (frontend expects 'reason', seeder might have 'quarantine_reason')
    if not item.get("reason") and item.get("quarantine_reason"):
        item["reason"] = item["quarantine_reason"]
    
    # Ensure unit_type is set
    if not item.get("unit_type"):
        item["unit_type"] = "component"
    
    return item

@router.get("")
async def get_quarantine_items(current_user: dict = Depends(get_current_user)):
    items = await db.quarantine.find({"disposition": None}, {"_id": 0}).to_list(1000)
    return [enrich_quarantine_item(item) for item in items]

@router.put("/{quarantine_id}/resolve")
async def resolve_quarantine(
    quarantine_id: str,
    retest_result: ScreeningResult,
    disposition: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["admin", "qc_manager", "lab_tech"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    update_data = {
        "retest_result": retest_result.value,
        "disposition": disposition,
        "resolved_date": datetime.now(timezone.utc).isoformat().split("T")[0],
        "resolved_by": current_user["id"]
    }
    
    quarantine = await db.quarantine.find_one({"id": quarantine_id}, {"_id": 0})
    if not quarantine:
        raise HTTPException(status_code=404, detail="Quarantine record not found")
    
    await db.quarantine.update_one({"id": quarantine_id}, {"$set": update_data})
    
    new_status = UnitStatus.READY_TO_USE.value if disposition == "release" else UnitStatus.DISCARDED.value
    
    if quarantine["unit_type"] == "unit":
        await db.blood_units.update_one(
            {"id": quarantine["unit_component_id"]},
            {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db.components.update_one(
            {"id": quarantine["unit_component_id"]},
            {"$set": {"status": new_status}}
        )
    
    return {"status": "success"}
