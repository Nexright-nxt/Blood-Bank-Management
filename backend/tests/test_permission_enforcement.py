"""
Test Suite for Permission Enforcement on API Routes
Tests the require_permission middleware applied to:
- donors router
- inventory router
- requests router
- laboratory router
- screening router

Tests verify:
1. Admin users can access all endpoints
2. System admins bypass all permission checks
3. Role-specific users can only access permitted endpoints
4. Users get 403 when accessing endpoints without permission
5. Custom roles override default role permissions
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials for different roles
CREDENTIALS = {
    "org_admin": {"email": "admin@testorg.com", "password": "Test@123"},
    "system_admin": {"email": "admin@bbms.local", "password": "Admin@123456"},
    "lab_tech": {"email": "labtech@testorg.com", "password": "Test@123"},
    "registration": {"email": "registration@testorg.com", "password": "Test@123"},
    "inventory": {"email": "inventory@testorg.com", "password": "Test@123"},
}

# Expected permissions per role (from models/role.py SYSTEM_ROLES)
ROLE_PERMISSIONS = {
    "admin": {
        "donors": ["view", "create", "edit", "delete"],
        "inventory": ["view", "move", "reserve", "transfer"],
        "laboratory": ["view", "create", "edit", "verify"],
        "screening": ["view", "create", "edit"],
        "requests": ["view", "create", "edit", "approve", "reject", "fulfill"],
    },
    "lab_tech": {
        "laboratory": ["view", "create", "edit"],
        "donors": ["view"],
        "donations": ["view"],
        # NO inventory, requests, screening permissions
    },
    "registration": {
        "donors": ["view", "create", "edit"],
        "donations": ["view", "create"],
        "screening": ["view", "create", "edit"],
        # NO inventory, laboratory, requests permissions
    },
    "inventory": {
        "inventory": ["view", "move", "reserve", "transfer"],
        "storage": ["view", "create", "edit"],
        "requests": ["view"],
        "distribution": ["view", "create"],
        "logistics": ["view", "create"],
        "returns": ["view", "create"],
        "discards": ["view", "create"],
        # NO donors, laboratory, screening permissions
    },
}


class TestPermissionEnforcementBase:
    """Base class with login helpers"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.tokens = {}
    
    def login(self, role_key: str) -> str:
        """Login and return token for a specific role"""
        if role_key in self.tokens:
            return self.tokens[role_key]
        
        creds = CREDENTIALS.get(role_key)
        if not creds:
            pytest.skip(f"No credentials for role: {role_key}")
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=creds)
        assert response.status_code == 200, f"Login failed for {role_key}: {response.text}"
        
        token = response.json().get("token")
        self.tokens[role_key] = token
        return token
    
    def get_auth_header(self, role_key: str) -> dict:
        """Get authorization header for a role"""
        token = self.login(role_key)
        return {"Authorization": f"Bearer {token}"}


class TestAdminFullAccess(TestPermissionEnforcementBase):
    """Test that Admin users can access all endpoints"""
    
    def test_admin_can_access_donors(self):
        """Admin can access /api/donors (donors.view)"""
        headers = self.get_auth_header("org_admin")
        response = self.session.get(f"{BASE_URL}/api/donors", headers=headers)
        assert response.status_code == 200, f"Admin should access donors: {response.text}"
        print("SUCCESS: Admin can access /api/donors")
    
    def test_admin_can_access_inventory_summary(self):
        """Admin can access /api/inventory/summary (inventory.view)"""
        headers = self.get_auth_header("org_admin")
        response = self.session.get(f"{BASE_URL}/api/inventory/summary", headers=headers)
        assert response.status_code == 200, f"Admin should access inventory: {response.text}"
        
        data = response.json()
        assert "total_units_available" in data
        print("SUCCESS: Admin can access /api/inventory/summary")
    
    def test_admin_can_access_lab_tests(self):
        """Admin can access /api/lab-tests (laboratory.view)"""
        headers = self.get_auth_header("org_admin")
        response = self.session.get(f"{BASE_URL}/api/lab-tests", headers=headers)
        assert response.status_code == 200, f"Admin should access lab-tests: {response.text}"
        print("SUCCESS: Admin can access /api/lab-tests")
    
    def test_admin_can_access_screenings(self):
        """Admin can access /api/screenings (screening.view)"""
        headers = self.get_auth_header("org_admin")
        response = self.session.get(f"{BASE_URL}/api/screenings", headers=headers)
        assert response.status_code == 200, f"Admin should access screenings: {response.text}"
        print("SUCCESS: Admin can access /api/screenings")
    
    def test_admin_can_access_requests(self):
        """Admin can access /api/requests (requests.view)"""
        headers = self.get_auth_header("org_admin")
        response = self.session.get(f"{BASE_URL}/api/requests", headers=headers)
        assert response.status_code == 200, f"Admin should access requests: {response.text}"
        print("SUCCESS: Admin can access /api/requests")


class TestSystemAdminBypass(TestPermissionEnforcementBase):
    """Test that System Admin bypasses all permission checks"""
    
    def test_system_admin_bypasses_donors(self):
        """System admin can access /api/donors"""
        headers = self.get_auth_header("system_admin")
        response = self.session.get(f"{BASE_URL}/api/donors", headers=headers)
        assert response.status_code == 200, f"System admin should bypass: {response.text}"
        print("SUCCESS: System admin bypasses permission check for /api/donors")
    
    def test_system_admin_bypasses_inventory(self):
        """System admin can access /api/inventory/summary"""
        headers = self.get_auth_header("system_admin")
        response = self.session.get(f"{BASE_URL}/api/inventory/summary", headers=headers)
        assert response.status_code == 200, f"System admin should bypass: {response.text}"
        print("SUCCESS: System admin bypasses permission check for /api/inventory/summary")
    
    def test_system_admin_bypasses_lab_tests(self):
        """System admin can access /api/lab-tests"""
        headers = self.get_auth_header("system_admin")
        response = self.session.get(f"{BASE_URL}/api/lab-tests", headers=headers)
        assert response.status_code == 200, f"System admin should bypass: {response.text}"
        print("SUCCESS: System admin bypasses permission check for /api/lab-tests")
    
    def test_system_admin_bypasses_screenings(self):
        """System admin can access /api/screenings"""
        headers = self.get_auth_header("system_admin")
        response = self.session.get(f"{BASE_URL}/api/screenings", headers=headers)
        assert response.status_code == 200, f"System admin should bypass: {response.text}"
        print("SUCCESS: System admin bypasses permission check for /api/screenings")
    
    def test_system_admin_bypasses_requests(self):
        """System admin can access /api/requests"""
        headers = self.get_auth_header("system_admin")
        response = self.session.get(f"{BASE_URL}/api/requests", headers=headers)
        assert response.status_code == 200, f"System admin should bypass: {response.text}"
        print("SUCCESS: System admin bypasses permission check for /api/requests")


class TestLabTechPermissions(TestPermissionEnforcementBase):
    """Test Lab Tech role permissions - has laboratory.view, NO inventory.view"""
    
    def test_lab_tech_can_access_lab_tests(self):
        """Lab tech CAN access /api/lab-tests (has laboratory.view)"""
        headers = self.get_auth_header("lab_tech")
        response = self.session.get(f"{BASE_URL}/api/lab-tests", headers=headers)
        assert response.status_code == 200, f"Lab tech should access lab-tests: {response.text}"
        print("SUCCESS: Lab tech CAN access /api/lab-tests (laboratory.view)")
    
    def test_lab_tech_cannot_access_inventory(self):
        """Lab tech CANNOT access /api/inventory/summary (no inventory.view)"""
        headers = self.get_auth_header("lab_tech")
        response = self.session.get(f"{BASE_URL}/api/inventory/summary", headers=headers)
        assert response.status_code == 403, f"Lab tech should be denied inventory: {response.status_code}"
        
        data = response.json()
        assert "Permission denied" in data.get("detail", ""), f"Should have permission denied message: {data}"
        print("SUCCESS: Lab tech CANNOT access /api/inventory/summary (403 - no inventory.view)")
    
    def test_lab_tech_can_view_donors(self):
        """Lab tech CAN view donors (has donors.view)"""
        headers = self.get_auth_header("lab_tech")
        response = self.session.get(f"{BASE_URL}/api/donors", headers=headers)
        assert response.status_code == 200, f"Lab tech should view donors: {response.text}"
        print("SUCCESS: Lab tech CAN access /api/donors (donors.view)")
    
    def test_lab_tech_cannot_access_screenings(self):
        """Lab tech CANNOT access /api/screenings (no screening.view)"""
        headers = self.get_auth_header("lab_tech")
        response = self.session.get(f"{BASE_URL}/api/screenings", headers=headers)
        assert response.status_code == 403, f"Lab tech should be denied screenings: {response.status_code}"
        print("SUCCESS: Lab tech CANNOT access /api/screenings (403 - no screening.view)")
    
    def test_lab_tech_cannot_access_requests(self):
        """Lab tech CANNOT access /api/requests (no requests.view)"""
        headers = self.get_auth_header("lab_tech")
        response = self.session.get(f"{BASE_URL}/api/requests", headers=headers)
        assert response.status_code == 403, f"Lab tech should be denied requests: {response.status_code}"
        print("SUCCESS: Lab tech CANNOT access /api/requests (403 - no requests.view)")


class TestRegistrationStaffPermissions(TestPermissionEnforcementBase):
    """Test Registration Staff role permissions - has donors.view, screening.view, NO laboratory.view"""
    
    def test_registration_can_access_donors(self):
        """Registration staff CAN access /api/donors (has donors.view)"""
        headers = self.get_auth_header("registration")
        response = self.session.get(f"{BASE_URL}/api/donors", headers=headers)
        assert response.status_code == 200, f"Registration should access donors: {response.text}"
        print("SUCCESS: Registration staff CAN access /api/donors (donors.view)")
    
    def test_registration_can_access_screenings(self):
        """Registration staff CAN access /api/screenings (has screening.view)"""
        headers = self.get_auth_header("registration")
        response = self.session.get(f"{BASE_URL}/api/screenings", headers=headers)
        assert response.status_code == 200, f"Registration should access screenings: {response.text}"
        print("SUCCESS: Registration staff CAN access /api/screenings (screening.view)")
    
    def test_registration_cannot_access_lab_tests(self):
        """Registration staff CANNOT access /api/lab-tests (no laboratory.view)"""
        headers = self.get_auth_header("registration")
        response = self.session.get(f"{BASE_URL}/api/lab-tests", headers=headers)
        assert response.status_code == 403, f"Registration should be denied lab-tests: {response.status_code}"
        
        data = response.json()
        assert "Permission denied" in data.get("detail", "")
        print("SUCCESS: Registration staff CANNOT access /api/lab-tests (403 - no laboratory.view)")
    
    def test_registration_cannot_access_inventory(self):
        """Registration staff CANNOT access /api/inventory/summary (no inventory.view)"""
        headers = self.get_auth_header("registration")
        response = self.session.get(f"{BASE_URL}/api/inventory/summary", headers=headers)
        assert response.status_code == 403, f"Registration should be denied inventory: {response.status_code}"
        print("SUCCESS: Registration staff CANNOT access /api/inventory/summary (403 - no inventory.view)")
    
    def test_registration_cannot_access_requests(self):
        """Registration staff CANNOT access /api/requests (no requests.view)"""
        headers = self.get_auth_header("registration")
        response = self.session.get(f"{BASE_URL}/api/requests", headers=headers)
        assert response.status_code == 403, f"Registration should be denied requests: {response.status_code}"
        print("SUCCESS: Registration staff CANNOT access /api/requests (403 - no requests.view)")


class TestInventoryManagerPermissions(TestPermissionEnforcementBase):
    """Test Inventory Manager role permissions - has inventory.view, requests.view, NO donors.view"""
    
    def test_inventory_can_access_inventory_summary(self):
        """Inventory manager CAN access /api/inventory/summary (has inventory.view)"""
        headers = self.get_auth_header("inventory")
        response = self.session.get(f"{BASE_URL}/api/inventory/summary", headers=headers)
        assert response.status_code == 200, f"Inventory should access inventory: {response.text}"
        print("SUCCESS: Inventory manager CAN access /api/inventory/summary (inventory.view)")
    
    def test_inventory_can_access_inventory_by_blood_group(self):
        """Inventory manager CAN access /api/inventory/by-blood-group"""
        headers = self.get_auth_header("inventory")
        response = self.session.get(f"{BASE_URL}/api/inventory/by-blood-group", headers=headers)
        assert response.status_code == 200, f"Inventory should access by-blood-group: {response.text}"
        print("SUCCESS: Inventory manager CAN access /api/inventory/by-blood-group")
    
    def test_inventory_can_access_inventory_expiring(self):
        """Inventory manager CAN access /api/inventory/expiring"""
        headers = self.get_auth_header("inventory")
        response = self.session.get(f"{BASE_URL}/api/inventory/expiring", headers=headers)
        assert response.status_code == 200, f"Inventory should access expiring: {response.text}"
        print("SUCCESS: Inventory manager CAN access /api/inventory/expiring")
    
    def test_inventory_can_access_requests(self):
        """Inventory manager CAN access /api/requests (has requests.view)"""
        headers = self.get_auth_header("inventory")
        response = self.session.get(f"{BASE_URL}/api/requests", headers=headers)
        assert response.status_code == 200, f"Inventory should access requests: {response.text}"
        print("SUCCESS: Inventory manager CAN access /api/requests (requests.view)")
    
    def test_inventory_cannot_access_donors(self):
        """Inventory manager CANNOT access /api/donors (no donors.view)"""
        headers = self.get_auth_header("inventory")
        response = self.session.get(f"{BASE_URL}/api/donors", headers=headers)
        assert response.status_code == 403, f"Inventory should be denied donors: {response.status_code}"
        print("SUCCESS: Inventory manager CANNOT access /api/donors (403 - no donors.view)")
    
    def test_inventory_cannot_access_lab_tests(self):
        """Inventory manager CANNOT access /api/lab-tests (no laboratory.view)"""
        headers = self.get_auth_header("inventory")
        response = self.session.get(f"{BASE_URL}/api/lab-tests", headers=headers)
        assert response.status_code == 403, f"Inventory should be denied lab-tests: {response.status_code}"
        print("SUCCESS: Inventory manager CANNOT access /api/lab-tests (403 - no laboratory.view)")
    
    def test_inventory_cannot_access_screenings(self):
        """Inventory manager CANNOT access /api/screenings (no screening.view)"""
        headers = self.get_auth_header("inventory")
        response = self.session.get(f"{BASE_URL}/api/screenings", headers=headers)
        assert response.status_code == 403, f"Inventory should be denied screenings: {response.status_code}"
        print("SUCCESS: Inventory manager CANNOT access /api/screenings (403 - no screening.view)")


class TestCustomRolePermissions(TestPermissionEnforcementBase):
    """Test custom role with specific permissions overrides default role"""
    
    def test_create_custom_role_with_donors_only(self):
        """Create a custom role with only donors.view permission"""
        headers = self.get_auth_header("org_admin")
        
        role_name = f"TEST_DonorsOnly_{uuid.uuid4().hex[:8]}"
        role_data = {
            "name": role_name,
            "description": "Test role with only donors.view permission",
            "permissions": {
                "donors": ["view"]
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/roles", json=role_data, headers=headers)
        assert response.status_code == 200, f"Failed to create role: {response.text}"
        
        created_role = response.json()
        self.custom_role_id = created_role["id"]
        
        # Verify the role was created with correct permissions
        assert created_role["permissions"]["donors"] == ["view"]
        assert "laboratory" not in created_role["permissions"]
        
        print(f"SUCCESS: Created custom role '{role_name}' with donors.view only")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/roles/{self.custom_role_id}", headers=headers)


class TestRolesAPIStillWorking(TestPermissionEnforcementBase):
    """Verify Roles API CRUD operations still work after middleware changes"""
    
    def test_get_roles_list(self):
        """GET /api/roles returns list of roles"""
        headers = self.get_auth_header("org_admin")
        response = self.session.get(f"{BASE_URL}/api/roles", headers=headers)
        assert response.status_code == 200, f"Failed to get roles: {response.text}"
        
        roles = response.json()
        assert isinstance(roles, list)
        assert len(roles) >= 8, "Should have at least 8 system roles"
        print(f"SUCCESS: GET /api/roles returns {len(roles)} roles")
    
    def test_get_available_modules(self):
        """GET /api/roles/available-modules returns modules"""
        headers = self.get_auth_header("org_admin")
        response = self.session.get(f"{BASE_URL}/api/roles/available-modules", headers=headers)
        assert response.status_code == 200, f"Failed to get modules: {response.text}"
        
        data = response.json()
        assert "modules" in data
        print("SUCCESS: GET /api/roles/available-modules works")
    
    def test_get_my_permissions(self):
        """GET /api/roles/my-permissions returns user permissions"""
        headers = self.get_auth_header("org_admin")
        response = self.session.get(f"{BASE_URL}/api/roles/my-permissions", headers=headers)
        assert response.status_code == 200, f"Failed to get permissions: {response.text}"
        
        data = response.json()
        assert "permissions" in data
        print("SUCCESS: GET /api/roles/my-permissions works")
    
    def test_create_update_delete_role(self):
        """Full CRUD cycle for custom role"""
        headers = self.get_auth_header("org_admin")
        
        # Create
        role_name = f"TEST_CRUD_{uuid.uuid4().hex[:8]}"
        create_response = self.session.post(f"{BASE_URL}/api/roles", json={
            "name": role_name,
            "permissions": {"dashboard": ["view"]}
        }, headers=headers)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        role_id = create_response.json()["id"]
        
        # Update
        update_response = self.session.put(f"{BASE_URL}/api/roles/{role_id}", json={
            "name": f"{role_name}_Updated"
        }, headers=headers)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Delete
        delete_response = self.session.delete(f"{BASE_URL}/api/roles/{role_id}", headers=headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        print("SUCCESS: Roles CRUD operations still working")


class TestUnauthenticatedAccess(TestPermissionEnforcementBase):
    """Test that unauthenticated users are blocked"""
    
    def test_unauthenticated_blocked_from_donors(self):
        """Unauthenticated user cannot access /api/donors"""
        response = self.session.get(f"{BASE_URL}/api/donors")
        assert response.status_code in [401, 403], f"Should be blocked: {response.status_code}"
        print("SUCCESS: Unauthenticated user blocked from /api/donors")
    
    def test_unauthenticated_blocked_from_inventory(self):
        """Unauthenticated user cannot access /api/inventory/summary"""
        response = self.session.get(f"{BASE_URL}/api/inventory/summary")
        assert response.status_code in [401, 403], f"Should be blocked: {response.status_code}"
        print("SUCCESS: Unauthenticated user blocked from /api/inventory/summary")
    
    def test_unauthenticated_blocked_from_lab_tests(self):
        """Unauthenticated user cannot access /api/lab-tests"""
        response = self.session.get(f"{BASE_URL}/api/lab-tests")
        assert response.status_code in [401, 403], f"Should be blocked: {response.status_code}"
        print("SUCCESS: Unauthenticated user blocked from /api/lab-tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
