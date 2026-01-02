"""
Configuration & Logistics Module - Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ==================== FORM BUILDER ====================

class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    DROPDOWN = "dropdown"
    MULTI_SELECT = "multi_select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DATE = "date"
    FILE = "file"
    TEXTAREA = "textarea"

class FormField(BaseModel):
    name: str
    label: str
    field_type: FieldType
    required: bool = False
    options: Optional[List[str]] = None  # For dropdown, multi_select, radio
    validation: Optional[Dict[str, Any]] = None  # {min, max, pattern, minLength, maxLength}
    help_text: Optional[str] = None
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None
    is_system_field: bool = False  # Non-deletable fields like Donor ID, Blood Group
    order: int = 0

class FormConfiguration(BaseModel):
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    form_name: str  # donor_registration, health_screening, collection, lab_tests, etc.
    form_schema: List[FormField] = []
    is_active: bool = True
    version: int = 1
    updated_by: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class FormConfigurationCreate(BaseModel):
    form_name: str
    form_schema: List[FormField] = []

class FormFieldCreate(BaseModel):
    name: str
    label: str
    field_type: FieldType
    required: bool = False
    options: Optional[List[str]] = None
    validation: Optional[Dict[str, Any]] = None
    help_text: Optional[str] = None
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None

# ==================== WORKFLOW RULES ENGINE ====================

class TriggerEvent(str, Enum):
    ON_SUBMIT = "on_submit"
    ON_FIELD_CHANGE = "on_field_change"
    ON_STATUS_CHANGE = "on_status_change"
    SCHEDULED_DAILY = "scheduled_daily"
    SCHEDULED_WEEKLY = "scheduled_weekly"

class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    EMPTY = "empty"
    NOT_EMPTY = "not_empty"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"

class ActionType(str, Enum):
    SET_FIELD = "set_field"
    SET_STATUS = "set_status"
    SEND_NOTIFICATION = "send_notification"
    CREATE_ALERT = "create_alert"
    SEND_EMAIL = "send_email"
    AUTO_QUARANTINE = "auto_quarantine"
    AUTO_DEFER = "auto_defer"
    BLOCK_SUBMISSION = "block_submission"

class RuleCondition(BaseModel):
    field: str
    operator: ConditionOperator
    value: Any
    logic: str = "AND"  # AND, OR

class RuleAction(BaseModel):
    action_type: ActionType
    params: Dict[str, Any] = {}  # {field_name, value, message, recipient, etc.}

class WorkflowRule(BaseModel):
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    rule_name: str
    module: str  # donor, screening, collection, lab, inventory, etc.
    trigger_event: TriggerEvent
    conditions: List[RuleCondition] = []
    actions: List[RuleAction] = []
    is_active: bool = True
    priority: int = 0  # Higher priority = runs first
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None

class WorkflowRuleCreate(BaseModel):
    rule_name: str
    module: str
    trigger_event: TriggerEvent
    conditions: List[RuleCondition] = []
    actions: List[RuleAction] = []
    priority: int = 0
    is_active: bool = True

# ==================== TRIGGERS ====================

class TriggerType(str, Enum):
    BEFORE_INSERT = "before_insert"
    AFTER_INSERT = "after_insert"
    BEFORE_UPDATE = "before_update"
    AFTER_UPDATE = "after_update"
    BEFORE_DELETE = "before_delete"

class DatabaseTrigger(BaseModel):
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    trigger_name: str
    trigger_type: TriggerType
    table_name: str  # donors, screenings, donations, inventory, etc.
    workflow_rule_id: Optional[str] = None  # Link to workflow rule
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class TriggerCreate(BaseModel):
    trigger_name: str
    trigger_type: TriggerType
    table_name: str
    workflow_rule_id: Optional[str] = None

# ==================== VEHICLES ====================

class Vehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    vehicle_id: Optional[str] = None  # Auto-generated
    vehicle_type: str  # ambulance, van, bike, car
    vehicle_model: str
    registration_number: str
    capacity: int  # Number of units can carry
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_license: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None

class VehicleCreate(BaseModel):
    vehicle_type: str
    vehicle_model: str
    registration_number: str
    capacity: int
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_license: Optional[str] = None

# ==================== COURIER PARTNERS ====================

class CourierPartner(BaseModel):
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    company_name: str
    contact_person: str
    contact_phone: str
    contact_email: Optional[str] = None
    address: Optional[str] = None
    service_areas: List[str] = []
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class CourierPartnerCreate(BaseModel):
    company_name: str
    contact_person: str
    contact_phone: str
    contact_email: Optional[str] = None
    address: Optional[str] = None
    service_areas: List[str] = []

# ==================== TRANSPORT & TRACKING ====================

class TransportMethod(str, Enum):
    SELF_VEHICLE = "self_vehicle"
    THIRD_PARTY = "third_party"

class TrackingStatus(str, Enum):
    PREPARING = "preparing"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    FAILED = "failed"

class TrackingUpdate(BaseModel):
    timestamp: str
    location: str
    status: TrackingStatus
    updated_by: str
    notes: Optional[str] = None

# ==================== SYSTEM SETTINGS ====================

class SystemSettings(BaseModel):
    id: str = "system_settings"
    # Eligibility thresholds
    min_hemoglobin_male: float = 13.0
    min_hemoglobin_female: float = 12.5
    min_weight_kg: float = 50.0
    min_age: int = 18
    max_age: int = 65
    min_bp_systolic: int = 90
    max_bp_systolic: int = 180
    min_bp_diastolic: int = 60
    max_bp_diastolic: int = 100
    # Donation intervals
    min_donation_interval_days: int = 56
    # Storage temperatures
    whole_blood_temp_min: float = 2.0
    whole_blood_temp_max: float = 6.0
    plasma_temp_min: float = -25.0
    plasma_temp_max: float = -18.0
    platelet_temp_min: float = 20.0
    platelet_temp_max: float = 24.0
    # Alert settings
    expiry_alert_days: int = 7
    low_stock_threshold: int = 5
    # Updated tracking
    updated_by: Optional[str] = None
    updated_at: Optional[str] = None

# ==================== CONFIG AUDIT LOG ====================

class ConfigAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    config_type: str  # form, rule, trigger, vehicle, settings
    config_id: str
    action: str  # create, update, delete, activate, deactivate
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changed_by: str
    changed_at: str = Field(default_factory=lambda: datetime.now().isoformat())
