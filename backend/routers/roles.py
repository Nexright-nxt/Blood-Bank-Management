"""
Roles Router - Custom Roles & Permissions Management
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database import db
from models.role import (
    Role, RoleCreate, RoleUpdate, RoleResponse,
    AVAILABLE_MODULES, SYSTEM_ROLES
)
from routers.auth import get_current_user
from middleware.permissions import check_permission, get_user_permissions

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/available-modules")
async def get_available_modules(current_user: dict = Depends(get_current_user)):
    """Get all available modules and their actions for role creation"""
    return {
        "modules": AVAILABLE_MODULES,
        "system_roles": {k: {"name": v["name"], "description": v["description"]} 
                        for k, v in SYSTEM_ROLES.items()}
    }


@router.get("/my-permissions")
async def get_my_permissions(current_user: dict = Depends(get_current_user)):
    """Get current user's permissions"""
    return await get_user_permissions(current_user)


@router.get("", response_model=List[RoleResponse])
async def get_roles(current_user: dict = Depends(get_current_user)):
    """Get all roles (system + custom for user's org)"""
    # System admins see all roles
    if current_user.get("user_type") == "system_admin":
        query = {}
    else:
        # Other users see system roles + their org's custom roles
        org_id = current_user.get("org_id")
        query = {"$or": [
            {"is_system_role": True},
            {"org_id": org_id}
        ]}
    
    roles = await db.roles.find(query, {"_id": 0}).to_list(1000)
    
    # Count users per role
    for role in roles:
        if role.get("is_system_role"):
            # Count users with this role_key
            count = await db.users.count_documents({"role": role.get("role_key")})
        else:
            # Count users with this custom_role_id
            count = await db.users.count_documents({"custom_role_id": role.get("id")})
        role["users_count"] = count
    
    return roles


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific role"""
    role = await db.roles.find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check access
    if not role.get("is_system_role") and role.get("org_id") != current_user.get("org_id"):
        if current_user.get("user_type") != "system_admin":
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Count users
    if role.get("is_system_role"):
        role["users_count"] = await db.users.count_documents({"role": role.get("role_key")})
    else:
        role["users_count"] = await db.users.count_documents({"custom_role_id": role.get("id")})
    
    return role


@router.post("", response_model=RoleResponse)
async def create_role(role_data: RoleCreate, current_user: dict = Depends(get_current_user)):
    """Create a custom role"""
    # Only admins can create roles
    if current_user.get("user_type") not in ["system_admin", "super_admin", "tenant_admin"]:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only admins can create roles")
    
    # Validate permissions
    for module, actions in role_data.permissions.items():
        if module not in AVAILABLE_MODULES:
            raise HTTPException(status_code=400, detail=f"Invalid module: {module}")
        for action in actions:
            if action not in AVAILABLE_MODULES[module]:
                raise HTTPException(status_code=400, detail=f"Invalid action '{action}' for module '{module}'")
    
    # Generate role key
    role_key = f"custom_{uuid.uuid4().hex[:8]}"
    
    role = Role(
        role_key=role_key,
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
        is_system_role=False,
        org_id=current_user.get("org_id") if current_user.get("user_type") != "system_admin" else None,
        created_by=current_user.get("id")
    )
    
    await db.roles.insert_one(role.model_dump())
    
    result = role.model_dump()
    result["users_count"] = 0
    return result


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: str, role_data: RoleUpdate, current_user: dict = Depends(get_current_user)):
    """Update a custom role"""
    role = await db.roles.find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Cannot edit system roles
    if role.get("is_system_role"):
        raise HTTPException(status_code=403, detail="Cannot edit system roles")
    
    # Check access
    if role.get("org_id") != current_user.get("org_id"):
        if current_user.get("user_type") != "system_admin":
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate permissions if provided
    if role_data.permissions:
        for module, actions in role_data.permissions.items():
            if module not in AVAILABLE_MODULES:
                raise HTTPException(status_code=400, detail=f"Invalid module: {module}")
            for action in actions:
                if action not in AVAILABLE_MODULES[module]:
                    raise HTTPException(status_code=400, detail=f"Invalid action '{action}' for module '{module}'")
    
    update_data = {k: v for k, v in role_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.roles.update_one({"id": role_id}, {"$set": update_data})
    
    updated_role = await db.roles.find_one({"id": role_id}, {"_id": 0})
    updated_role["users_count"] = await db.users.count_documents({"custom_role_id": role_id})
    return updated_role


@router.delete("/{role_id}")
async def delete_role(role_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a custom role"""
    role = await db.roles.find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Cannot delete system roles
    if role.get("is_system_role"):
        raise HTTPException(status_code=403, detail="Cannot delete system roles")
    
    # Check access
    if role.get("org_id") != current_user.get("org_id"):
        if current_user.get("user_type") != "system_admin":
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if role is assigned to any users
    users_count = await db.users.count_documents({"custom_role_id": role_id})
    if users_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete role: {users_count} user(s) are assigned to this role"
        )
    
    await db.roles.delete_one({"id": role_id})
    return {"status": "success", "message": "Role deleted"}


@router.post("/{role_id}/duplicate", response_model=RoleResponse)
async def duplicate_role(role_id: str, current_user: dict = Depends(get_current_user)):
    """Duplicate an existing role"""
    role = await db.roles.find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Generate new role
    role_key = f"custom_{uuid.uuid4().hex[:8]}"
    
    new_role = Role(
        role_key=role_key,
        name=f"{role['name']} (Copy)",
        description=role.get("description"),
        permissions=role.get("permissions", {}),
        is_system_role=False,
        org_id=current_user.get("org_id") if current_user.get("user_type") != "system_admin" else None,
        created_by=current_user.get("id")
    )
    
    await db.roles.insert_one(new_role.model_dump())
    
    result = new_role.model_dump()
    result["users_count"] = 0
    return result


async def seed_system_roles():
    """Seed system roles if they don't exist"""
    for role_key, role_info in SYSTEM_ROLES.items():
        existing = await db.roles.find_one({"role_key": role_key, "is_system_role": True})
        if not existing:
            role = Role(
                role_key=role_key,
                name=role_info["name"],
                description=role_info["description"],
                permissions=role_info["permissions"],
                is_system_role=True,
                org_id=None
            )
            await db.roles.insert_one(role.model_dump())
            print(f"Created system role: {role_key}")
