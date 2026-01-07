from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from models import ChainOfCustody, ChainOfCustodyCreate
from services import get_current_user
from middleware import ReadAccess, WriteAccess, OrgAccessHelper

router = APIRouter(prefix="/blood-units", tags=["Blood Units"])

@router.get("")
async def get_blood_units(
    status: Optional[str] = None,
    blood_group: Optional[str] = None,
    location: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    query = {}
    if status:
        query["status"] = status
    if blood_group:
        query["$or"] = [
            {"blood_group": blood_group},
            {"confirmed_blood_group": blood_group}
        ]
    if location:
        query["current_location"] = location
    
    units = await db.blood_units.find(access.filter(query), {"_id": 0}).to_list(1000)
    return units

@router.get("/{unit_id}")
async def get_blood_unit(
    unit_id: str, 
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    unit = await db.blood_units.find_one(
        access.filter({"$or": [{"id": unit_id}, {"unit_id": unit_id}]}),
        {"_id": 0}
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Blood unit not found")
    return unit

@router.put("/{unit_id}")
async def update_blood_unit(
    unit_id: str, 
    updates: dict, 
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(WriteAccess)
):
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.blood_units.update_one(
        access.filter({"$or": [{"id": unit_id}, {"unit_id": unit_id}]}),
        {"$set": updates}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Blood unit not found")
    return {"status": "success"}

@router.get("/{unit_id}/traceability")
async def get_unit_traceability(
    unit_id: str, 
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    unit = await db.blood_units.find_one(
        access.filter({"$or": [{"id": unit_id}, {"unit_id": unit_id}]}),
        {"_id": 0}
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Blood unit not found")
    
    custody = await db.chain_custody.find({"unit_id": unit["id"]}, {"_id": 0}).to_list(100)
    lab_tests = await db.lab_tests.find({"unit_id": unit["id"]}, {"_id": 0}).to_list(10)
    components = await db.components.find({"parent_unit_id": unit["id"]}, {"_id": 0}).to_list(10)
    
    return {
        "unit": unit,
        "chain_of_custody": custody,
        "lab_tests": lab_tests,
        "components": components
    }

# Chain of Custody Router
custody_router = APIRouter(prefix="/chain-custody", tags=["Chain of Custody"])

@custody_router.post("")
async def create_custody_record(
    custody_data: ChainOfCustodyCreate, 
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(WriteAccess)
):
    custody = ChainOfCustody(**custody_data.model_dump())
    custody.org_id = access.get_default_org_id()
    
    doc = custody.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    await db.chain_custody.insert_one(doc)
    
    await db.blood_units.update_one(
        {"$or": [{"id": custody_data.unit_id}, {"unit_id": custody_data.unit_id}]},
        {"$set": {"current_location": custody_data.to_location, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "success", "custody_id": custody.id}

@custody_router.get("")
async def get_custody_records(
    unit_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    query = {}
    if unit_id:
        query["unit_id"] = unit_id
    
    records = await db.chain_custody.find(access.filter(query), {"_id": 0}).to_list(1000)
    return records

@custody_router.put("/{custody_id}/confirm")
async def confirm_custody(
    custody_id: str, 
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(WriteAccess)
):
    result = await db.chain_custody.update_one(
        access.filter({"id": custody_id}),
        {"$set": {"confirmed": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Custody record not found")
    return {"status": "success"}
