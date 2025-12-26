from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from models import Component, ComponentCreate, UnitStatus, ComponentType
from services import get_current_user, generate_component_id

router = APIRouter(prefix="/components", tags=["Components"])

@router.post("")
async def create_component(component_data: ComponentCreate, current_user: dict = Depends(get_current_user)):
    unit = await db.blood_units.find_one(
        {"$or": [{"id": component_data.parent_unit_id}, {"unit_id": component_data.parent_unit_id}]},
        {"_id": 0}
    )
    if not unit:
        raise HTTPException(status_code=404, detail="Parent blood unit not found")
    
    component = Component(**component_data.model_dump())
    component.component_id = await generate_component_id()
    component.blood_group = unit.get("confirmed_blood_group") or unit.get("blood_group")
    component.processed_by = current_user["id"]
    
    temp_ranges = {
        ComponentType.PRC: (2, 6),
        ComponentType.PLASMA: (-30, -25),
        ComponentType.FFP: (-30, -25),
        ComponentType.PLATELETS: (20, 24),
        ComponentType.CRYOPRECIPITATE: (-30, -25)
    }
    
    if component.component_type in temp_ranges:
        component.storage_temp_min, component.storage_temp_max = temp_ranges[component.component_type]
    
    doc = component.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.components.insert_one(doc)
    
    await db.blood_units.update_one(
        {"$or": [{"id": component_data.parent_unit_id}, {"unit_id": component_data.parent_unit_id}]},
        {"$set": {"status": UnitStatus.PROCESSING.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "success", "component_id": component.component_id, "id": component.id}

@router.get("")
async def get_components(
    status: Optional[str] = None,
    component_type: Optional[str] = None,
    blood_group: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if component_type:
        query["component_type"] = component_type
    if blood_group:
        query["blood_group"] = blood_group
    
    components = await db.components.find(query, {"_id": 0}).to_list(1000)
    return components

@router.get("/{component_id}")
async def get_component(component_id: str, current_user: dict = Depends(get_current_user)):
    component = await db.components.find_one(
        {"$or": [{"id": component_id}, {"component_id": component_id}]},
        {"_id": 0}
    )
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return component

@router.put("/{component_id}")
async def update_component(component_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    result = await db.components.update_one(
        {"$or": [{"id": component_id}, {"component_id": component_id}]},
        {"$set": updates}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Component not found")
    return {"status": "success"}
