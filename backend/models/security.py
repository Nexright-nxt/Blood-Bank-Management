"""
Security Models
Password Policy, MFA, Session Tracking, and API Keys.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid
import secrets


class MFAMethod(str, Enum):
    TOTP = "totp"
    EMAIL = "email"


class MFAStatus(str, Enum):
    DISABLED = "disabled"
    PENDING_SETUP = "pending_setup"
    ENABLED = "enabled"


# ==================== Password Policy ====================

class PasswordPolicy(BaseModel):
    """Organization-level password policy configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    org_id: Optional[str] = None  # None = system-wide default
    min_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    max_age_days: Optional[int] = 90  # Force password change after X days, None = never
    password_history_count: int = 5  # Prevent reuse of last N passwords
    max_failed_attempts: int = 5  # Lock account after X failed attempts
    lockout_duration_minutes: int = 30  # How long account stays locked
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class PasswordPolicyUpdate(BaseModel):
    min_length: Optional[int] = None
    require_uppercase: Optional[bool] = None
    require_lowercase: Optional[bool] = None
    require_numbers: Optional[bool] = None
    require_special_chars: Optional[bool] = None
    special_chars: Optional[str] = None
    max_age_days: Optional[int] = None
    password_history_count: Optional[int] = None
    max_failed_attempts: Optional[int] = None
    lockout_duration_minutes: Optional[int] = None


class PasswordHistory(BaseModel):
    """Tracks password history for reuse prevention"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== MFA ====================

class UserMFA(BaseModel):
    """User MFA configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    status: MFAStatus = MFAStatus.DISABLED
    primary_method: MFAMethod = MFAMethod.TOTP
    
    # TOTP settings
    totp_secret: Optional[str] = None
    totp_verified: bool = False
    
    # Email OTP settings
    email_otp_enabled: bool = False
    
    # Backup codes
    backup_codes: List[str] = []
    backup_codes_used: List[str] = []
    
    # Enforcement
    is_required: bool = False  # If True, user must set up MFA
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class MFASetupResponse(BaseModel):
    secret: str
    qr_code_uri: str
    backup_codes: List[str]


class MFAVerifyRequest(BaseModel):
    code: str
    method: MFAMethod = MFAMethod.TOTP


# ==================== Session Management ====================

class UserSession(BaseModel):
    """Active user session tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token_hash: str  # Hash of the JWT token for identification
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None
    is_active: bool = True
    is_current: bool = False  # Marks the current session
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


class SessionConfig(BaseModel):
    """Session configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    org_id: Optional[str] = None  # None = system-wide
    session_timeout_minutes: int = 480  # 8 hours default
    max_concurrent_sessions: int = 5
    require_re_auth_for_sensitive: bool = True  # Require password for sensitive ops
    track_device_info: bool = True
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== API Keys ====================

class APIKeyScope(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    INVENTORY = "inventory"
    DONORS = "donors"
    REPORTS = "reports"


class APIKey(BaseModel):
    """API Key for external integrations"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str
    name: str
    description: Optional[str] = None
    key_prefix: str = ""  # First 8 chars for identification
    key_hash: str = ""  # Hashed full key
    scopes: List[APIKeyScope] = [APIKeyScope.READ]
    is_active: bool = True
    expires_at: Optional[str] = None  # YYYY-MM-DD
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    rate_limit_per_minute: int = 60
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None


class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scopes: List[APIKeyScope] = [APIKeyScope.READ]
    expires_at: Optional[str] = None
    rate_limit_per_minute: int = 60


class APIKeyResponse(BaseModel):
    """Response when creating a new API key - includes the raw key"""
    id: str
    name: str
    key: str  # Only shown once at creation
    key_prefix: str
    scopes: List[str]
    expires_at: Optional[str]
    created_at: str


# ==================== Account Lockout ====================

class AccountLockout(BaseModel):
    """Tracks failed login attempts and account lockouts"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    failed_attempts: int = 0
    last_failed_at: Optional[datetime] = None
    locked_until: Optional[datetime] = None
    is_locked: bool = False
    unlock_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== Helper Functions ====================

def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate random backup codes"""
    return [secrets.token_hex(4).upper() for _ in range(count)]


def generate_api_key() -> tuple:
    """Generate a new API key, returns (full_key, prefix, hash)"""
    import hashlib
    full_key = f"bbk_{secrets.token_urlsafe(32)}"
    prefix = full_key[:12]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


def hash_token(token: str) -> str:
    """Hash a token for storage"""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


# Default password policy
DEFAULT_PASSWORD_POLICY = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special_chars": True,
    "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
    "max_age_days": 90,
    "password_history_count": 5,
    "max_failed_attempts": 5,
    "lockout_duration_minutes": 30
}
