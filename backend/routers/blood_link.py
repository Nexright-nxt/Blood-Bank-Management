"""
Blood Link Router - Nearby blood bank availability search
Allows users to find nearby blood banks with available stock based on geolocation.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import math

import sys
sys.path.append('..')

from database import db
from services import get_current_user
from models import BloodGroup, ComponentType

router = APIRouter(prefix="/blood-link", tags=["Blood Link"])


# ==================== MODELS ====================

class NearbySearchRequest(BaseModel):
    latitude: float
    longitude: float
    blood_group: Optional[str] = None
    component_type: Optional[str] = None
    max_distance_km: float = 50.0  # Default 50km radius
    min_units: int = 1


class BloodBankAvailability(BaseModel):
    org_id: str
    org_name: str
    address: str
    city: str
    state: str
    pincode: Optional[str] = None
    latitude: float
    longitude: float
    distance_km: float
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    operating_hours: Optional[str] = None
    is_24x7: bool = False
    availability: dict  # {blood_group: {component_type: count}}
    total_units: int


# ==================== UTILITY FUNCTIONS ====================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers
    r = 6371
    
    return c * r


async def get_org_blood_availability(org_id: str, blood_group: Optional[str] = None) -> dict:
    """
    Get blood availability for an organization.
    Returns dict of {blood_group: {component_type: count}}
    """
    availability = {}
    total = 0
    
    # Query for whole blood units
    unit_query = {"org_id": org_id, "status": "ready_to_use"}
    if blood_group:
        unit_query["$or"] = [
            {"blood_group": blood_group},
            {"confirmed_blood_group": blood_group}
        ]
    
    units_pipeline = [
        {"$match": unit_query},
        {"$group": {
            "_id": {"$ifNull": ["$confirmed_blood_group", "$blood_group"]},
            "count": {"$sum": 1}
        }}
    ]
    
    units_result = await db.blood_units.aggregate(units_pipeline).to_list(20)
    for item in units_result:
        bg = item["_id"]
        if bg:
            if bg not in availability:
                availability[bg] = {}
            availability[bg]["whole_blood"] = item["count"]
            total += item["count"]
    
    # Query for components
    comp_query = {"org_id": org_id, "status": "ready_to_use"}
    if blood_group:
        comp_query["blood_group"] = blood_group
    
    comp_pipeline = [
        {"$match": comp_query},
        {"$group": {
            "_id": {"blood_group": "$blood_group", "component_type": "$component_type"},
            "count": {"$sum": 1}
        }}
    ]
    
    comp_result = await db.components.aggregate(comp_pipeline).to_list(100)
    for item in comp_result:
        bg = item["_id"]["blood_group"]
        ct = item["_id"]["component_type"]
        if bg and ct:
            if bg not in availability:
                availability[bg] = {}
            availability[bg][ct] = item["count"]
            total += item["count"]
    
    return {"availability": availability, "total": total}


# ==================== PUBLIC ROUTES (No Auth Required) ====================

@router.post("/search")
async def search_nearby_blood_banks(request: NearbySearchRequest):
    """
    Search for nearby blood banks with available blood stock.
    This is a public endpoint for emergency blood searches.
    """
    # Get all organizations with geolocation that accept external requests
    orgs = await db.organizations.find({
        "latitude": {"$exists": True, "$ne": None},
        "longitude": {"$exists": True, "$ne": None},
        "is_active": True,
        "accepts_external_requests": {"$ne": False}
    }, {"_id": 0}).to_list(1000)
    
    results = []
    
    for org in orgs:
        # Calculate distance
        distance = haversine_distance(
            request.latitude, request.longitude,
            org["latitude"], org["longitude"]
        )
        
        # Skip if too far
        if distance > request.max_distance_km:
            continue
        
        # Get blood availability
        avail_data = await get_org_blood_availability(
            org["id"], 
            request.blood_group
        )
        
        # Skip if no stock or below minimum
        if avail_data["total"] < request.min_units:
            continue
        
        # Filter by component type if specified
        if request.component_type:
            filtered_avail = {}
            filtered_total = 0
            for bg, components in avail_data["availability"].items():
                if request.component_type in components:
                    if bg not in filtered_avail:
                        filtered_avail[bg] = {}
                    filtered_avail[bg][request.component_type] = components[request.component_type]
                    filtered_total += components[request.component_type]
            
            if filtered_total < request.min_units:
                continue
            avail_data = {"availability": filtered_avail, "total": filtered_total}
        
        results.append({
            "org_id": org["id"],
            "org_name": org["org_name"],
            "address": org.get("address", ""),
            "city": org.get("city", ""),
            "state": org.get("state", ""),
            "pincode": org.get("pincode"),
            "latitude": org["latitude"],
            "longitude": org["longitude"],
            "distance_km": round(distance, 2),
            "contact_phone": org.get("contact_phone"),
            "contact_email": org.get("contact_email"),
            "operating_hours": org.get("operating_hours"),
            "is_24x7": org.get("is_24x7", False),
            "availability": avail_data["availability"],
            "total_units": avail_data["total"]
        })
    
    # Sort by distance
    results.sort(key=lambda x: x["distance_km"])
    
    return {
        "search_location": {
            "latitude": request.latitude,
            "longitude": request.longitude
        },
        "filters": {
            "blood_group": request.blood_group,
            "component_type": request.component_type,
            "max_distance_km": request.max_distance_km,
            "min_units": request.min_units
        },
        "results_count": len(results),
        "blood_banks": results
    }


@router.get("/availability/{org_id}")
async def get_blood_bank_availability(org_id: str):
    """
    Get detailed blood availability for a specific blood bank.
    Public endpoint for checking stock before visiting.
    """
    org = await db.organizations.find_one(
        {"id": org_id, "is_active": True},
        {"_id": 0}
    )
    if not org:
        raise HTTPException(status_code=404, detail="Blood bank not found")
    
    avail_data = await get_org_blood_availability(org_id)
    
    # Get expiring soon count (within 7 days)
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat().split("T")[0]
    expiring_units = await db.blood_units.count_documents({
        "org_id": org_id,
        "status": "ready_to_use",
        "expiry_date": {"$lte": expiry_date}
    })
    expiring_components = await db.components.count_documents({
        "org_id": org_id,
        "status": "ready_to_use",
        "expiry_date": {"$lte": expiry_date}
    })
    
    return {
        "org_id": org["id"],
        "org_name": org["org_name"],
        "address": org.get("address"),
        "city": org.get("city"),
        "state": org.get("state"),
        "pincode": org.get("pincode"),
        "contact_phone": org.get("contact_phone"),
        "contact_email": org.get("contact_email"),
        "operating_hours": org.get("operating_hours"),
        "is_24x7": org.get("is_24x7", False),
        "availability": avail_data["availability"],
        "total_units": avail_data["total"],
        "expiring_within_7_days": expiring_units + expiring_components,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


@router.get("/blood-groups")
async def get_available_blood_groups():
    """Get list of blood groups with network-wide availability summary."""
    summary = {}
    
    for bg in BloodGroup:
        # Count whole blood units
        units = await db.blood_units.count_documents({
            "status": "ready_to_use",
            "$or": [{"blood_group": bg.value}, {"confirmed_blood_group": bg.value}]
        })
        
        # Count components
        components = await db.components.count_documents({
            "status": "ready_to_use",
            "blood_group": bg.value
        })
        
        # Count blood banks with this blood group
        orgs_with_stock = await db.blood_units.distinct("org_id", {
            "status": "ready_to_use",
            "$or": [{"blood_group": bg.value}, {"confirmed_blood_group": bg.value}]
        })
        
        summary[bg.value] = {
            "whole_blood": units,
            "components": components,
            "total": units + components,
            "blood_banks_with_stock": len(orgs_with_stock)
        }
    
    return summary


# ==================== AUTHENTICATED ROUTES ====================

@router.get("/my-org/settings")
async def get_blood_link_settings(current_user: dict = Depends(get_current_user)):
    """Get Blood Link settings for current user's organization."""
    if not current_user.get("org_id"):
        raise HTTPException(status_code=400, detail="No organization associated")
    
    org = await db.organizations.find_one(
        {"id": current_user["org_id"]},
        {"_id": 0}
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {
        "org_id": org["id"],
        "org_name": org["org_name"],
        "latitude": org.get("latitude"),
        "longitude": org.get("longitude"),
        "operating_hours": org.get("operating_hours"),
        "is_24x7": org.get("is_24x7", False),
        "accepts_external_requests": org.get("accepts_external_requests", True),
        "has_geolocation": org.get("latitude") is not None and org.get("longitude") is not None
    }


@router.put("/my-org/settings")
async def update_blood_link_settings(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    operating_hours: Optional[str] = None,
    is_24x7: Optional[bool] = None,
    accepts_external_requests: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update Blood Link settings for current user's organization."""
    if not current_user.get("org_id"):
        raise HTTPException(status_code=400, detail="No organization associated")
    
    # Only admins can update settings
    if current_user.get("user_type") not in ["system_admin", "super_admin", "tenant_admin"]:
        raise HTTPException(status_code=403, detail="Only admins can update Blood Link settings")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if latitude is not None:
        update_data["latitude"] = latitude
    if longitude is not None:
        update_data["longitude"] = longitude
    if operating_hours is not None:
        update_data["operating_hours"] = operating_hours
    if is_24x7 is not None:
        update_data["is_24x7"] = is_24x7
    if accepts_external_requests is not None:
        update_data["accepts_external_requests"] = accepts_external_requests
    
    result = await db.organizations.update_one(
        {"id": current_user["org_id"]},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {"status": "success", "message": "Blood Link settings updated"}


@router.get("/emergency-contacts")
async def get_emergency_blood_contacts():
    """
    Get list of 24x7 blood banks for emergencies.
    Public endpoint.
    """
    orgs = await db.organizations.find({
        "is_active": True,
        "is_24x7": True,
        "accepts_external_requests": {"$ne": False}
    }, {"_id": 0}).to_list(100)
    
    contacts = []
    for org in orgs:
        avail = await get_org_blood_availability(org["id"])
        contacts.append({
            "org_name": org["org_name"],
            "address": org.get("address"),
            "city": org.get("city"),
            "state": org.get("state"),
            "contact_phone": org.get("contact_phone"),
            "contact_email": org.get("contact_email"),
            "total_units_available": avail["total"]
        })
    
    return contacts
