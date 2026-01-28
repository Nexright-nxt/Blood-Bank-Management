# Blood Link - Blood Bank Management System
## Product Requirements Document

## Original Problem Statement
Build a comprehensive Blood Bank Management System with multi-tenancy support, featuring:
1. Multi-Tenancy System (Blood Bank Network) - Organizations, branches, hierarchical roles
2. Security, Audit, Compliance & Admin Enhancements - Audit logs, context switching, user management

## Application Branding
- **Name**: Blood Link (renamed from BBMS)
- **Tagline**: Blood Bank Management System

## Deployment Status
- **Last Updated**: January 24, 2026
- **Status**: PRODUCTION READY
- **Database**: Clean (no demo data)
- **Testing**: All 33 backend tests passed, all 13 frontend modules verified
- **Bugs Fixed**: 3 model bugs (missing org_id in Screening, Donation, BloodRequest models)

## Core Architecture

### Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React with Shadcn/UI components
- **Database**: MongoDB
- **Authentication**: JWT tokens with role-based access

### User Role Hierarchy (4-tier)
1. **System Admin** - Global access, manages all organizations
2. **Super Admin** - Organization-level, manages own org + child branches
3. **Tenant Admin** - Branch-level management
4. **Staff** - Standard operations within assigned branch

### Key Database Collections
- `organizations` - Organization hierarchy
- `users` - User accounts with org_id and user_type
- `audit_logs` - Comprehensive audit trail
- `user_sessions` - Session tracking for context switching
- `donors`, `donations`, `screenings`, `blood_units`, `components`, etc.

---

## What's Been Implemented

### Phase 1-4: Multi-Tenancy System (COMPLETE)
- [x] Organization CRUD operations
- [x] Parent-child organization hierarchy
- [x] Role-based access control with 4-tier hierarchy
- [x] System Admin and Super Admin login flows
- [x] Network Dashboard for system-wide overview
- [x] Inter-Organization Blood Requests module

### Phase A: Audit Logs System (COMPLETE)
- [x] Backend audit service (`/app/backend/services/audit_service.py`)
- [x] Audit log router (`/app/backend/routers/audit_logs.py`)
- [x] Authentication event logging (login, failed login)
- [x] Frontend Audit Logs page (`/app/frontend/src/pages/AuditLogs.js`)

### Phase B: Context Switching & Session Management (COMPLETE - Jan 7, 2026)
- [x] Session model (`/app/backend/models/session.py`)
- [x] Sessions router (`/app/backend/routers/sessions.py`)
  - `GET /api/sessions/context` - Get current context
  - `GET /api/sessions/switchable-contexts` - Get available orgs to switch to
  - `POST /api/sessions/switch-context` - Switch to another org
  - `POST /api/sessions/exit-context` - Return to original context
- [x] JWT tokens with impersonation flags (is_impersonating, actual_user_type)
- [x] Frontend context switching UI in Layout.js
- [x] Impersonation banner with "Exit Context" button
- [x] AuthContext.js with switchContext and exitContext functions
- [x] **RLS respects impersonation context** - When switched, user only sees target org's data
- [x] Dashboard refreshes on context switch to show filtered data

### Row-Level Security (RLS) Implementation (COMPLETE - Jan 7, 2026)
- [x] `donors.py` - Uses ReadAccess/WriteAccess middleware
- [x] `inventory.py` - Uses ReadAccess middleware
- [x] `donations.py` - Uses ReadAccess/WriteAccess middleware
- [x] `screening.py` - Uses ReadAccess/WriteAccess middleware
- [x] `blood_units.py` - Uses ReadAccess/WriteAccess middleware
- [x] `requests.py` - Uses ReadAccess/WriteAccess middleware
- [x] `storage.py` - Uses ReadAccess/WriteAccess middleware
- [x] `components.py` - Uses ReadAccess/WriteAccess middleware
- [x] `laboratory.py` - Uses ReadAccess/WriteAccess middleware
- [x] `disposition.py` (returns/discards) - Uses ReadAccess/WriteAccess middleware
- [x] `logistics.py` - Uses ReadAccess/WriteAccess middleware
- [x] `dashboard.py` - Uses ReadAccess middleware

### Phase C: Org & User Management (COMPLETE - Jan 7, 2026)
- [x] Combined creation endpoint: `POST /organizations/with-admin` - Creates org + super_admin
- [x] Combined creation endpoint: `POST /organizations/{id}/branches/with-admin` - Creates branch + tenant_admin
- [x] User management: `GET/POST/PUT/DELETE /organizations/{id}/users`
- [x] Frontend: "Add Organization + Admin" dialog with org details + admin details
- [x] Frontend: "Add Branch with Admin" button on parent orgs
- [x] Frontend: "Add User" button on each organization
- [x] Frontend: Users list in organization details dialog

### Phase D: Interactive Dashboards (COMPLETE - Jan 7, 2026)
- [x] **Main Dashboard** - All stat cards clickable with navigation to respective pages
- [x] **Network Dashboard Enhanced**:
  - [x] Quick Actions bar for System Admins (Add Org, Audit Logs, Manage Transfers)
  - [x] All 5 stat cards clickable with navigation
  - [x] Branch Overview table with clickable rows
  - [x] Inventory Distribution with clickable blood group cards
  - [x] Transfer Activity with clickable transfer rows
  - [x] Recent Activity feed showing audit log events
  - [x] Tab interface for different views (Overview, Inventory, Transfers)

### Phase E: Interactive Org & Branch Detail Pages (COMPLETE - Jan 7, 2026)
- [x] **Organization Detail Page** (`/organizations/:orgId`):
  - [x] Overview tab with org details and contact information
  - [x] Users tab with full user management (add, edit, deactivate)
  - [x] Inventory tab showing blood group distribution and stats
  - [x] Branches tab (for parent orgs) listing child branches with navigation
  - [x] Activity tab showing org-specific audit logs
  - [x] Edit organization dialog
  - [x] Add/Edit user dialogs with role and type selection
- [x] Navigation from Organizations list to detail page
- [x] Back navigation to Organizations list

### Phase F: Document Management (COMPLETE - Jan 7, 2026)
- [x] **Backend Document API** (`/app/backend/routers/documents.py`):
  - [x] `POST /api/documents/{org_id}` - Upload document with metadata
  - [x] `GET /api/documents/{org_id}` - List org documents with filters
  - [x] `GET /api/documents/{org_id}/{doc_id}` - Get single document metadata
  - [x] `GET /api/documents/{org_id}/{doc_id}/download` - Download document file
  - [x] `PUT /api/documents/{org_id}/{doc_id}/verify` - Verify document (admin only)
  - [x] `DELETE /api/documents/{org_id}/{doc_id}` - Delete document
  - [x] `GET /api/documents/{org_id}/summary/stats` - Document statistics
- [x] **Frontend Documents Tab** in OrganizationDetail page:
  - [x] Document stats cards (Total, Verified, Pending, Expiring Soon, Expired)
  - [x] Documents table with title, type, expiry, status, actions
  - [x] Upload Document dialog with full metadata fields
  - [x] Download, verify, and delete actions
  - [x] Empty state with upload prompt
- [x] File validation: extensions (.pdf, .doc, .docx, .xls, .xlsx, etc.), max 10MB
- [x] RLS enforced via OrgAccessHelper middleware

### Phase G: Compliance & Training Modules (COMPLETE - Jan 7, 2026)
- [x] **Compliance Backend API** (`/app/backend/routers/compliance.py`):
  - [x] `GET /api/compliance/requirements` - List all compliance requirements
  - [x] `POST /api/compliance/requirements` - Create requirement (system admin)
  - [x] `POST /api/compliance/seed-defaults` - Seed 6 default requirements
  - [x] `GET /api/compliance/organizations/{org_id}` - Get org compliance status
  - [x] `POST /api/compliance/organizations/{org_id}` - Update org compliance
  - [x] `POST /api/compliance/organizations/{org_id}/link-document` - Link document to compliance
  - [x] `GET /api/compliance/organizations/{org_id}/summary` - Compliance statistics
- [x] **Training Backend API** (`/app/backend/routers/training.py`):
  - [x] `GET /api/training/courses` - List all training courses
  - [x] `POST /api/training/courses` - Create course (system admin)
  - [x] `POST /api/training/seed-defaults` - Seed 8 default courses
  - [x] `GET /api/training/organizations/{org_id}/records` - Get training records
  - [x] `POST /api/training/organizations/{org_id}/assign` - Assign training to staff
  - [x] `PUT /api/training/records/{id}/start` - Start training
  - [x] `PUT /api/training/records/{id}/complete` - Complete training with score
  - [x] `GET /api/training/organizations/{org_id}/summary` - Training statistics
- [x] **Frontend Compliance Tab** in OrganizationDetail:
  - [x] Stats cards (Requirements, Compliant, Pending, Expiring Soon, Compliance Rate)
  - [x] Requirements table with status, expiry, document linking
  - [x] Mark compliant and link document actions
- [x] **Frontend Training Tab** in OrganizationDetail:
  - [x] Stats cards (Assignments, Completed, In Progress, Not Started, Completion Rate)
  - [x] Training records table with staff, course, status, progress
  - [x] Assign Training dialog with user/course selection
  - [x] Start and Complete training actions
- [x] Pre-seeded data: 6 compliance requirements, 8 training courses

---

### Phase H: Full Security Suite (COMPLETE - Jan 7, 2026)
- [x] **Password Policy** (`/app/backend/routers/security.py`):
  - [x] Configurable requirements (min length, uppercase, lowercase, numbers, special chars)
  - [x] Password expiry (max_age_days)
  - [x] Account lockout (max_failed_attempts, lockout_duration_minutes)
  - [x] Password validation API
  - [x] System-wide and org-specific policies
- [x] **Multi-Factor Authentication (MFA)**:
  - [x] TOTP setup with QR code generation (Google Authenticator/Authy compatible)
  - [x] Email OTP as backup method (MOCKED - prints to console)
  - [x] 10 backup recovery codes
  - [x] MFA enable/disable/status
  - [x] Admin can enforce MFA for users
  - [x] **MFA Enforcement at Login (COMPLETE - Jan 12, 2026)**:
    - [x] Login flow detects if user has MFA enabled
    - [x] Returns `mfa_required: true` with temporary token
    - [x] MFA verification endpoint `/api/auth/login/mfa-verify`
    - [x] Supports TOTP codes from authenticator apps
    - [x] Supports backup codes as fallback
    - [x] 5-minute expiry on MFA verification session
    - [x] Frontend MFA verification UI with OTP input
    - [x] Toggle between authenticator and backup code modes
- [x] **Session Management**:
  - [x] Active session tracking
  - [x] Revoke single session or all sessions
  - [x] Session configuration (timeout, max concurrent)
- [x] **API Key Management**:
  - [x] Create API keys with scopes (read/write/admin)
  - [x] List, revoke API keys
  - [x] Key prefix (bbk_) and secure hashing
  - [x] Expiry and usage tracking
- [x] **Frontend Security Settings Page** (`/app/frontend/src/pages/SecuritySettings.js`):
  - [x] MFA tab with setup dialog, QR code, backup codes
  - [x] Sessions tab with active session list
  - [x] Password Policy tab (admin only) with editable settings
  - [x] API Keys tab (org users) with create/revoke

### Phase I: Data Backup & Recovery (COMPLETE - Jan 9, 2026)
- [x] **Backend Backup API** (`/app/backend/routers/backups.py`):
  - [x] `POST /api/backups/create` - Create backup (role-scoped)
  - [x] `GET /api/backups/list` - List accessible backups
  - [x] `GET /api/backups/collections` - List collections for backup
  - [x] `POST /api/backups/restore` - Restore from backup
  - [x] `DELETE /api/backups/{backup_id}` - Delete backup
  - [x] `GET /api/backups/{backup_id}/preview` - Preview backup contents
  - [x] `GET /api/backups/download/{backup_id}` - Download backup as ZIP
- [x] **Role-Based Access Control**:
  - [x] System Admin: Full system-wide backups using mongodump/mongorestore
  - [x] Super Admin: Org + branches data as filtered JSON (cannot see system backups)
  - [x] Tenant Admin: Branch-only data as filtered JSON (cannot see system/org backups)
- [x] **Frontend Backup Management Page** (`/app/frontend/src/pages/BackupManagement.js`):
  - [x] Create backup with optional file inclusion
  - [x] Backup list with scope, size, creation date
  - [x] Preview backup contents before restore
  - [x] Selective restore by collections
  - [x] Download backup as ZIP
  - [x] Delete backups (own backups only for non-system admins)
- [x] Backups stored locally at `/app/backups/`
- [x] Audit logging for all backup operations

### UI/UX Fixes (COMPLETE - Jan 9, 2026)
- [x] Blood Request form dialog made scrollable (`/app/frontend/src/pages/BloodRequests.js`)
- [x] Login page organization selector upgraded to hierarchical searchable UI (`/app/frontend/src/pages/Login.js`)
- [x] Inventory Management view-switching runtime error fixed (`/app/frontend/src/pages/InventoryEnhanced.js`)
- [x] Duplicate Security Settings nav item for Tenant Admins fixed (`/app/frontend/src/components/Layout.js`)
- [x] Added stable `data-testid` attributes to Inventory view selector for test reliability

### Access Control Fixes (COMPLETE - Jan 9, 2026)
- [x] Active sessions now correctly tracked and displayed on login
- [x] Tenant Admins granted access to Audit Logs and Security Settings
- [x] System Admins granted access to Configuration module
- [x] User Management scoped by role (System sees all, Super sees org+branches, Tenant sees branch only)

### Malaysian ID Support (COMPLETE - Jan 9, 2026)
- [x] All donor forms updated to use Malaysian ID types (MyKad, MyKas, MyKid, MyPR, Passport)
- [x] Auto-formatting for MyKad (XXXXXX-XX-XXXX)
- [x] Updated validation patterns
- [x] Files: DonorRegistration.js, DonorLoginForm.js, DonorRegisterForm.js

### Code Cleanup & Deployment Preparation (COMPLETE - Jan 12, 2026)
- [x] Renamed application to "BBMS" throughout (removed all "BloodLink" references)
- [x] Removed all "emergent" references from code and UI
- [x] Updated page titles and branding
- [x] Created deployment folder with:
  - [x] README.md - Comprehensive deployment guide
  - [x] database_schema.md - MongoDB collections documentation
  - [x] init_database.py - Database initialization script
  - [x] requirements.txt - Python dependencies
  - [x] install.sh - Automated installation script
  - [x] docker-compose.yml - Docker deployment configuration
  - [x] Dockerfile.backend / Dockerfile.frontend
  - [x] mongo-init.js - MongoDB initialization
  - [x] .env.template - Environment variables template
- [x] Added /api/health endpoint for monitoring
- [x] Updated server.py with BBMS branding

### Phase J: Custom Roles & Permissions (COMPLETE - Jan 27, 2026)
- [x] **Backend Roles API** (`/app/backend/routers/roles.py`):
  - [x] `GET /api/roles` - List all roles (system + custom for user's org)
  - [x] `GET /api/roles/{id}` - Get single role with user count
  - [x] `GET /api/roles/available-modules` - Get all modules and actions for role builder
  - [x] `GET /api/roles/my-permissions` - Get current user's permissions
  - [x] `POST /api/roles` - Create custom role with granular permissions
  - [x] `PUT /api/roles/{id}` - Update custom role (blocked for system roles)
  - [x] `DELETE /api/roles/{id}` - Delete custom role (blocked if users assigned)
  - [x] `POST /api/roles/{id}/duplicate` - Duplicate any role as custom
- [x] **Permission Middleware** (`/app/backend/middleware/permissions.py`):
  - [x] `check_permission(user, module, action)` - Check if user has permission
  - [x] `require_permission(module, action)` - FastAPI dependency for route protection
  - [x] `require_any_permission(module, actions)` - Check any of multiple actions
  - [x] `require_module_access(module)` - Check any access to a module
  - [x] `get_user_permissions(user)` - Get full permission object for user
- [x] **Permission Enforcement Applied to Routes:**
  - [x] `/api/donors` - donors.view, donors.create, donors.edit
  - [x] `/api/donations` - donations.view, donations.create, donations.edit
  - [x] `/api/screenings` - screening.view, screening.create
  - [x] `/api/lab-tests` - laboratory.view, laboratory.create
  - [x] `/api/components` - processing.view, processing.create, processing.edit
  - [x] `/api/qc-validation` - qc_validation.view, qc_validation.create, qc_validation.approve
  - [x] `/api/inventory` - inventory.view
  - [x] `/api/blood-units` - inventory.view, inventory.move
  - [x] `/api/requests` - requests.view, requests.create, requests.approve, requests.reject, requests.fulfill
  - [x] `/api/logistics/shipments` - logistics.view, logistics.create, logistics.edit, logistics.dispatch, logistics.deliver
- [x] **Frontend Roles Management** (`/app/frontend/src/pages/RolesManagement.js`):
  - [x] System Roles section (read-only, 8 seeded roles)
  - [x] Custom Roles section with full CRUD
  - [x] Create Role dialog with expandable permission checkboxes
  - [x] Edit/View/Duplicate/Delete actions
  - [x] User count per role
- [x] **User Management Custom Role Assignment** (`/app/frontend/src/pages/UserManagement.js`):
  - [x] Custom Role column in Staff Users table
  - [x] Custom Role dropdown in Add/Edit User dialog
  - [x] Shows "System Default" for users without custom role
- [x] **Auth Context Permission Helpers** (`/app/frontend/src/context/AuthContext.js`):
  - [x] `hasPermission(module, action)` - Check specific permission
  - [x] `canAccessModule(module)` - Check any access to module
  - [x] `userPermissions` state - Full permissions object
  - [x] `refreshPermissions()` - Reload permissions after role change
- [x] **Navigation Updates** (`/app/frontend/src/components/Layout.js`):
  - [x] Roles & Permissions link in sidebar for super_admin and tenant_admin
- [x] **API Helper** (`/app/frontend/src/lib/api.js`):
  - [x] `rolesAPI` with all CRUD operations

---

## Prioritized Backlog

### P0 (Critical - Next)
- All P0 tasks complete!

### P1 (High Priority)
- [x] **Requestor User Role** - Public registration, admin approval workflow, limited dashboard (COMPLETE)

### P2 (Medium Priority)
- [x] **Blood Link (Nearby Availability)** - Geolocation to find nearby blood banks with stock (COMPLETE)

### P3 (Future)
- [ ] API Rate Limiting (deferred by user)
- [ ] Logistics Module Notifications
- [ ] Email Service Integration (Email OTP is MOCKED - prints to console)
- [ ] Enterprise Backup & Recovery Upgrade (deferred by user)

---

### Phase K: Requestor User Role (COMPLETE - Jan 27, 2026)
- [x] **Backend Requestor API** (`/app/backend/routers/requestors.py`):
  - [x] `POST /api/requestors/register` - Public registration (no auth required)
  - [x] `GET /api/requestors/check-status/{email}` - Public status check
  - [x] `GET /api/requestors` - List all requestors (admin)
  - [x] `GET /api/requestors/stats` - Statistics (admin)
  - [x] `GET /api/requestors/pending` - Pending approvals (admin)
  - [x] `GET /api/requestors/{id}` - Get single requestor (admin)
  - [x] `PUT /api/requestors/{id}/approve` - Approve/Reject (admin)
  - [x] `PUT /api/requestors/{id}/suspend` - Suspend approved requestor (admin)
  - [x] `PUT /api/requestors/{id}/reactivate` - Reactivate suspended (admin)
  - [x] `GET /api/requestors/me/profile` - Requestor self-service
  - [x] `PUT /api/requestors/me/profile` - Requestor profile update
- [x] **Requestor Model** (`/app/backend/models/requestor.py`):
  - [x] RequestorStatus enum (pending, approved, rejected, suspended)
  - [x] RequestorType enum (hospital, clinic, emergency_service, research_lab, other)
  - [x] Requestor, RequestorRegistration, RequestorUpdate, RequestorApproval models
- [x] **Frontend Public Registration** (`/app/frontend/src/pages/RequestorRegistration.js`):
  - [x] 3-step registration form (Organization Info, Account Details, Address)
  - [x] Form validation at each step
  - [x] Success confirmation with status check link
- [x] **Frontend Admin Management** (`/app/frontend/src/pages/RequestorManagement.js`):
  - [x] Stats cards (pending, approved, rejected, total)
  - [x] Pending approval alert
  - [x] Search and filter (by status, type)
  - [x] Table with approve/reject/suspend/reactivate actions
  - [x] Detail dialog with full requestor info
  - [x] Approval dialog with org selection
  - [x] Rejection dialog with reason input
- [x] **Frontend Requestor Dashboard** (`/app/frontend/src/pages/RequestorDashboard.js`):
  - [x] Stats cards (pending, approved, fulfilled requests)
  - [x] Blood availability view by blood group
  - [x] My Requests list with status tracking
  - [x] New Request dialog with patient info form
  - [x] Organization profile tab
- [x] **Navigation Updates** (`/app/frontend/src/components/Layout.js`):
  - [x] "Requestors" link in sidebar for admins
  - [x] Requestor user type redirects to requestor dashboard
- [x] **Routes** (`/app/frontend/src/App.js`):
  - [x] `/requestor/register` - Public registration page
  - [x] `/requestor-dashboard` - Approved requestor dashboard
  - [x] `/requestor-management` - Admin management page

---

### Phase L: Blood Link - Nearby Availability (COMPLETE - Jan 28, 2026)
- [x] **Backend Blood Link API** (`/app/backend/routers/blood_link.py`):
  - [x] `POST /api/blood-link/search` - Public geolocation search for nearby blood banks
  - [x] `GET /api/blood-link/availability/{org_id}` - Detailed availability for specific blood bank
  - [x] `GET /api/blood-link/blood-groups` - Network-wide blood group availability summary
  - [x] `GET /api/blood-link/emergency-contacts` - 24x7 blood bank contact list
  - [x] `GET /api/blood-link/my-org/settings` - Get org's Blood Link settings (authenticated)
  - [x] `PUT /api/blood-link/my-org/settings` - Update org's Blood Link settings (admin)
- [x] **Geolocation Features:**
  - [x] Haversine formula distance calculation (accurate great-circle distance)
  - [x] Filter by blood group, component type, max radius, min units
  - [x] Results sorted by distance (nearest first)
  - [x] Organization latitude/longitude fields in organizations collection
- [x] **Frontend Blood Link Search** (`/app/frontend/src/pages/BloodLinkSearch.js`):
  - [x] Public accessible at `/blood-link` (no auth required)
  - [x] Latitude/Longitude inputs with auto-detect geolocation button
  - [x] Blood Group dropdown filter (Any, A+, A-, B+, B-, AB+, AB-, O+, O-)
  - [x] Component Type dropdown filter (All, Whole Blood, PRC, FFP, Platelets, Cryoprecipitate)
  - [x] Search Radius dropdown (10km, 25km, 50km, 100km, 200km)
  - [x] Search results with blood bank cards showing:
    - Organization name, address, city, state
    - Distance from user location
    - Total units available with availability badge (No Stock/Low Stock/Available)
    - Operating hours and 24x7 badge
    - Blood group availability breakdown
  - [x] Blood bank detail modal with:
    - Full contact info (phone, email, address)
    - Complete availability breakdown by blood group and component
    - Get Directions button (opens Google Maps)
    - Call Now button
  - [x] Empty state handling with helpful message
  - [x] Emergency info card with guidance
- [x] **Navigation Updates** (`/app/frontend/src/components/Layout.js`):
  - [x] "Blood Link" public link in sidebar (visible to all users)

---

### Phase M: Share Availability - Network Broadcasts (COMPLETE - Jan 28, 2026)
- [x] **Backend Broadcasts API** (`/app/backend/routers/broadcasts.py`):
  - [x] `GET /api/broadcasts/active` - Public endpoint to get active broadcasts
  - [x] `GET /api/broadcasts/stats` - Public network-wide broadcast statistics
  - [x] `POST /api/broadcasts` - Create new broadcast (any authenticated staff)
  - [x] `GET /api/broadcasts/my-broadcasts` - Get org's broadcasts
  - [x] `GET /api/broadcasts/{id}` - Get broadcast details with responses
  - [x] `POST /api/broadcasts/{id}/respond` - Respond to a broadcast (different org only)
  - [x] `PUT /api/broadcasts/{id}/close` - Close/mark fulfilled (creator or admin)
  - [x] `DELETE /api/broadcasts/{id}` - Delete broadcast (creator or admin)
  - [x] `GET /api/broadcasts/{id}/responses` - Get all responses to a broadcast
- [x] **Broadcast Model** (`/app/backend/models/broadcast.py`):
  - [x] BroadcastType enum: urgent_need, surplus_alert
  - [x] BroadcastStatus enum: active, responded, fulfilled, expired, closed
  - [x] BroadcastVisibility enum: network_wide, nearby_only
  - [x] Priority levels: normal, high, critical
  - [x] Auto-expiry after 48 hours
  - [x] Response count tracking
- [x] **Frontend Blood Link Integration** (`/app/frontend/src/pages/BloodLinkSearch.js`):
  - [x] Network Alerts section showing active broadcasts
  - [x] Broadcast cards with type icon (urgent/surplus)
  - [x] Priority badges (Critical, High, Normal)
  - [x] Blood group and type badges
  - [x] Click to view broadcast details in modal
- [x] **Frontend Broadcasts Management** (`/app/frontend/src/pages/BroadcastsManagement.js`):
  - [x] Stats cards: Urgent Needs, Surplus Alerts, Fulfilled, Total Responses
  - [x] Network Alerts tab (broadcasts from all orgs)
  - [x] My Broadcasts tab (org's own broadcasts)
  - [x] Create Broadcast dialog with:
    - Type selection (Urgent Need / Surplus Alert)
    - Blood group, component type, units fields
    - Priority, description, contact info
    - Visibility (network-wide / nearby only)
  - [x] Respond to broadcast dialog
  - [x] Mark Fulfilled and Delete actions for own broadcasts
- [x] **Navigation Updates** (`/app/frontend/src/components/Layout.js`):
  - [x] "Network Broadcasts" link in sidebar for all staff roles

### Phase M.1: In-App Notifications for Critical Broadcasts (COMPLETE - Jan 28, 2026)
- [x] **Notification Listener** (`/app/frontend/src/components/BroadcastNotificationListener.js`):
  - [x] Polling architecture (30 second intervals)
  - [x] Initial 3 second delay to let app settle
  - [x] Tracks "seen" broadcasts to avoid duplicate notifications
  - [x] Filters for critical and high priority broadcasts only
  - [x] Excludes same-org broadcasts (users don't need notifications for their own)
- [x] **Toast Notifications** (using sonner):
  - [x] Critical priority: Red background (#fef2f2), 15 second duration, 🚨 emoji
  - [x] High priority: Amber background (#fffbeb), 10 second duration, ⚠️ emoji
  - [x] Shows blood group, organization name, and broadcast title
  - [x] "View" button navigates to /broadcasts page
- [x] **Integration**:
  - [x] BroadcastNotificationListener rendered in Layout.js for all logged-in users
  - [x] Works with existing auth context for org_id filtering

---

### Phase N: Map Integration for Requestors (COMPLETE - Jan 28, 2026)
- [x] **Map Components** (OpenStreetMap + Leaflet):
  - [x] `MapPicker.jsx` - Reusable map picker with location selection
    - Click to select location, draggable marker
    - Address search using Nominatim (free geocoding)
    - Current location detection (geolocation API)
    - Reverse geocoding to show address
  - [x] `BloodBankMap.jsx` - Interactive blood bank map display
    - Custom colored markers: green (24/7 with stock), blue (has stock), gray (no stock)
    - User location marker (blue dot)
    - Blood group filter dropdown
    - My Location button, Refresh button
    - Click marker for popup with details
    - Get Directions button (opens Google Maps)
    - Map legend
- [x] **Blood Link Page Updates** (`/app/frontend/src/pages/BloodLinkSearch.js`):
  - [x] List View / Map View toggle buttons
  - [x] Map View shows BloodBankMap component
  - [x] Blood banks displayed as interactive markers
- [x] **Requestor Registration** (`/app/frontend/src/pages/RequestorRegistration.js`):
  - [x] Step 3 renamed to "Location & Documents"
  - [x] MapPicker for location selection (required field)
  - [x] Address search functionality
  - [x] Current location detection
  - [x] Latitude/longitude stored with requestor profile
- [x] **Requestor Dashboard** (`/app/frontend/src/pages/RequestorDashboard.js`):
  - [x] "Find Blood Banks" button opens map dialog
  - [x] Map dialog shows nearby blood banks on map
  - [x] New Blood Request form has location section:
    - Delivery / Self Pickup toggle
    - "Use Registered Location" button for delivery
    - MapPicker for custom delivery location
    - Address input field
- [x] **Backend Updates**:
  - [x] `Requestor` model updated with latitude/longitude fields
  - [x] `RequestorRegistration` model accepts lat/lng

---

### Phase O: Requestor Portal Improvements (COMPLETE - Jan 28, 2026)
- [x] **Routing Fixes** (`/app/frontend/src/App.js`):
  - [x] Requestors now redirect to `/requestor-dashboard` on login (not `/dashboard`)
  - [x] Index route also handles requestor redirect correctly
- [x] **Backend API Enhancements** (`/app/backend/routers/requestors.py`):
  - [x] `GET /api/requestors/me/profile` - Requestor self-service profile endpoint
  - [x] `GET /api/requestors/me/requests` - Get requestor's own blood requests
  - [x] `POST /api/requestors/me/requests` - Create blood request as requestor
  - [x] All endpoints validate `user_type === 'requestor'`
- [x] **RequestorDashboard Improvements** (`/app/frontend/src/pages/RequestorDashboard.js`):
  - [x] Uses requestor-specific API endpoints
  - [x] Stats cards: Pending, Approved, Fulfilled, Total Requests
  - [x] My Requests tab with status badges and request details
  - [x] Blood Availability tab showing public blood stock (fixed NaN bug)
  - [x] My Profile tab showing organization details
  - [x] New Request dialog with all fields including delivery/pickup location
  - [x] Find Blood Banks button opening map dialog
- [x] **Navigation Updates** (`/app/frontend/src/components/Layout.js`):
  - [x] Requestor sidebar shows: Dashboard, Find Blood, Network Alerts
- [x] **Enum Updates** (`/app/backend/models/enums.py`):
  - [x] Added `REQUESTOR` to UserType enum
  - [x] Added `REQUESTOR` to UserRole enum

---

### Phase P: Inter-Organization Blood Requests & Location Features (COMPLETE - Jan 28, 2026)
- [x] **New Role: Blood Request Staff** (`blood_request_staff`):
  - [x] Permissions: requests, returns, discard, inventory, blood_link, donors, collection
  - [x] Added to UserRole enum
  - [x] Created system role in database
- [x] **Find Blood Page** (`/app/frontend/src/pages/FindBlood.js`):
  - [x] Route at `/find-blood` for admin, inventory, distribution, blood_request_staff roles
  - [x] Internal Inventory tab showing org's blood stock by blood group
  - [x] External Blood Banks tab with search controls (blood group, max distance, list/map toggle)
  - [x] New Request button with Internal/External toggle
  - [x] Internal request: from own inventory
  - [x] External request: shows target blood bank info and delivery location map
  - [x] MapPicker for delivery location selection
  - [x] **"View My Requests" button** - Navigates to Blood Requests page
  - [x] **Unified data flow** - Requests created here now use `/api/inter-org-requests` endpoint
- [x] **Backend API Updates**:
  - [x] `GET /api/organizations/current` - Get current user's organization with location
  - [x] Blood request creation works with correct payload mapping
- [x] **Donor Registration Location** (`/app/frontend/src/pages/DonorRegistration.js`):
  - [x] MapPicker added to Step 2 (Contact Information)
  - [x] Location is mandatory for registration
  - [x] City, State, Pincode fields added
  - [x] Donor model updated with latitude/longitude fields
- [x] **Organization Registration Location** (`/app/frontend/src/pages/Organizations.js`):
  - [x] MapPicker added to Create Organization with Admin dialog
  - [x] Latitude/longitude stored with organization
- [x] **Navigation Updates** (`/app/frontend/src/components/Layout.js`):
  - [x] "Find Blood" link added to sidebar for appropriate roles
  - [x] blood_request_staff role added to all relevant menu items
---

## Deployment

### Deployment Files Location
`/app/deployment/`

### Quick Start (Development)
```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn server:app --port 8001

# Frontend
cd frontend && yarn install && yarn start
```

### Production Deployment Options
1. **Bare Metal/VM**: Use `install.sh` script
2. **Docker**: Use `docker-compose.yml`

### Initial Admin Credentials (after fresh deployment)
- Email: `admin@bbms.local`
- Password: `Admin@123456`
- ⚠️ Change immediately after first login!

---

## Test Credentials (Development)

| User | Email | Password | Type | Notes |
|------|-------|----------|------|-------|
| System Admin | admin@bloodbank.com | adminpassword | system_admin | Select "No organization" |
| Super Admin | superadmin@bloodlink.com | superadmin123 | super_admin | BloodLink Central |
| Tenant Admin | admin@northbranch.com | northadmin123 | tenant_admin | North Branch Updated |

---

## Key Files Reference

### Backend
- `/app/backend/middleware/org_access.py` - RLS middleware
- `/app/backend/middleware/permissions.py` - Custom Roles permission checking middleware
- `/app/backend/services/audit_service.py` - Audit logging service
- `/app/backend/routers/sessions.py` - Context switching API
- `/app/backend/routers/documents.py` - Document management API
- `/app/backend/routers/compliance.py` - Compliance management API
- `/app/backend/routers/training.py` - Training management API
- `/app/backend/routers/security.py` - Security Suite API (MFA, Password Policy, Sessions, API Keys)
- `/app/backend/routers/backups.py` - Data Backup & Recovery API
- `/app/backend/routers/users.py` - User management with role-based scoping
- `/app/backend/routers/roles.py` - Custom Roles & Permissions CRUD API
- `/app/backend/routers/auth.py` - Auth with session creation on login
- `/app/backend/models/security.py` - Security models
- `/app/backend/models/role.py` - Role model with AVAILABLE_MODULES and SYSTEM_ROLES
- `/app/backend/services/helpers.py` - JWT token creation with impersonation

### Frontend
- `/app/frontend/src/context/AuthContext.js` - Auth state + context switching + permission helpers
- `/app/frontend/src/components/Layout.js` - Header with context switcher + roles nav
- `/app/frontend/src/pages/AuditLogs.js` - Audit trail viewer
- `/app/frontend/src/pages/OrganizationDetail.js` - Org detail with Documents, Compliance, Training tabs
- `/app/frontend/src/pages/SecuritySettings.js` - Security Settings page (MFA, Sessions, Password Policy, API Keys)
- `/app/frontend/src/pages/BackupManagement.js` - Data Backup & Recovery page
- `/app/frontend/src/pages/InventoryEnhanced.js` - Inventory with stable test IDs
- `/app/frontend/src/pages/UserManagement.js` - Role-scoped user management + custom role assignment
- `/app/frontend/src/pages/RolesManagement.js` - Custom Roles & Permissions management UI
- `/app/frontend/src/pages/Login.js` - Hierarchical org selector
- `/app/frontend/src/lib/api.js` - API helpers including rolesAPI

---

## Latest Test Reports
- `/app/test_reports/iteration_5.json` - Phase B testing (100% pass rate)
- `/app/test_reports/iteration_6.json` - Phase F Document Management (100% pass rate, 13 tests)
- `/app/test_reports/iteration_7.json` - Phase G Compliance & Training (100% pass rate, 18 tests)
- `/app/test_reports/iteration_8.json` - Phase H Security Suite (100% pass rate, 25 tests)
- `/app/test_reports/iteration_2.json` - Phase J Custom Roles & Permissions (100% pass rate, 18 tests)
- `/app/test_reports/iteration_3.json` - Phase J Permission Enforcement (100% pass rate, 35 tests)
- `/app/test_reports/iteration_4.json` - Phase K Requestor User Role (100% pass rate, 23 tests)
- `/app/tests/test_phase_f_documents.py` - Document management API tests
- `/app/tests/test_phase_g_compliance_training.py` - Compliance & Training API tests
- `/app/tests/test_phase_h_security.py` - Security Suite API tests
- `/app/backend/tests/test_roles_permissions.py` - Roles & Permissions API tests
- `/app/backend/tests/test_permission_enforcement.py` - Permission enforcement tests
- `/app/backend/tests/test_requestors.py` - Requestor feature tests
- `/app/backend/tests/test_blood_link_search.py` - Blood Link feature tests
- `/app/test_reports/iteration_5.json` - Blood Link feature (100% pass rate, 17 backend tests)
- `/app/backend/tests/test_broadcasts.py` - Network Broadcasts feature tests
- `/app/test_reports/iteration_6.json` - Network Broadcasts feature (100% pass rate, 18 backend tests)
- `/app/test_reports/iteration_7.json` - In-App Notifications for Broadcasts (100% pass rate, 9 frontend tests)
- `/app/test_reports/iteration_8.json` - Map Integration for Requestors (100% pass rate, 10 frontend tests)
- `/app/test_reports/iteration_9.json` - Requestor Portal Improvements (100% pass rate, 13 backend + all frontend tests)
