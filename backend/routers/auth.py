from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid
import pyotp

import sys
sys.path.append('..')

from database import db
from models import User, UserCreate, UserLogin, UserResponse, UserType
from models.audit import AuditAction, AuditModule
from services import hash_password, verify_password, create_token, get_current_user, AuditService


class MFAVerifyLogin(BaseModel):
    """Request body for MFA verification during login"""
    mfa_token: str  # Temporary token from initial login
    mfa_code: str   # TOTP code or backup code
    mfa_method: str = "totp"  # "totp" or "backup_code"


def get_device_info(user_agent: str) -> str:
    """Extract device info from user agent string"""
    if not user_agent:
        return "Unknown Device"
    
    user_agent_lower = user_agent.lower()
    
    # Detect browser
    browser = "Unknown Browser"
    if "chrome" in user_agent_lower and "edg" not in user_agent_lower:
        browser = "Chrome"
    elif "firefox" in user_agent_lower:
        browser = "Firefox"
    elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
        browser = "Safari"
    elif "edg" in user_agent_lower:
        browser = "Edge"
    elif "opera" in user_agent_lower or "opr" in user_agent_lower:
        browser = "Opera"
    
    # Detect OS
    os_name = "Unknown OS"
    if "windows" in user_agent_lower:
        os_name = "Windows"
    elif "mac" in user_agent_lower:
        os_name = "macOS"
    elif "linux" in user_agent_lower:
        os_name = "Linux"
    elif "android" in user_agent_lower:
        os_name = "Android"
    elif "iphone" in user_agent_lower or "ipad" in user_agent_lower:
        os_name = "iOS"
    
    return f"{browser} on {os_name}"

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request, current_user: dict = Depends(get_current_user)):
    """
    Register a new staff user.
    - System Admin: Can create any user type in any org
    - Super Admin: Can create Tenant Admin and Staff in own org + children
    - Tenant Admin: Can create Staff in own org only
    """
    creator_type = current_user.get("user_type", "staff")
    creator_org_id = current_user.get("org_id")
    
    # Permission checks
    if creator_type == "staff":
        raise HTTPException(status_code=403, detail="Staff cannot create users")
    
    if current_user["role"] != "admin" and creator_type not in ["system_admin", "super_admin", "tenant_admin"]:
        raise HTTPException(
            status_code=403, 
            detail="Only administrators can create staff accounts"
        )
    
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Determine target org_id
    target_org_id = user_data.org_id
    if not target_org_id and creator_org_id:
        target_org_id = creator_org_id
    
    # Validate user_type creation permissions
    new_user_type = user_data.user_type or UserType.STAFF
    
    if creator_type == "super_admin":
        if new_user_type == UserType.SYSTEM_ADMIN:
            raise HTTPException(status_code=403, detail="Super Admin cannot create System Admins")
        if new_user_type == UserType.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Super Admin cannot create other Super Admins")
        # Verify target org is self or child
        if target_org_id and target_org_id != creator_org_id:
            child_org = await db.organizations.find_one({"id": target_org_id, "parent_org_id": creator_org_id})
            if not child_org:
                raise HTTPException(status_code=403, detail="Can only create users in own organization or child branches")
    
    elif creator_type == "tenant_admin":
        if new_user_type in [UserType.SYSTEM_ADMIN, UserType.SUPER_ADMIN, UserType.TENANT_ADMIN]:
            raise HTTPException(status_code=403, detail="Tenant Admin can only create Staff users")
        if target_org_id and target_org_id != creator_org_id:
            raise HTTPException(status_code=403, detail="Tenant Admin can only create users in own organization")
        target_org_id = creator_org_id
    
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        org_id=target_org_id,
        user_type=new_user_type
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.users.insert_one(doc)
    
    # Audit log - user created
    await AuditService.log(
        action=AuditAction.CREATE,
        module=AuditModule.USERS,
        user=current_user,
        record_id=user.id,
        record_type="user",
        description=f"Created user {user.email} ({new_user_type.value})",
        new_values={"email": user.email, "full_name": user.full_name, "role": user.role.value, "user_type": new_user_type.value},
        request=request,
        org_id=target_org_id
    )
    
    # Get org name for response
    org_name = None
    if target_org_id:
        org = await db.organizations.find_one({"id": target_org_id}, {"org_name": 1})
        org_name = org.get("org_name") if org else None
    
    return UserResponse(
        id=user.id, 
        email=user.email, 
        full_name=user.full_name, 
        role=user.role, 
        is_active=user.is_active,
        org_id=user.org_id,
        user_type=user.user_type,
        org_name=org_name
    )

@router.post("/login")
async def login(credentials: UserLogin, request: Request):
    """
    Login with email, password, and optionally org_id.
    If MFA is enabled, returns mfa_required=True with a temporary token.
    User must then call /auth/login/mfa-verify to complete login.
    """
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        # Log failed login attempt
        await AuditService.log_auth(
            AuditAction.LOGIN_FAILED,
            credentials.email,
            success=False,
            request=request,
            details="Invalid credentials - user not found"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user["password_hash"]):
        # Log failed login attempt
        await AuditService.log_auth(
            AuditAction.LOGIN_FAILED,
            credentials.email,
            success=False,
            request=request,
            user=user,
            details="Invalid credentials - wrong password"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        await AuditService.log_auth(
            AuditAction.LOGIN_FAILED,
            credentials.email,
            success=False,
            request=request,
            user=user,
            details="Account is disabled"
        )
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    user_type = user.get("user_type", "staff")
    user_org_id = user.get("org_id")
    
    # System admin doesn't need org selection
    if user_type == "system_admin":
        selected_org_id = credentials.org_id  # Optional for system admin
    else:
        # Non-system users must have an org
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User account not associated with any organization")
        
        # If org_id provided in login, validate it matches user's org
        if credentials.org_id and credentials.org_id != user_org_id:
            raise HTTPException(status_code=403, detail="You don't have access to this organization")
        
        selected_org_id = user_org_id
    
    # Get org info
    org_name = None
    if selected_org_id:
        org = await db.organizations.find_one({"id": selected_org_id}, {"_id": 0})
        if org:
            org_name = org.get("org_name")
            if not org.get("is_active", True):
                raise HTTPException(status_code=403, detail="Organization is deactivated")
    
    # Check if user has MFA enabled
    mfa_record = await db.user_mfa.find_one({"user_id": user["id"]}, {"_id": 0})
    mfa_enabled = mfa_record and mfa_record.get("status") == "enabled" and mfa_record.get("totp_verified", False)
    
    if mfa_enabled:
        # MFA is enabled - create a temporary MFA token and require verification
        mfa_token = str(uuid.uuid4())
        
        # Store the pending MFA verification with all login context
        await db.mfa_pending_logins.delete_many({"user_id": user["id"]})  # Clean old pending
        await db.mfa_pending_logins.insert_one({
            "mfa_token": mfa_token,
            "user_id": user["id"],
            "user_email": user["email"],
            "user_full_name": user.get("full_name"),
            "user_role": user["role"],
            "user_type": user_type,
            "selected_org_id": selected_org_id,
            "org_name": org_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", "")
        })
        
        # Log MFA challenge
        await AuditService.log_auth(
            AuditAction.LOGIN,
            credentials.email,
            success=True,
            request=request,
            user=user,
            details="MFA challenge issued - awaiting verification"
        )
        
        return {
            "mfa_required": True,
            "mfa_token": mfa_token,
            "message": "MFA verification required",
            "user": {
                "email": user["email"],
                "full_name": user.get("full_name")
            }
        }
    
    # No MFA - complete login directly
    return await complete_login(user, user_type, selected_org_id, org_name, request)


async def complete_login(user: dict, user_type: str, selected_org_id: str, org_name: str, request: Request):
    """Complete the login process and return token"""
    # Create token with org info
    token = create_token(
        user["id"], 
        user["role"],
        org_id=selected_org_id,
        user_type=user_type
    )
    
    # Create user session record
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    device_info = get_device_info(user_agent)
    
    session_data = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_email": user["email"],
        "user_name": user.get("full_name"),
        "user_type": user_type,
        "user_org_id": selected_org_id,
        "ip_address": client_ip,
        "user_agent": user_agent,
        "device_info": device_info,
        "login_at": datetime.now(timezone.utc).isoformat(),
        "last_activity": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "is_active": True,
        "is_current": True
    }
    
    await db.user_sessions.insert_one(session_data)
    
    # Log successful login
    await AuditService.log_auth(
        AuditAction.LOGIN,
        user["email"],
        success=True,
        request=request,
        user=user,
        details=f"Successful login as {user_type}"
    )
    
    return {
        "token": token,
        "user": UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            is_active=user.get("is_active", True),
            org_id=selected_org_id,
            user_type=user_type,
            org_name=org_name
        )
    }


@router.post("/login/mfa-verify")
async def verify_mfa_login(mfa_data: MFAVerifyLogin, request: Request):
    """
    Verify MFA code and complete the login process.
    Called after initial login returns mfa_required=True.
    """
    # Find the pending MFA login
    pending = await db.mfa_pending_logins.find_one({"mfa_token": mfa_data.mfa_token}, {"_id": 0})
    
    if not pending:
        raise HTTPException(status_code=401, detail="Invalid or expired MFA session")
    
    # Check if token expired
    expires_at = datetime.fromisoformat(pending["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        await db.mfa_pending_logins.delete_one({"mfa_token": mfa_data.mfa_token})
        raise HTTPException(status_code=401, detail="MFA session expired. Please login again.")
    
    user_id = pending["user_id"]
    
    # Get user's MFA settings
    mfa_record = await db.user_mfa.find_one({"user_id": user_id}, {"_id": 0})
    if not mfa_record:
        raise HTTPException(status_code=400, detail="MFA not configured for this user")
    
    # Verify the code based on method
    verified = False
    
    if mfa_data.mfa_method == "totp":
        # Verify TOTP code
        if not mfa_record.get("totp_secret"):
            raise HTTPException(status_code=400, detail="TOTP not configured")
        
        totp = pyotp.TOTP(mfa_record["totp_secret"])
        verified = totp.verify(mfa_data.mfa_code, valid_window=1)
        
    elif mfa_data.mfa_method == "backup_code":
        # Verify backup code
        backup_codes = mfa_record.get("backup_codes", [])
        backup_codes_used = mfa_record.get("backup_codes_used", [])
        
        if mfa_data.mfa_code in backup_codes and mfa_data.mfa_code not in backup_codes_used:
            verified = True
            # Mark backup code as used
            await db.user_mfa.update_one(
                {"user_id": user_id},
                {"$push": {"backup_codes_used": mfa_data.mfa_code}}
            )
    
    if not verified:
        # Log failed MFA attempt
        await AuditService.log_auth(
            AuditAction.LOGIN_FAILED,
            pending["user_email"],
            success=False,
            request=request,
            details="Invalid MFA code"
        )
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    # MFA verified - complete login
    # Clean up pending login
    await db.mfa_pending_logins.delete_one({"mfa_token": mfa_data.mfa_token})
    
    # Get full user data
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log successful MFA verification
    await AuditService.log_auth(
        AuditAction.LOGIN,
        pending["user_email"],
        success=True,
        request=request,
        user=user,
        details="MFA verification successful"
    )
    
    return await complete_login(
        user,
        pending["user_type"],
        pending["selected_org_id"],
        pending["org_name"],
        request
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    # Get org name
    org_name = None
    org_id = current_user.get("org_id")
    if org_id:
        org = await db.organizations.find_one({"id": org_id}, {"org_name": 1})
        org_name = org.get("org_name") if org else None
    
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        is_active=current_user.get("is_active", True),
        org_id=org_id,
        user_type=current_user.get("user_type", "staff"),
        org_name=org_name
    )
