from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from enum import Enum

# Default storage types (can be extended with custom types)
class StorageType(str, Enum):
    REFRIGERATOR = "refrigerator"
    FREEZER = "freezer"
    PLATELET_INCUBATOR = "platelet_incubator"
    QUARANTINE_AREA = "quarantine_area"
    CUSTOM = "custom"  # For custom storage types

# Custom Storage Type model
class CustomStorageType(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type_code: str  # Unique identifier like "cryo_storage"
    type_name: str  # Display name like "Cryo Storage"
    description: Optional[str] = None
    default_temp_range: str  # e.g., "-196°C" for cryo
    icon: str = "📦"  # Emoji or icon identifier
    color: str = "slate"  # Color theme (slate, blue, red, amber, etc.)
    suitable_for: List[str] = []  # ["plasma", "stem_cells", etc.]
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None

class CustomStorageTypeCreate(BaseModel):
    type_code: str
    type_name: str
    description: Optional[str] = None
    default_temp_range: str
    icon: str = "📦"
    color: str = "slate"
    suitable_for: List[str] = []

class StorageLocation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    storage_name: str
    storage_type: str  # Changed from StorageType enum to str to support custom types
    temperature_range: str
    capacity: int
    current_occupancy: int = 0
    location_code: str
    facility: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None

class StorageLocationCreate(BaseModel):
    storage_name: str
    storage_type: str  # Changed to str to support custom types
    temperature_range: str
    capacity: int
    location_code: str
    facility: str
