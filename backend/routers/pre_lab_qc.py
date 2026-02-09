from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from models import PreLabQC, PreLabQCCreate, QCResult, UnitStatus, Quarantine
from services import get_current_user

router = APIRouter(prefix="/pre-lab-qc", tags=["Pre-Lab QC"])

async def generate_pre_qc_id() -> str:
    count = await db.pre_lab_qc.count_documents({})
    return f"PREQC-{datetime.now().year}-{str(count + 1).zfill(5)}"

@router.post("")
async def create_pre_lab_qc(data: PreLabQCCreate, current_user: dict = Depends(get_current_user)):
    """Perform pre-lab QC check on a blood unit"""
    # Check if unit exists
    unit = await db.blood_units.find_one(
        {"$or": [{"id": data.unit_id}, {"unit_id": data.unit_id}]},
        {"_id": 0}
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Blood unit not found")
    
    # Check if already has pre-lab QC
    existing = await db.pre_lab_qc.find_one({"unit_id": unit["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Pre-Lab QC already performed for this unit")
    
    # Determine overall result
    checks = [data.bag_integrity, data.color_appearance, data.clots_visible, 
              data.hemolysis_check, data.volume_adequate]
    overall_result = QCResult.PASS if all(c == QCResult.PASS for c in checks) else QCResult.FAIL
    
    pre_qc = PreLabQC(
        **data.model_dump(),
        overall_result=overall_result,
        inspector_id=current_user["id"],
        inspector_name=current_user.get("full_name", "")
    )
    pre_qc.pre_qc_id = await generate_pre_qc_id()
    pre_qc.unit_id = unit["id"]  # Use internal ID
    
    doc = pre_qc.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.pre_lab_qc.insert_one(doc)
    
    # Update unit status based on result
    if overall_result == QCResult.PASS:
        new_status = UnitStatus.LAB.value
        await db.blood_units.update_one(
            {"id": unit["id"]},
            {"$set": {
                "status": new_status,
                "pre_lab_qc_passed": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        # Move to quarantine
        new_status = UnitStatus.QUARANTINE.value
        await db.blood_units.update_one(
            {"id": unit["id"]},
            {"$set": {
                "status": new_status,
                "pre_lab_qc_passed": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Create quarantine record
        quarantine = Quarantine(
            unit_component_id=unit["id"],
            unit_type="unit",
            reason=f"Pre-Lab QC Failed: {data.failure_reason or 'Visual inspection failed'}",
            quarantine_date=datetime.now(timezone.utc).isoformat().split("T")[0]
        )
        q_doc = quarantine.model_dump()
        q_doc['created_at'] = q_doc['created_at'].isoformat()
        await db.quarantine.insert_one(q_doc)
        
        # Create notification for failed QC
        notification = {
            "id": str(__import__('uuid').uuid4()),
            "role": "qc_manager",
            "alert_type": "warning",
            "title": "Pre-Lab QC Failed",
            "message": f"Unit {unit.get('unit_id')} failed pre-lab QC: {data.failure_reason or 'Visual inspection failed'}",
            "link_to": "/qc-validation",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
    
    return {
        "status": "success",
        "pre_qc_id": pre_qc.pre_qc_id,
        "overall_result": overall_result.value,
        "unit_status": new_status,
        "message": "Unit sent to Lab" if overall_result == QCResult.PASS else "Unit sent to Quarantine"
    }

@router.get("")
async def get_pre_lab_qc_records(
    result: Optional[str] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if result:
        query["overall_result"] = result
    if date:
        query["created_at"] = {"$regex": f"^{date}"}
    
    records = await db.pre_lab_qc.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return records

@router.get("/pending")
async def get_pending_pre_lab_qc(current_user: dict = Depends(get_current_user)):
    """Get blood units that need pre-lab QC"""
    # Find units with status 'collected' that don't have pre-lab QC
    units = await db.blood_units.find(
        {"status": "collected"},
        {"_id": 0}
    ).to_list(1000)
    
    pending = []
    for unit in units:
        qc = await db.pre_lab_qc.find_one({"unit_id": unit["id"]})
        if not qc:
            # Ensure blood_group is populated for frontend
            if not unit.get("blood_group") and unit.get("preliminary_blood_group"):
                unit["blood_group"] = unit["preliminary_blood_group"]
            if not unit.get("confirmed_blood_group") and unit.get("blood_group"):
                unit["confirmed_blood_group"] = unit["blood_group"]
            pending.append(unit)
    
    return pending

@router.get("/{pre_qc_id}")
async def get_pre_lab_qc(pre_qc_id: str, current_user: dict = Depends(get_current_user)):
    record = await db.pre_lab_qc.find_one(
        {"$or": [{"id": pre_qc_id}, {"pre_qc_id": pre_qc_id}]},
        {"_id": 0}
    )
    if not record:
        raise HTTPException(status_code=404, detail="Pre-Lab QC record not found")
    
    # Get unit details
    unit = await db.blood_units.find_one({"id": record["unit_id"]}, {"_id": 0})
    
    return {
        "qc_record": record,
        "unit": unit
    }

@router.get("/unit/{unit_id}")
async def get_unit_pre_lab_qc(unit_id: str, current_user: dict = Depends(get_current_user)):
    """Get pre-lab QC for a specific unit"""
    unit = await db.blood_units.find_one(
        {"$or": [{"id": unit_id}, {"unit_id": unit_id}]},
        {"_id": 0}
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Blood unit not found")
    
    record = await db.pre_lab_qc.find_one({"unit_id": unit["id"]}, {"_id": 0})
    
    return {
        "unit": unit,
        "pre_lab_qc": record,
        "has_qc": record is not None
    }
