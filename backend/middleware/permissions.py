"""
Permission Checking Middleware for Custom Roles & Permissions
This module provides a FastAPI dependency for checking user permissions
based on their assigned role (system role or custom role).
"""
from fastapi import HTTPException, Depends
from functools import wraps

from database import db
from services import get_current_user
from models.role import AVAILABLE_MODULES, SYSTEM_ROLES


async def check_permission(user: dict, module: str, action: str) -> bool:
    """
    Check if user has permission for a specific module action.
    
    Priority order:
    1. System admins have all permissions
    2. Check custom_role_id if assigned
    3. Fall back to system role from DB
    4. Fall back to built-in SYSTEM_ROLES
    """
    # System admins have all permissions
    if user.get("user_type") == "system_admin":
        return True
    
    # Get user's role
    role_key = user.get("role")
    if not role_key:
        return False
    
    # First check if user has a custom role assigned
    custom_role_id = user.get("custom_role_id")
    if custom_role_id:
        role = await db.roles.find_one({"id": custom_role_id}, {"_id": 0})
        if role:
            permissions = role.get("permissions", {})
            return action in permissions.get(module, [])
    
    # Check system role from DB
    role = await db.roles.find_one({"role_key": role_key, "is_system_role": True}, {"_id": 0})
    if role:
        permissions = role.get("permissions", {})
        return action in permissions.get(module, [])
    
    # Fall back to built-in system roles
    if role_key in SYSTEM_ROLES:
        permissions = SYSTEM_ROLES[role_key]["permissions"]
        return action in permissions.get(module, [])
    
    return False


def require_permission(module: str, action: str):
    """
    FastAPI dependency factory that requires a specific permission.
    
    Usage:
        @router.post("/donors")
        async def create_donor(
            data: DonorCreate,
            current_user: dict = Depends(require_permission("donors", "create"))
        ):
            # Only users with donors.create permission can access this
            pass
    
    Args:
        module: The module name (e.g., "donors", "inventory", "laboratory")
        action: The action name (e.g., "view", "create", "edit", "delete")
    
    Returns:
        A FastAPI dependency that validates permission and returns the current user
    """
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        has_permission = await check_permission(current_user, module, action)
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {module}.{action}"
            )
        return current_user
    return permission_checker


def require_any_permission(module: str, actions: list):
    """
    FastAPI dependency that requires any one of the specified permissions.
    
    Usage:
        @router.get("/donors")
        async def list_donors(
            current_user: dict = Depends(require_any_permission("donors", ["view", "create", "edit"]))
        ):
            # Users with any of these permissions can access
            pass
    """
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        for action in actions:
            if await check_permission(current_user, module, action):
                return current_user
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: requires one of {module}.{actions}"
        )
    return permission_checker


def require_module_access(module: str):
    """
    FastAPI dependency that requires any access to a module.
    Equivalent to having at least one permission for the module.
    
    Usage:
        @router.get("/donors/stats")
        async def get_donor_stats(
            current_user: dict = Depends(require_module_access("donors"))
        ):
            pass
    """
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        # System admins always have access
        if current_user.get("user_type") == "system_admin":
            return current_user
        
        # Get all actions for this module
        module_actions = AVAILABLE_MODULES.get(module, [])
        
        # Check if user has any permission for this module
        for action in module_actions:
            if await check_permission(current_user, module, action):
                return current_user
        
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: no access to {module} module"
        )
    return permission_checker


async def get_user_permissions(user: dict) -> dict:
    """
    Get all permissions for a user.
    
    Returns a dictionary with:
    - role: The role key
    - role_name: Display name of the role
    - permissions: Dict of module -> list of actions
    - is_system_admin: Boolean
    - is_custom_role: Boolean (if using a custom role)
    """
    # System admin has all permissions
    if user.get("user_type") == "system_admin":
        return {
            "role": "system_admin",
            "role_name": "System Administrator",
            "permissions": AVAILABLE_MODULES,
            "is_system_admin": True,
            "is_custom_role": False
        }
    
    role_key = user.get("role")
    custom_role_id = user.get("custom_role_id")
    
    # Check custom role first
    if custom_role_id:
        role = await db.roles.find_one({"id": custom_role_id}, {"_id": 0})
        if role:
            return {
                "role": role.get("role_key"),
                "role_name": role.get("name"),
                "permissions": role.get("permissions", {}),
                "is_system_admin": False,
                "is_custom_role": True
            }
    
    # Check system role from DB
    role = await db.roles.find_one({"role_key": role_key, "is_system_role": True}, {"_id": 0})
    if role:
        return {
            "role": role.get("role_key"),
            "role_name": role.get("name"),
            "permissions": role.get("permissions", {}),
            "is_system_admin": False,
            "is_custom_role": False
        }
    
    # Fall back to built-in system roles
    if role_key in SYSTEM_ROLES:
        return {
            "role": role_key,
            "role_name": SYSTEM_ROLES[role_key]["name"],
            "permissions": SYSTEM_ROLES[role_key]["permissions"],
            "is_system_admin": False,
            "is_custom_role": False
        }
    
    # No role found - return empty permissions
    return {
        "role": role_key,
        "role_name": role_key,
        "permissions": {},
        "is_system_admin": False,
        "is_custom_role": False
    }
