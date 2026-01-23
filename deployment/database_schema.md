# Blood Link Database Schema
## MongoDB Collections

This document describes the MongoDB collections used by Blood Link.

---

## Core Collections

### users
Stores all system users (staff, admins).

```javascript
{
  id: String,              // UUID
  email: String,           // Unique, indexed
  password_hash: String,   // bcrypt hashed
  full_name: String,
  role: String,            // "admin", "staff", etc.
  user_type: String,       // "system_admin", "super_admin", "tenant_admin", "staff"
  org_id: String,          // Reference to organizations.id (null for system_admin)
  is_active: Boolean,
  phone: String,
  department: String,
  permissions: [String],
  created_at: String,      // ISO datetime
  updated_at: String
}
// Indexes: email (unique)
```

### organizations
Multi-tenant organization management.

```javascript
{
  id: String,              // UUID
  org_code: String,        // Unique code (e.g., "BLC001")
  org_name: String,
  org_type: String,        // "hospital", "blood_bank_chain", "government", "ngo"
  is_parent: Boolean,      // True if parent org
  parent_org_id: String,   // Reference to parent (null if parent)
  address: String,
  city: String,
  state: String,
  country: String,
  phone: String,
  email: String,
  license_number: String,
  license_expiry: String,
  is_active: Boolean,
  storage_capacity: Number,
  operating_hours: String,
  created_at: String,
  updated_at: String
}
// Indexes: org_code (unique), parent_org_id
```

### donors
Registered blood donors.

```javascript
{
  id: String,              // UUID
  org_id: String,          // Organization reference
  donor_code: String,      // Auto-generated (e.g., "DNR-2025-000001")
  full_name: String,
  id_type: String,         // "mykad", "passport", etc.
  id_number: String,
  email: String,
  phone: String,
  date_of_birth: String,
  gender: String,
  blood_group: String,     // "A+", "B-", etc. (null until confirmed)
  address: String,
  city: String,
  state: String,
  country: String,
  postal_code: String,
  emergency_contact_name: String,
  emergency_contact_phone: String,
  medical_history: Object,
  is_active: Boolean,
  is_verified: Boolean,
  last_donation_date: String,
  total_donations: Number,
  created_at: String,
  updated_at: String
}
// Indexes: donor_code (unique), org_id, email
```

### donations
Blood donation records.

```javascript
{
  id: String,              // UUID
  org_id: String,
  donation_number: String, // Auto-generated
  donor_id: String,        // Reference to donors.id
  donation_type: String,   // "whole_blood", "apheresis_platelets", etc.
  donation_date: String,
  collection_site: String,
  collected_by: String,    // Staff user ID
  volume_ml: Number,
  bag_type: String,
  status: String,          // "pending", "completed", "cancelled"
  screening_id: String,    // Reference to screenings.id
  notes: String,
  created_at: String,
  updated_at: String
}
// Indexes: donation_number (unique), org_id, donor_id
```

### blood_units
Individual blood unit tracking.

```javascript
{
  id: String,              // UUID
  org_id: String,
  unit_id: String,         // Barcode/identifier
  donation_id: String,     // Reference to donations.id
  donor_id: String,
  blood_group: String,
  rh_factor: String,
  donation_date: String,
  expiry_date: String,
  volume_ml: Number,
  status: String,          // "quarantine", "available", "reserved", "issued", "expired", "discarded"
  storage_location: String,
  temperature_log: [Object],
  sample_labels: [String],
  created_at: String,
  updated_at: String
}
// Indexes: unit_id (unique), org_id, status, blood_group, expiry_date
```

### components
Blood components derived from whole blood.

```javascript
{
  id: String,              // UUID
  org_id: String,
  component_id: String,    // Unique identifier
  unit_id: String,         // Parent blood unit
  component_type: String,  // "prbc", "ffp", "platelets", "cryoprecipitate"
  blood_group: String,
  volume_ml: Number,
  status: String,
  storage_location: String,
  processing_date: String,
  expiry_date: String,
  processed_by: String,
  created_at: String,
  updated_at: String
}
// Indexes: component_id (unique), org_id, status, component_type
```

### lab_tests
Laboratory testing results.

```javascript
{
  id: String,              // UUID
  org_id: String,
  unit_id: String,
  test_date: String,
  tested_by: String,
  hiv_result: String,      // "negative", "positive", "inconclusive"
  hbsag_result: String,
  hcv_result: String,
  syphilis_result: String,
  malaria_result: String,
  overall_status: String,  // "passed", "failed", "pending"
  blood_group_test: String,
  rh_factor_test: String,
  confirmed_blood_group: String,
  notes: String,
  created_at: String,
  updated_at: String
}
// Indexes: org_id, unit_id, overall_status
```

### blood_requests
Blood requisition requests.

```javascript
{
  id: String,              // UUID
  org_id: String,
  request_number: String,
  patient_name: String,
  patient_id: String,
  patient_age: Number,
  patient_gender: String,
  blood_group: String,
  component_type: String,
  units_requested: Number,
  units_issued: Number,
  priority: String,        // "routine", "urgent", "emergency"
  status: String,          // "pending", "approved", "fulfilled", "cancelled"
  requested_by: String,
  requesting_facility: String,
  diagnosis: String,
  notes: String,
  created_at: String,
  updated_at: String
}
// Indexes: request_number (unique), org_id, status, priority
```

---

## Security Collections

### user_mfa
MFA configuration per user.

```javascript
{
  user_id: String,         // Reference to users.id
  status: String,          // "disabled", "pending", "enabled"
  totp_secret: String,     // Encrypted TOTP secret
  totp_verified: Boolean,
  backup_codes: [String],  // 10 single-use codes
  backup_codes_used: [String],
  setup_at: String,
  updated_at: String
}
// Indexes: user_id (unique)
```

### user_sessions
Active login sessions.

```javascript
{
  id: String,              // Session UUID
  user_id: String,
  user_email: String,
  user_name: String,
  user_type: String,
  user_org_id: String,
  ip_address: String,
  user_agent: String,
  device_info: Object,
  login_at: String,
  last_activity: String,
  expires_at: String,
  is_active: Boolean
}
// Indexes: user_id, is_active
```

### password_policies
Organization password policies.

```javascript
{
  id: String,
  org_id: String,          // null for system-wide
  min_length: Number,
  require_uppercase: Boolean,
  require_lowercase: Boolean,
  require_numbers: Boolean,
  require_special: Boolean,
  max_age_days: Number,
  max_failed_attempts: Number,
  lockout_duration_minutes: Number,
  created_at: String,
  updated_at: String
}
// Indexes: org_id
```

### api_keys
API key management.

```javascript
{
  id: String,
  user_id: String,
  org_id: String,
  name: String,
  key_prefix: String,      // "bbk_" prefix
  key_hash: String,        // Hashed key
  scopes: [String],        // "read", "write", "admin"
  expires_at: String,
  last_used_at: String,
  is_active: Boolean,
  created_at: String
}
// Indexes: user_id, key_prefix
```

---

## Audit & Compliance

### audit_logs
Comprehensive audit trail.

```javascript
{
  id: String,
  timestamp: String,
  user_id: String,
  user_email: String,
  user_type: String,
  org_id: String,
  action: String,          // "CREATE", "UPDATE", "DELETE", "LOGIN", etc.
  module: String,          // "users", "donors", "inventory", etc.
  record_id: String,
  record_type: String,
  changes: Object,         // Before/after values
  ip_address: String,
  user_agent: String,
  notes: String
}
// Indexes: timestamp, user_id, org_id, action, module
```

### compliance_requirements
Regulatory compliance tracking.

```javascript
{
  id: String,
  name: String,
  description: String,
  category: String,
  regulatory_body: String,
  frequency: String,       // "annual", "quarterly", etc.
  is_active: Boolean,
  created_at: String
}
```

### training_courses
Staff training curriculum.

```javascript
{
  id: String,
  name: String,
  description: String,
  category: String,
  duration_hours: Number,
  is_mandatory: Boolean,
  validity_months: Number,
  passing_score: Number,
  is_active: Boolean,
  created_at: String
}
```

---

## Logistics & Inventory

### storage_locations
Blood storage facilities.

```javascript
{
  id: String,
  org_id: String,
  name: String,
  location_code: String,
  type: String,            // "refrigerator", "freezer", "room_temp"
  temperature_range: Object,
  capacity: Number,
  current_occupancy: Number,
  is_active: Boolean,
  created_at: String
}
// Indexes: org_id, location_code
```

### logistics
Transport and delivery tracking.

```javascript
{
  id: String,
  org_id: String,
  shipment_id: String,
  type: String,            // "pickup", "delivery", "transfer"
  status: String,
  origin: Object,
  destination: Object,
  items: [Object],
  courier_id: String,
  vehicle_id: String,
  scheduled_at: String,
  completed_at: String,
  temperature_log: [Object],
  created_at: String
}
// Indexes: org_id, shipment_id, status
```

---

## System Configuration

### system_settings
Global system configuration.

```javascript
{
  id: String,
  setting_key: String,
  setting_value: Mixed,
  description: String,
  updated_by: String,
  updated_at: String
}
// Indexes: setting_key (unique)
```

### session_configs
Session management configuration.

```javascript
{
  id: String,
  org_id: String,
  session_timeout_minutes: Number,
  max_concurrent_sessions: Number,
  updated_at: String
}
```

---

## Indexes Summary

For optimal performance, ensure these indexes are created:

```javascript
// Users
db.users.createIndex({ "email": 1 }, { unique: true })

// Organizations
db.organizations.createIndex({ "org_code": 1 }, { unique: true })
db.organizations.createIndex({ "parent_org_id": 1 })

// Donors
db.donors.createIndex({ "donor_code": 1 }, { unique: true })
db.donors.createIndex({ "org_id": 1 })
db.donors.createIndex({ "email": 1 })

// Blood Units
db.blood_units.createIndex({ "unit_id": 1 }, { unique: true })
db.blood_units.createIndex({ "org_id": 1, "status": 1 })
db.blood_units.createIndex({ "blood_group": 1, "status": 1 })
db.blood_units.createIndex({ "expiry_date": 1 })

// Components
db.components.createIndex({ "component_id": 1 }, { unique: true })
db.components.createIndex({ "org_id": 1, "status": 1 })

// Audit Logs
db.audit_logs.createIndex({ "timestamp": -1 })
db.audit_logs.createIndex({ "org_id": 1, "timestamp": -1 })
db.audit_logs.createIndex({ "user_id": 1, "timestamp": -1 })
```

---

**Version:** 1.0.0
**Last Updated:** January 2026
