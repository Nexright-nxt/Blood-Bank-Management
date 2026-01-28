"""
Requestor Router - Public registration and management for external blood requestors
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timezone
import uuid

import sys
sys.path.append('..')

from database import db
from models.requestor import (
    Requestor, RequestorRegistration, RequestorUpdate, RequestorApproval,
    RequestorStatus, RequestorType
)
from services import get_current_user, hash_password, verify_password, create_token
from middleware import ReadAccess, WriteAccess, OrgAccessHelper
from middleware.permissions import require_permission

router = APIRouter(prefix="/requestors", tags=["Requestors"])


# ==================== PUBLIC ROUTES (No Auth Required) ====================

@router.post("/register")
async def register_requestor(data: RequestorRegistration):
    """
    Public endpoint for requestor registration.
    Creates a pending requestor application that needs admin approval.
    """
    # Check if email already exists
    existing_user = await db.users.find_one({"email": data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered as a user")
    
    existing_requestor = await db.requestors.find_one({"email": data.email})
    if existing_requestor:
        if existing_requestor.get("status") == "pending":
            raise HTTPException(status_code=400, detail="Registration already pending approval")
        elif existing_requestor.get("status") == "approved":
            raise HTTPException(status_code=400, detail="Email already registered. Please login.")
        elif existing_requestor.get("status") == "rejected":
            # Allow re-registration if previously rejected
            await db.requestors.delete_one({"email": data.email})
    
    # Create requestor record
    requestor = Requestor(
        organization_name=data.organization_name,
        requestor_type=data.requestor_type,
        contact_person=data.contact_person,
        email=data.email,
        phone=data.phone,
        address=data.address,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        latitude=data.latitude,
        longitude=data.longitude,
        license_number=data.license_number,
        registration_number=data.registration_number,
        notes=data.notes,
        status=RequestorStatus.PENDING
    )
    
    # Store hashed password temporarily (will be used when creating user account)
    doc = requestor.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['password_hash'] = hash_password(data.password)
    
    await db.requestors.insert_one(doc)
    
    return {
        "status": "success",
        "message": "Registration submitted successfully. Please wait for admin approval.",
        "requestor_id": requestor.id
    }


@router.get("/check-status/{email}")
async def check_registration_status(email: str):
    """
    Public endpoint to check registration status by email.
    """
    requestor = await db.requestors.find_one({"email": email}, {"_id": 0, "password_hash": 0})
    if not requestor:
        raise HTTPException(status_code=404, detail="No registration found for this email")
    
    return {
        "status": requestor.get("status"),
        "organization_name": requestor.get("organization_name"),
        "submitted_at": requestor.get("created_at"),
        "rejection_reason": requestor.get("rejection_reason") if requestor.get("status") == "rejected" else None
    }


# ==================== ADMIN ROUTES (Auth Required) ====================

@router.get("")
async def get_requestors(
    status: Optional[str] = None,
    requestor_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_permission("users", "view")),
    access: OrgAccessHelper = Depends(ReadAccess)
):
    """Get all requestor registrations (admin only)"""
    query = {}
    
    if status:
        query["status"] = status
    if requestor_type:
        query["requestor_type"] = requestor_type
    if search:
        query["$or"] = [
            {"organization_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"contact_person": {"$regex": search, "$options": "i"}}
        ]
    
    requestors = await db.requestors.find(query, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(1000)
    return requestors


@router.get("/pending")
async def get_pending_requestors(
    current_user: dict = Depends(require_permission("users", "view"))
):
    """Get all pending requestor registrations for approval"""
    requestors = await db.requestors.find(
        {"status": "pending"}, 
        {"_id": 0, "password_hash": 0}
    ).sort("created_at", 1).to_list(100)
    return requestors


@router.get("/stats")
async def get_requestor_stats(
    current_user: dict = Depends(require_permission("users", "view"))
):
    """Get requestor registration statistics"""
    total = await db.requestors.count_documents({})
    pending = await db.requestors.count_documents({"status": "pending"})
    approved = await db.requestors.count_documents({"status": "approved"})
    rejected = await db.requestors.count_documents({"status": "rejected"})
    suspended = await db.requestors.count_documents({"status": "suspended"})
    
    # By type
    by_type = {}
    for rtype in RequestorType:
        by_type[rtype.value] = await db.requestors.count_documents({"requestor_type": rtype.value})
    
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "suspended": suspended,
        "by_type": by_type
    }


@router.get("/{requestor_id}")
async def get_requestor(
    requestor_id: str,
    current_user: dict = Depends(require_permission("users", "view"))
):
    """Get a specific requestor's details"""
    requestor = await db.requestors.find_one(
        {"id": requestor_id}, 
        {"_id": 0, "password_hash": 0}
    )
    if not requestor:
        raise HTTPException(status_code=404, detail="Requestor not found")
    return requestor


@router.put("/{requestor_id}/approve")
async def approve_or_reject_requestor(
    requestor_id: str,
    data: RequestorApproval,
    current_user: dict = Depends(require_permission("users", "create"))
):
    """Approve or reject a requestor registration"""
    requestor = await db.requestors.find_one({"id": requestor_id})
    if not requestor:
        raise HTTPException(status_code=404, detail="Requestor not found")
    
    if requestor.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Requestor is already {requestor.get('status')}")
    
    if data.action == "approve":
        if not data.associated_org_id:
            raise HTTPException(status_code=400, detail="Associated organization is required for approval")
        
        # Verify org exists
        org = await db.organizations.find_one({"id": data.associated_org_id})
        if not org:
            raise HTTPException(status_code=400, detail="Associated organization not found")
        
        # Create user account for the requestor
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": requestor["email"],
            "password_hash": requestor.get("password_hash"),
            "full_name": requestor["contact_person"],
            "phone": requestor["phone"],
            "role": "requestor",
            "user_type": "requestor",
            "org_id": data.associated_org_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "requestor_id": requestor_id,
            "requestor_org_name": requestor["organization_name"]
        }
        
        await db.users.insert_one(user)
        
        # Update requestor record
        await db.requestors.update_one(
            {"id": requestor_id},
            {
                "$set": {
                    "status": RequestorStatus.APPROVED.value,
                    "approved_by": current_user["id"],
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                    "user_id": user_id,
                    "associated_org_id": data.associated_org_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$unset": {"password_hash": ""}
            }
        )
        
        return {
            "status": "success",
            "message": f"Requestor approved. User account created for {requestor['email']}",
            "user_id": user_id
        }
    
    else:  # reject
        if not data.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        
        await db.requestors.update_one(
            {"id": requestor_id},
            {
                "$set": {
                    "status": RequestorStatus.REJECTED.value,
                    "rejection_reason": data.rejection_reason,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$unset": {"password_hash": ""}
            }
        )
        
        return {
            "status": "success",
            "message": "Requestor registration rejected"
        }


@router.put("/{requestor_id}/suspend")
async def suspend_requestor(
    requestor_id: str,
    reason: str,
    current_user: dict = Depends(require_permission("users", "edit"))
):
    """Suspend an approved requestor"""
    requestor = await db.requestors.find_one({"id": requestor_id})
    if not requestor:
        raise HTTPException(status_code=404, detail="Requestor not found")
    
    if requestor.get("status") != "approved":
        raise HTTPException(status_code=400, detail="Only approved requestors can be suspended")
    
    # Deactivate user account
    if requestor.get("user_id"):
        await db.users.update_one(
            {"id": requestor["user_id"]},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    await db.requestors.update_one(
        {"id": requestor_id},
        {
            "$set": {
                "status": RequestorStatus.SUSPENDED.value,
                "suspension_reason": reason,
                "suspended_by": current_user["id"],
                "suspended_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"status": "success", "message": "Requestor suspended"}


@router.put("/{requestor_id}/reactivate")
async def reactivate_requestor(
    requestor_id: str,
    current_user: dict = Depends(require_permission("users", "edit"))
):
    """Reactivate a suspended requestor"""
    requestor = await db.requestors.find_one({"id": requestor_id})
    if not requestor:
        raise HTTPException(status_code=404, detail="Requestor not found")
    
    if requestor.get("status") != "suspended":
        raise HTTPException(status_code=400, detail="Only suspended requestors can be reactivated")
    
    # Reactivate user account
    if requestor.get("user_id"):
        await db.users.update_one(
            {"id": requestor["user_id"]},
            {"$set": {"is_active": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    await db.requestors.update_one(
        {"id": requestor_id},
        {
            "$set": {
                "status": RequestorStatus.APPROVED.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$unset": {
                "suspension_reason": "",
                "suspended_by": "",
                "suspended_at": ""
            }
        }
    )
    
    return {"status": "success", "message": "Requestor reactivated"}


# ==================== REQUESTOR SELF-SERVICE ROUTES ====================

@router.get("/me/profile")
async def get_my_requestor_profile(current_user: dict = Depends(get_current_user)):
    """Get current requestor's profile"""
    if current_user.get("user_type") != "requestor":
        raise HTTPException(status_code=403, detail="Only requestors can access this endpoint")
    
    requestor_id = current_user.get("requestor_id")
    if not requestor_id:
        raise HTTPException(status_code=404, detail="Requestor profile not found")
    
    requestor = await db.requestors.find_one(
        {"id": requestor_id}, 
        {"_id": 0, "password_hash": 0}
    )
    if not requestor:
        raise HTTPException(status_code=404, detail="Requestor not found")
    
    return requestor


@router.put("/me/profile")
async def update_my_requestor_profile(
    updates: RequestorUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current requestor's profile"""
    if current_user.get("user_type") != "requestor":
        raise HTTPException(status_code=403, detail="Only requestors can access this endpoint")
    
    requestor_id = current_user.get("requestor_id")
    if not requestor_id:
        raise HTTPException(status_code=404, detail="Requestor profile not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.requestors.update_one({"id": requestor_id}, {"$set": update_data})
    
    # Also update user record if contact person changed
    if updates.contact_person:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"full_name": updates.contact_person, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"status": "success", "message": "Profile updated"}
