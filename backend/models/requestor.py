"""
Requestor Model - For external blood requestors (hospitals, clinics, etc.)
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid


class RequestorStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class RequestorType(str, Enum):
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    EMERGENCY_SERVICE = "emergency_service"
    RESEARCH_LAB = "research_lab"
    OTHER = "other"


class RequestorRegistration(BaseModel):
    """Model for requestor registration submission"""
    organization_name: str = Field(..., min_length=2, max_length=200)
    requestor_type: RequestorType
    contact_person: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    address: str = Field(..., min_length=10, max_length=500)
    city: str
    state: str
    pincode: str
    latitude: Optional[float] = None  # Map location
    longitude: Optional[float] = None  # Map location
    license_number: Optional[str] = None
    registration_number: Optional[str] = None
    notes: Optional[str] = None


class Requestor(BaseModel):
    """Full requestor model stored in database"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_name: str
    requestor_type: RequestorType
    contact_person: str
    email: EmailStr
    phone: str
    address: str
    city: str
    state: str
    pincode: str
    latitude: Optional[float] = None  # Map location
    longitude: Optional[float] = None  # Map location
    license_number: Optional[str] = None
    registration_number: Optional[str] = None
    notes: Optional[str] = None
    
    # Status and approval
    status: RequestorStatus = RequestorStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Associated user account (created after approval)
    user_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Which blood bank org they're associated with (set during approval)
    associated_org_id: Optional[str] = None


class RequestorUpdate(BaseModel):
    """Model for updating requestor details"""
    organization_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    license_number: Optional[str] = None
    registration_number: Optional[str] = None
    notes: Optional[str] = None


class RequestorApproval(BaseModel):
    """Model for approving/rejecting a requestor"""
    action: str = Field(..., pattern="^(approve|reject)$")
    associated_org_id: Optional[str] = None  # Required for approval
    rejection_reason: Optional[str] = None  # Required for rejection
