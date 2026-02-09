from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from models import QCValidation, QCValidationCreate, UnitStatus
from services import get_current_user
from middleware.permissions import require_permission

router = APIRouter(prefix="/qc-validation", tags=["QC Validation"])

def enrich_qc_validation(item: dict) -> dict:
    """Add missing fields to QC validation for frontend compatibility"""
    if not item:
        return item
    
    # Ensure unit_component_id and unit_type are set
    if not item.get("unit_component_id") and item.get("component_id"):
        item["unit_component_id"] = item["component_id"]
    if not item.get("unit_type"):
        item["unit_type"] = "component"
    
    # Ensure checklist fields have boolean values
    if item.get("data_complete") is None:
        item["data_complete"] = False
    if item.get("screening_complete") is None:
        item["screening_complete"] = False
    if item.get("custody_complete") is None:
        item["custody_complete"] = False
    
    return item

@router.post("")
async def create_qc_validation(
    validation_data: QCValidationCreate, 
    current_user: dict = Depends(require_permission("qc_validation", "create"))
):
    validation = QCValidation(**validation_data.model_dump())
    
    if validation.data_complete and validation.screening_complete and validation.custody_complete:
        validation.status = "approved"
        validation.approved_by = current_user["id"]
        validation.approval_timestamp = datetime.now(timezone.utc)
    else:
        validation.status = "hold"
        missing = []
        if not validation.data_complete:
            missing.append("data incomplete")
        if not validation.screening_complete:
            missing.append("screening incomplete")
        if not validation.custody_complete:
            missing.append("custody incomplete")
        validation.hold_reason = ", ".join(missing)
    
    doc = validation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('approval_timestamp'):
        doc['approval_timestamp'] = doc['approval_timestamp'].isoformat()
    
    await db.qc_validation.insert_one(doc)
    
    if validation.status == "approved":
        new_status = UnitStatus.READY_TO_USE.value
        if validation.unit_type == "unit":
            await db.blood_units.update_one(
                {"id": validation.unit_component_id},
                {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        else:
            await db.components.update_one(
                {"id": validation.unit_component_id},
                {"$set": {"status": new_status}}
            )
    
    return {"status": "success", "validation_id": validation.id, "qc_status": validation.status}

@router.get("")
async def get_qc_validations(
    status: Optional[str] = None,
    current_user: dict = Depends(require_permission("qc_validation", "view"))
):
    query = {}
    if status:
        query["status"] = status
    
    validations = await db.qc_validation.find(query, {"_id": 0}).to_list(1000)
    return [enrich_qc_validation(v) for v in validations]

@router.put("/{validation_id}/approve")
async def approve_qc_validation(
    validation_id: str, 
    current_user: dict = Depends(require_permission("qc_validation", "approve"))
):
    validation = await db.qc_validation.find_one({"id": validation_id}, {"_id": 0})
    if not validation:
        raise HTTPException(status_code=404, detail="Validation record not found")
    
    await db.qc_validation.update_one(
        {"id": validation_id},
        {
            "$set": {
                "status": "approved",
                "approved_by": current_user["id"],
                "approval_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if validation["unit_type"] == "unit":
        await db.blood_units.update_one(
            {"id": validation["unit_component_id"]},
            {"$set": {"status": UnitStatus.READY_TO_USE.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db.components.update_one(
            {"id": validation["unit_component_id"]},
            {"$set": {"status": UnitStatus.READY_TO_USE.value}}
        )
    
    return {"status": "success"}
