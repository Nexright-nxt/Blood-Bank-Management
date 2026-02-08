"""
Role Model for Custom Roles & Permissions
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional, Dict, List
import uuid

# Define all available modules and their actions
AVAILABLE_MODULES = {
    "dashboard": ["view"],
    "donors": ["view", "create", "edit", "delete"],
    "donations": ["view", "create", "edit"],
    "screening": ["view", "create", "edit"],
    "laboratory": ["view", "create", "edit", "verify"],
    "processing": ["view", "create", "edit"],
    "qc_validation": ["view", "create", "edit", "approve"],
    "inventory": ["view", "move", "reserve", "transfer"],
    "requests": ["view", "create", "edit", "approve", "reject", "fulfill"],
    "distribution": ["view", "create", "edit"],
    "logistics": ["view", "create", "edit", "dispatch", "deliver"],
    "returns": ["view", "create", "edit", "approve"],
    "discards": ["view", "create", "approve"],
    "reports": ["view", "export"],
    "users": ["view", "create", "edit", "delete"],
    "organizations": ["view", "create", "edit", "delete"],
    "roles": ["view", "create", "edit", "delete"],
    "configuration": ["view", "edit"],
    "audit_logs": ["view", "export"],
    "storage": ["view", "create", "edit", "delete"],
    "alerts": ["view", "manage"],
}

# Default system roles with their permissions
SYSTEM_ROLES = {
    "admin": {
        "name": "Administrator",
        "description": "Full access to all modules",
        "permissions": {module: actions for module, actions in AVAILABLE_MODULES.items()}
    },
    "registration": {
        "name": "Registration Staff",
        "description": "Manage donor registration and screening",
        "permissions": {
            "dashboard": ["view"],
            "donors": ["view", "create", "edit"],
            "donations": ["view", "create"],
            "screening": ["view", "create", "edit"],
        }
    },
    "lab_tech": {
        "name": "Lab Technician",
        "description": "Perform laboratory tests",
        "permissions": {
            "dashboard": ["view"],
            "laboratory": ["view", "create", "edit"],
            "donors": ["view"],
            "donations": ["view"],
            "inventory": ["view"],
        }
    },
    "processing": {
        "name": "Processing Staff",
        "description": "Process blood components",
        "permissions": {
            "dashboard": ["view"],
            "processing": ["view", "create", "edit"],
            "laboratory": ["view"],
            "inventory": ["view"],
        }
    },
    "qc_manager": {
        "name": "QC Manager",
        "description": "Quality control and validation",
        "permissions": {
            "dashboard": ["view"],
            "qc_validation": ["view", "create", "edit", "approve"],
            "laboratory": ["view", "verify"],
            "processing": ["view"],
            "inventory": ["view"],
            "discards": ["view", "create", "approve"],
        }
    },
    "inventory": {
        "name": "Inventory Manager",
        "description": "Manage blood inventory",
        "permissions": {
            "dashboard": ["view"],
            "inventory": ["view", "move", "reserve", "transfer"],
            "storage": ["view", "create", "edit"],
            "requests": ["view"],
            "distribution": ["view", "create"],
            "logistics": ["view", "create"],
            "returns": ["view", "create"],
            "discards": ["view", "create"],
        }
    },
    "distribution": {
        "name": "Distribution Staff",
        "description": "Handle blood distribution",
        "permissions": {
            "dashboard": ["view"],
            "distribution": ["view", "create", "edit"],
            "requests": ["view", "fulfill"],
            "logistics": ["view", "create", "edit", "dispatch", "deliver"],
            "inventory": ["view", "reserve"],
            "returns": ["view", "create", "edit"],
        }
    },
    "phlebotomist": {
        "name": "Phlebotomist",
        "description": "Collect blood donations",
        "permissions": {
            "dashboard": ["view"],
            "donations": ["view", "create", "edit"],
            "donors": ["view"],
            "screening": ["view"],
        }
    },
}


class Role(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role_key: str  # Unique key like 'admin', 'lab_tech', or custom 'custom_role_123'
    name: str  # Display name
    description: Optional[str] = None
    permissions: Dict[str, List[str]] = Field(default_factory=dict)  # {module: [actions]}
    
    is_system_role: bool = False  # System roles cannot be edited/deleted
    org_id: Optional[str] = None  # None for system-wide roles, org_id for org-specific
    
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Dict[str, List[str]] = Field(default_factory=dict)


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, List[str]]] = None


class RoleResponse(BaseModel):
    id: str
    role_key: str
    name: str
    description: Optional[str] = None
    permissions: Dict[str, List[str]]
    is_system_role: bool
    org_id: Optional[str] = None
    users_count: int = 0
    created_at: datetime
    updated_at: datetime


class PermissionCheck(BaseModel):
    """For checking if user has permission"""
    module: str
    action: str
