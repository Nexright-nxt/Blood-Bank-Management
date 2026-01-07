from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timezone

import sys
sys.path.append('..')

from database import db
from models import StorageLocation, StorageLocationCreate, StorageType
from services import get_current_user
from middleware import ReadAccess, WriteAccess, OrgAccessHelper

router = APIRouter(prefix="/storage", tags=["Storage Management"])

async def generate_storage_id() -> str:
    count = await db.storage_locations.count_documents({})
    return f"STR-{str(count + 1).zfill(4)}"

@router.post("")
async def create_storage_location(
    data: StorageLocationCreate, 
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(WriteAccess)
):
    if current_user["role"] not in ["admin", "inventory"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Check for duplicate location code within org
    existing = await db.storage_locations.find_one(
        access.filter({"location_code": data.location_code})
    )
    if existing:
        raise HTTPException(status_code=400, detail="Location code already exists")
    
    storage = StorageLocation(**data.model_dump())
    storage.created_by = current_user["id"]
    storage.org_id = access.get_default_org_id()
    
    doc = storage.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.storage_locations.insert_one(doc)
    return {"status": "success", "storage_id": storage.id, "location_code": storage.location_code}

@router.get("")
async def get_storage_locations(
    storage_type: Optional[str] = None,
    facility: Optional[str] = None,
    is_active: Optional[bool] = True,
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    query = {}
    if storage_type:
        query["storage_type"] = storage_type
    if facility:
        query["facility"] = facility
    if is_active is not None:
        query["is_active"] = is_active
    
    locations = await db.storage_locations.find(access.filter(query), {"_id": 0}).to_list(1000)
    return locations

@router.get("/summary")
async def get_storage_summary(
    current_user: dict = Depends(get_current_user),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    locations = await db.storage_locations.find(access.filter({"is_active": True}), {"_id": 0}).to_list(1000)
    
    summary = {
        "total_locations": len(locations),
        "by_type": {},
        "capacity_alerts": [],
        "total_capacity": 0,
        "total_occupied": 0
    }
    
    for loc in locations:
        storage_type = loc.get("storage_type", "unknown")
        if storage_type not in summary["by_type"]:
            summary["by_type"][storage_type] = {"count": 0, "capacity": 0, "occupied": 0}
        
        summary["by_type"][storage_type]["count"] += 1
        summary["by_type"][storage_type]["capacity"] += loc.get("capacity", 0)
        summary["by_type"][storage_type]["occupied"] += loc.get("current_occupancy", 0)
        
        summary["total_capacity"] += loc.get("capacity", 0)
        summary["total_occupied"] += loc.get("current_occupancy", 0)
        
        # Check for capacity alerts (>80%)
        capacity = loc.get("capacity", 1)
        occupancy = loc.get("current_occupancy", 0)
        if capacity > 0 and (occupancy / capacity) > 0.8:
            summary["capacity_alerts"].append({
                "location_code": loc.get("location_code"),
                "storage_name": loc.get("storage_name"),
                "occupancy_percent": round((occupancy / capacity) * 100, 1)
            })
    
    return summary

@router.get("/{storage_id}")
async def get_storage_location(storage_id: str, current_user: dict = Depends(get_current_user)):
    location = await db.storage_locations.find_one(
        {"$or": [{"id": storage_id}, {"location_code": storage_id}]},
        {"_id": 0}
    )
    if not location:
        raise HTTPException(status_code=404, detail="Storage location not found")
    
    # Get items in this storage
    units = await db.blood_units.find({"storage_location_id": location["id"]}, {"_id": 0}).to_list(100)
    components = await db.components.find({"storage_location_id": location["id"]}, {"_id": 0}).to_list(100)
    
    return {
        "location": location,
        "units": units,
        "components": components,
        "item_count": len(units) + len(components)
    }

@router.put("/{storage_id}")
async def update_storage_location(storage_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "inventory"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    updates["updated_by"] = current_user["id"]
    
    result = await db.storage_locations.update_one(
        {"$or": [{"id": storage_id}, {"location_code": storage_id}]},
        {"$set": updates}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Storage location not found")
    return {"status": "success"}

@router.post("/{storage_id}/assign")
async def assign_to_storage(
    storage_id: str,
    item_id: str,
    item_type: str,  # "unit" or "component"
    current_user: dict = Depends(get_current_user)
):
    """Assign a blood unit or component to a storage location"""
    location = await db.storage_locations.find_one(
        {"$or": [{"id": storage_id}, {"location_code": storage_id}]},
        {"_id": 0}
    )
    if not location:
        raise HTTPException(status_code=404, detail="Storage location not found")
    
    # Check capacity
    if location.get("current_occupancy", 0) >= location.get("capacity", 0):
        raise HTTPException(status_code=400, detail="Storage location is at full capacity")
    
    collection = db.blood_units if item_type == "unit" else db.components
    id_field = "unit_id" if item_type == "unit" else "component_id"
    
    item = await collection.find_one(
        {"$or": [{"id": item_id}, {id_field: item_id}]},
        {"_id": 0}
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"{item_type.capitalize()} not found")
    
    old_storage_id = item.get("storage_location_id")
    
    # Update item with new storage location
    await collection.update_one(
        {"$or": [{"id": item_id}, {id_field: item_id}]},
        {"$set": {
            "storage_location_id": location["id"],
            "storage_location": location["location_code"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update occupancy counts
    await db.storage_locations.update_one(
        {"id": location["id"]},
        {"$inc": {"current_occupancy": 1}}
    )
    
    if old_storage_id:
        await db.storage_locations.update_one(
            {"id": old_storage_id},
            {"$inc": {"current_occupancy": -1}}
        )
    
    # Log chain of custody
    custody_record = {
        "id": str(__import__('uuid').uuid4()),
        "unit_id": item["id"],
        "stage": "Storage Assignment",
        "from_location": item.get("storage_location", "Unknown"),
        "to_location": location["location_code"],
        "giver_id": current_user["id"],
        "receiver_id": current_user["id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confirmed": True,
        "notes": f"Assigned to {location['storage_name']}"
    }
    await db.chain_custody.insert_one(custody_record)
    
    return {"status": "success", "message": f"{item_type.capitalize()} assigned to {location['storage_name']}"}

@router.post("/{storage_id}/transfer")
async def transfer_storage(
    storage_id: str,
    item_ids: List[str],
    item_type: str,
    target_storage_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Transfer multiple items to a different storage location"""
    target = await db.storage_locations.find_one(
        {"$or": [{"id": target_storage_id}, {"location_code": target_storage_id}]},
        {"_id": 0}
    )
    if not target:
        raise HTTPException(status_code=404, detail="Target storage location not found")
    
    # Check capacity
    available = target.get("capacity", 0) - target.get("current_occupancy", 0)
    if len(item_ids) > available:
        raise HTTPException(status_code=400, detail=f"Insufficient capacity. Only {available} slots available.")
    
    transferred = 0
    for item_id in item_ids:
        try:
            await assign_to_storage(target_storage_id, item_id, item_type, current_user)
            transferred += 1
        except:
            continue
    
    return {"status": "success", "transferred": transferred, "total": len(item_ids)}
