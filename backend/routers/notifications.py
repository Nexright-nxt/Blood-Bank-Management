from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timezone, timedelta

import sys
sys.path.append('..')

from database import db
from models import Notification, NotificationCreate, AlertType
from services import get_current_user
import uuid

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for current user"""
    query = {
        "$or": [
            {"user_id": current_user["id"]},
            {"user_id": None, "role": current_user["role"]},
            {"user_id": None, "role": None}  # Broadcast to all
        ]
    }
    
    if unread_only:
        query["is_read"] = False
    
    # Exclude expired notifications
    now = datetime.now(timezone.utc).isoformat()
    query["$or"] = [
        *query.get("$or", []),
    ]
    
    notifications = await db.notifications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    return notifications

@router.get("/count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications"""
    query = {
        "is_read": False,
        "$or": [
            {"user_id": current_user["id"]},
            {"user_id": None, "role": current_user["role"]},
            {"user_id": None, "role": None}
        ]
    }
    
    count = await db.notifications.count_documents(query)
    
    # Count by type
    emergency = await db.notifications.count_documents({**query, "alert_type": "emergency"})
    urgent = await db.notifications.count_documents({**query, "alert_type": "urgent"})
    warning = await db.notifications.count_documents({**query, "alert_type": "warning"})
    
    return {
        "total": count,
        "emergency": emergency,
        "urgent": urgent,
        "warning": warning
    }

@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"is_read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}

@router.put("/read-all")
async def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    query = {
        "is_read": False,
        "$or": [
            {"user_id": current_user["id"]},
            {"user_id": None, "role": current_user["role"]},
            {"user_id": None, "role": None}
        ]
    }
    
    result = await db.notifications.update_many(query, {"$set": {"is_read": True}})
    return {"status": "success", "marked_read": result.modified_count}

@router.post("")
async def create_notification(data: NotificationCreate, current_user: dict = Depends(get_current_user)):
    """Create a new notification (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    notification = Notification(**data.model_dump())
    
    doc = notification.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('expires_at'):
        doc['expires_at'] = doc['expires_at'].isoformat()
    
    await db.notifications.insert_one(doc)
    return {"status": "success", "notification_id": notification.id}

@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a notification"""
    result = await db.notifications.delete_one({"id": notification_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}

# Utility functions for creating system notifications
async def create_system_notification(
    alert_type: str,
    title: str,
    message: str,
    link_to: Optional[str] = None,
    user_id: Optional[str] = None,
    role: Optional[str] = None
):
    """Create a system-generated notification"""
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "role": role,
        "alert_type": alert_type,
        "title": title,
        "message": message,
        "link_to": link_to,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    return notification

# Background tasks for generating alerts
@router.post("/generate-alerts")
async def generate_system_alerts(current_user: dict = Depends(get_current_user)):
    """Generate system alerts for stock, expiry, etc."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    alerts_created = 0
    now = datetime.now(timezone.utc)
    today = now.isoformat().split("T")[0]
    
    # Check for low stock (< 5 units per blood group)
    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    for bg in blood_groups:
        count = await db.blood_units.count_documents({
            "status": "ready_to_use",
            "$or": [{"blood_group": bg}, {"confirmed_blood_group": bg}]
        })
        if count < 5:
            await create_system_notification(
                alert_type="warning" if count > 0 else "urgent",
                title=f"Low Stock Alert: {bg}",
                message=f"Only {count} units of {bg} blood available",
                link_to="/inventory",
                role="inventory"
            )
            alerts_created += 1
    
    # Check for expiring units (within 3 days)
    expiry_date = (now + timedelta(days=3)).isoformat().split("T")[0]
    expiring = await db.blood_units.count_documents({
        "status": "ready_to_use",
        "expiry_date": {"$lte": expiry_date, "$gte": today}
    })
    if expiring > 0:
        await create_system_notification(
            alert_type="warning",
            title="Expiring Units Alert",
            message=f"{expiring} units expiring within 3 days",
            link_to="/alerts",
            role="inventory"
        )
        alerts_created += 1
    
    # Check for pending requests
    urgent_requests = await db.blood_requests.count_documents({
        "status": "pending",
        "urgency": {"$in": ["urgent", "emergency"]}
    })
    if urgent_requests > 0:
        await create_system_notification(
            alert_type="emergency" if urgent_requests > 0 else "urgent",
            title="Urgent Blood Requests",
            message=f"{urgent_requests} urgent/emergency requests pending",
            link_to="/requests",
            role="inventory"
        )
        alerts_created += 1
    
    # Check for pending donor registrations
    pending_donors = await db.donor_requests.count_documents({"status": "pending"})
    if pending_donors > 5:
        await create_system_notification(
            alert_type="info",
            title="Pending Donor Registrations",
            message=f"{pending_donors} donor registrations awaiting approval",
            link_to="/donor-requests",
            role="registration"
        )
        alerts_created += 1
    
    return {"status": "success", "alerts_created": alerts_created}
