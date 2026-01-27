"""
Broadcast Model - For sharing urgent needs and surplus alerts across the blood bank network
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class BroadcastType(str, Enum):
    URGENT_NEED = "urgent_need"
    SURPLUS_ALERT = "surplus_alert"


class BroadcastStatus(str, Enum):
    ACTIVE = "active"
    RESPONDED = "responded"
    FULFILLED = "fulfilled"
    EXPIRED = "expired"
    CLOSED = "closed"


class BroadcastVisibility(str, Enum):
    NETWORK_WIDE = "network_wide"
    NEARBY_ONLY = "nearby_only"


class BroadcastResponse(BaseModel):
    """Response to a broadcast from another organization"""
    id: str
    broadcast_id: str
    responder_org_id: str
    responder_org_name: str
    responder_user_id: str
    responder_name: str
    message: str
    units_offered: Optional[int] = None
    contact_phone: Optional[str] = None
    created_at: str


class Broadcast(BaseModel):
    """Main broadcast model"""
    id: str
    org_id: str
    org_name: str
    broadcast_type: BroadcastType
    status: BroadcastStatus = BroadcastStatus.ACTIVE
    visibility: BroadcastVisibility = BroadcastVisibility.NETWORK_WIDE
    
    # Blood details
    blood_group: str
    component_type: Optional[str] = None
    units_needed: Optional[int] = None  # For urgent need
    units_available: Optional[int] = None  # For surplus
    expiry_date: Optional[str] = None  # For surplus - when units expire
    
    # Location for nearby filtering
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = 100.0  # For nearby_only visibility
    
    # Details
    title: str
    description: Optional[str] = None
    priority: str = "normal"  # normal, high, critical
    contact_phone: Optional[str] = None
    contact_name: Optional[str] = None
    
    # Tracking
    created_by: str
    created_by_name: str
    created_at: str
    expires_at: str  # Auto-expire after 48 hours by default
    updated_at: Optional[str] = None
    closed_at: Optional[str] = None
    closed_reason: Optional[str] = None
    
    # Responses
    response_count: int = 0


class BroadcastCreate(BaseModel):
    """Model for creating a new broadcast"""
    broadcast_type: BroadcastType
    visibility: BroadcastVisibility = BroadcastVisibility.NETWORK_WIDE
    blood_group: str
    component_type: Optional[str] = None
    units_needed: Optional[int] = None
    units_available: Optional[int] = None
    expiry_date: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str = "normal"
    contact_phone: Optional[str] = None
    contact_name: Optional[str] = None
    radius_km: Optional[float] = 100.0
    expires_in_hours: int = 48


class BroadcastResponseCreate(BaseModel):
    """Model for responding to a broadcast"""
    message: str
    units_offered: Optional[int] = None
    contact_phone: Optional[str] = None
