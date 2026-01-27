"""
Broadcasts Router - Share urgent needs and surplus alerts across the blood bank network
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import math

import sys
sys.path.append('..')

from database import db
from services import get_current_user
from models.broadcast import (
    Broadcast, BroadcastCreate, BroadcastType, BroadcastStatus,
    BroadcastVisibility, BroadcastResponse, BroadcastResponseCreate
)

router = APIRouter(prefix="/broadcasts", tags=["Broadcasts"])


# ==================== UTILITY FUNCTIONS ====================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return c * 6371


async def expire_old_broadcasts():
    """Mark expired broadcasts as expired."""
    now = datetime.now(timezone.utc).isoformat()
    await db.broadcasts.update_many(
        {"status": "active", "expires_at": {"$lt": now}},
        {"$set": {"status": "expired", "updated_at": now}}
    )


# ==================== PUBLIC ROUTES ====================

@router.get("/active")
async def get_active_broadcasts(
    broadcast_type: Optional[str] = None,
    blood_group: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    max_distance_km: float = 200.0
):
    """
    Get all active broadcasts. Public endpoint for Blood Link page.
    Optionally filter by location for nearby-only broadcasts.
    """
    # First expire old broadcasts
    await expire_old_broadcasts()
    
    query = {"status": "active"}
    
    if broadcast_type:
        query["broadcast_type"] = broadcast_type
    if blood_group:
        query["blood_group"] = blood_group
    
    broadcasts = await db.broadcasts.find(query, {"_id": 0}).to_list(100)
    
    results = []
    for b in broadcasts:
        # Check visibility and location filtering
        if b.get("visibility") == "nearby_only":
            # Skip if no user location provided
            if latitude is None or longitude is None:
                continue
            # Skip if broadcast has no location
            if b.get("latitude") is None or b.get("longitude") is None:
                continue
            # Calculate distance
            distance = haversine_distance(
                latitude, longitude,
                b["latitude"], b["longitude"]
            )
            # Skip if outside broadcast radius or user's max distance
            broadcast_radius = b.get("radius_km", 100)
            if distance > min(broadcast_radius, max_distance_km):
                continue
            b["distance_km"] = round(distance, 2)
        
        results.append(b)
    
    # Sort: critical first, then high, then by created_at desc
    priority_order = {"critical": 0, "high": 1, "normal": 2}
    results.sort(key=lambda x: (priority_order.get(x.get("priority", "normal"), 2), x.get("created_at", "")), reverse=False)
    
    return {
        "count": len(results),
        "broadcasts": results
    }


@router.get("/stats")
async def get_broadcast_stats():
    """Get network-wide broadcast statistics. Public endpoint."""
    await expire_old_broadcasts()
    
    # Count by type and status
    urgent_active = await db.broadcasts.count_documents({
        "broadcast_type": "urgent_need", "status": "active"
    })
    surplus_active = await db.broadcasts.count_documents({
        "broadcast_type": "surplus_alert", "status": "active"
    })
    total_fulfilled = await db.broadcasts.count_documents({"status": "fulfilled"})
    total_responses = await db.broadcast_responses.count_documents({})
    
    return {
        "urgent_needs_active": urgent_active,
        "surplus_alerts_active": surplus_active,
        "total_fulfilled": total_fulfilled,
        "total_responses": total_responses
    }


# ==================== AUTHENTICATED ROUTES ====================

@router.post("")
async def create_broadcast(
    data: BroadcastCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new broadcast. Any authenticated staff can create."""
    if not current_user.get("org_id"):
        raise HTTPException(status_code=400, detail="No organization associated with user")
    
    # Get organization details
    org = await db.organizations.find_one(
        {"id": current_user["org_id"]},
        {"_id": 0}
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=data.expires_in_hours)
    
    broadcast = {
        "id": str(uuid.uuid4()),
        "org_id": current_user["org_id"],
        "org_name": org.get("org_name", "Unknown"),
        "broadcast_type": data.broadcast_type,
        "status": "active",
        "visibility": data.visibility,
        "blood_group": data.blood_group,
        "component_type": data.component_type,
        "units_needed": data.units_needed,
        "units_available": data.units_available,
        "expiry_date": data.expiry_date,
        "latitude": org.get("latitude"),
        "longitude": org.get("longitude"),
        "radius_km": data.radius_km,
        "title": data.title,
        "description": data.description,
        "priority": data.priority,
        "contact_phone": data.contact_phone or org.get("contact_phone"),
        "contact_name": data.contact_name or current_user.get("name"),
        "created_by": current_user["id"],
        "created_by_name": current_user.get("name", "Unknown"),
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "response_count": 0
    }
    
    await db.broadcasts.insert_one(broadcast)
    
    # Remove _id before returning
    broadcast.pop("_id", None)
    
    return {"status": "success", "broadcast": broadcast}


@router.get("/my-broadcasts")
async def get_my_broadcasts(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get broadcasts created by current user's organization."""
    if not current_user.get("org_id"):
        raise HTTPException(status_code=400, detail="No organization associated")
    
    await expire_old_broadcasts()
    
    query = {"org_id": current_user["org_id"]}
    if status:
        query["status"] = status
    
    broadcasts = await db.broadcasts.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"count": len(broadcasts), "broadcasts": broadcasts}


@router.get("/{broadcast_id}")
async def get_broadcast(broadcast_id: str):
    """Get a single broadcast by ID. Public endpoint."""
    broadcast = await db.broadcasts.find_one(
        {"id": broadcast_id},
        {"_id": 0}
    )
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    
    # Get responses
    responses = await db.broadcast_responses.find(
        {"broadcast_id": broadcast_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    broadcast["responses"] = responses
    
    return broadcast


@router.post("/{broadcast_id}/respond")
async def respond_to_broadcast(
    broadcast_id: str,
    data: BroadcastResponseCreate,
    current_user: dict = Depends(get_current_user)
):
    """Respond to a broadcast. Any authenticated staff can respond."""
    if not current_user.get("org_id"):
        raise HTTPException(status_code=400, detail="No organization associated")
    
    broadcast = await db.broadcasts.find_one({"id": broadcast_id})
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    
    if broadcast["status"] != "active":
        raise HTTPException(status_code=400, detail="Broadcast is no longer active")
    
    # Can't respond to own broadcast
    if broadcast["org_id"] == current_user["org_id"]:
        raise HTTPException(status_code=400, detail="Cannot respond to your own broadcast")
    
    # Get responder org
    org = await db.organizations.find_one(
        {"id": current_user["org_id"]},
        {"_id": 0}
    )
    
    now = datetime.now(timezone.utc).isoformat()
    
    response = {
        "id": str(uuid.uuid4()),
        "broadcast_id": broadcast_id,
        "responder_org_id": current_user["org_id"],
        "responder_org_name": org.get("org_name", "Unknown") if org else "Unknown",
        "responder_user_id": current_user["id"],
        "responder_name": current_user.get("name", "Unknown"),
        "message": data.message,
        "units_offered": data.units_offered,
        "contact_phone": data.contact_phone,
        "created_at": now
    }
    
    await db.broadcast_responses.insert_one(response)
    
    # Update response count and status
    await db.broadcasts.update_one(
        {"id": broadcast_id},
        {
            "$inc": {"response_count": 1},
            "$set": {"status": "responded", "updated_at": now}
        }
    )
    
    response.pop("_id", None)
    
    return {"status": "success", "response": response}


@router.put("/{broadcast_id}/close")
async def close_broadcast(
    broadcast_id: str,
    reason: str = "fulfilled",
    current_user: dict = Depends(get_current_user)
):
    """Close a broadcast. Only the creator org can close."""
    broadcast = await db.broadcasts.find_one({"id": broadcast_id})
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    
    # Only creator org or system admin can close
    if broadcast["org_id"] != current_user.get("org_id"):
        if current_user.get("user_type") != "system_admin":
            raise HTTPException(status_code=403, detail="Only the creator can close this broadcast")
    
    now = datetime.now(timezone.utc).isoformat()
    new_status = "fulfilled" if reason == "fulfilled" else "closed"
    
    await db.broadcasts.update_one(
        {"id": broadcast_id},
        {"$set": {
            "status": new_status,
            "closed_at": now,
            "closed_reason": reason,
            "updated_at": now
        }}
    )
    
    return {"status": "success", "message": f"Broadcast {new_status}"}


@router.delete("/{broadcast_id}")
async def delete_broadcast(
    broadcast_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a broadcast. Only creator org or system admin can delete."""
    broadcast = await db.broadcasts.find_one({"id": broadcast_id})
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    
    if broadcast["org_id"] != current_user.get("org_id"):
        if current_user.get("user_type") != "system_admin":
            raise HTTPException(status_code=403, detail="Only the creator can delete this broadcast")
    
    await db.broadcasts.delete_one({"id": broadcast_id})
    await db.broadcast_responses.delete_many({"broadcast_id": broadcast_id})
    
    return {"status": "success", "message": "Broadcast deleted"}


@router.get("/{broadcast_id}/responses")
async def get_broadcast_responses(
    broadcast_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all responses to a broadcast. Creator org sees all details."""
    broadcast = await db.broadcasts.find_one({"id": broadcast_id})
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    
    responses = await db.broadcast_responses.find(
        {"broadcast_id": broadcast_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"count": len(responses), "responses": responses}
