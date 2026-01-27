"""
Test Suite for Custom Roles & Permissions Feature
Tests:
- Roles CRUD API endpoints
- Available modules endpoint
- My permissions endpoint
- Role duplication
- System role protection
- Permission middleware
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ORG_ADMIN_EMAIL = "admin@testorg.com"
ORG_ADMIN_PASSWORD = "Test@123"
SYSTEM_ADMIN_EMAIL = "admin@bbms.local"
SYSTEM_ADMIN_PASSWORD = "Admin@123456"


class TestRolesAPI:
    """Test Roles CRUD API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.created_role_ids = []
    
    def teardown_method(self):
        """Cleanup created test roles"""
        if hasattr(self, 'auth_token') and self.auth_token:
            for role_id in self.created_role_ids:
                try:
                    self.session.delete(
                        f"{BASE_URL}/api/roles/{role_id}",
                        headers={"Authorization": f"Bearer {self.auth_token}"}
                    )
                except:
                    pass
    
    def login_org_admin(self):
        """Login as org admin"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        self.auth_token = data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        return data
    
    def login_system_admin(self):
        """Login as system admin"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYSTEM_ADMIN_EMAIL,
            "password": SYSTEM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"System admin login failed: {response.text}"
        data = response.json()
        self.auth_token = data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        return data
    
    # ==================== GET /api/roles ====================
    def test_get_roles_returns_list(self):
        """GET /api/roles returns list of roles (8 system roles + any custom)"""
        self.login_org_admin()
        
        response = self.session.get(f"{BASE_URL}/api/roles")
        assert response.status_code == 200, f"Failed to get roles: {response.text}"
        
        roles = response.json()
        assert isinstance(roles, list), "Response should be a list"
        
        # Should have at least 8 system roles
        system_roles = [r for r in roles if r.get("is_system_role")]
        assert len(system_roles) >= 8, f"Expected at least 8 system roles, got {len(system_roles)}"
        
        # Verify system role structure
        for role in system_roles:
            assert "id" in role, "Role should have id"
            assert "role_key" in role, "Role should have role_key"
            assert "name" in role, "Role should have name"
            assert "permissions" in role, "Role should have permissions"
            assert "is_system_role" in role, "Role should have is_system_role flag"
            assert "users_count" in role, "Role should have users_count"
        
        print(f"SUCCESS: GET /api/roles returned {len(roles)} roles ({len(system_roles)} system roles)")
    
    def test_get_roles_includes_expected_system_roles(self):
        """Verify expected system roles exist"""
        self.login_org_admin()
        
        response = self.session.get(f"{BASE_URL}/api/roles")
        assert response.status_code == 200
        
        roles = response.json()
        role_keys = [r.get("role_key") for r in roles]
        
        expected_roles = ["admin", "registration", "lab_tech", "processing", 
                         "qc_manager", "inventory", "distribution", "phlebotomist"]
        
        for expected in expected_roles:
            assert expected in role_keys, f"Expected system role '{expected}' not found"
        
        print(f"SUCCESS: All 8 expected system roles found")
    
    # ==================== GET /api/roles/available-modules ====================
    def test_get_available_modules(self):
        """GET /api/roles/available-modules returns all modules and actions"""
        self.login_org_admin()
        
        response = self.session.get(f"{BASE_URL}/api/roles/available-modules")
        assert response.status_code == 200, f"Failed to get available modules: {response.text}"
        
        data = response.json()
        assert "modules" in data, "Response should have 'modules' key"
        assert "system_roles" in data, "Response should have 'system_roles' key"
        
        modules = data["modules"]
        assert isinstance(modules, dict), "Modules should be a dictionary"
        
        # Verify expected modules exist
        expected_modules = ["dashboard", "donors", "donations", "screening", 
                          "laboratory", "processing", "inventory", "requests",
                          "users", "roles", "configuration"]
        
        for module in expected_modules:
            assert module in modules, f"Expected module '{module}' not found"
            assert isinstance(modules[module], list), f"Module '{module}' actions should be a list"
        
        print(f"SUCCESS: GET /api/roles/available-modules returned {len(modules)} modules")
    
    # ==================== GET /api/roles/my-permissions ====================
    def test_get_my_permissions_org_admin(self):
        """GET /api/roles/my-permissions returns current user's permissions"""
        self.login_org_admin()
        
        response = self.session.get(f"{BASE_URL}/api/roles/my-permissions")
        assert response.status_code == 200, f"Failed to get my permissions: {response.text}"
        
        data = response.json()
        assert "role" in data, "Response should have 'role' key"
        assert "role_name" in data, "Response should have 'role_name' key"
        assert "permissions" in data, "Response should have 'permissions' key"
        assert "is_system_admin" in data, "Response should have 'is_system_admin' key"
        assert "is_custom_role" in data, "Response should have 'is_custom_role' key"
        
        # Org admin should have admin role with full permissions
        assert data["role"] == "admin", f"Expected role 'admin', got '{data['role']}'"
        assert isinstance(data["permissions"], dict), "Permissions should be a dictionary"
        
        print(f"SUCCESS: GET /api/roles/my-permissions returned permissions for role '{data['role']}'")
    
    def test_get_my_permissions_system_admin(self):
        """System admin should have all permissions"""
        self.login_system_admin()
        
        response = self.session.get(f"{BASE_URL}/api/roles/my-permissions")
        assert response.status_code == 200, f"Failed to get my permissions: {response.text}"
        
        data = response.json()
        assert data["is_system_admin"] == True, "System admin should have is_system_admin=True"
        
        # System admin should have all modules
        permissions = data["permissions"]
        assert len(permissions) > 10, "System admin should have many module permissions"
        
        print(f"SUCCESS: System admin has all permissions ({len(permissions)} modules)")
    
    # ==================== POST /api/roles (Create) ====================
    def test_create_custom_role(self):
        """POST /api/roles creates a new custom role with permissions"""
        self.login_org_admin()
        
        role_name = f"TEST_Role_{uuid.uuid4().hex[:8]}"
        role_data = {
            "name": role_name,
            "description": "Test custom role for automated testing",
            "permissions": {
                "dashboard": ["view"],
                "donors": ["view", "create"],
                "inventory": ["view"]
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/roles", json=role_data)
        assert response.status_code == 200, f"Failed to create role: {response.text}"
        
        created_role = response.json()
        self.created_role_ids.append(created_role["id"])
        
        # Verify response structure
        assert created_role["name"] == role_name, "Role name should match"
        assert created_role["description"] == role_data["description"], "Description should match"
        assert created_role["is_system_role"] == False, "Custom role should not be system role"
        assert created_role["users_count"] == 0, "New role should have 0 users"
        assert "role_key" in created_role, "Role should have role_key"
        assert created_role["role_key"].startswith("custom_"), "Custom role key should start with 'custom_'"
        
        # Verify permissions
        assert created_role["permissions"]["dashboard"] == ["view"]
        assert set(created_role["permissions"]["donors"]) == {"view", "create"}
        
        print(f"SUCCESS: Created custom role '{role_name}' with id '{created_role['id']}'")
    
    def test_create_role_validates_permissions(self):
        """POST /api/roles validates module and action names"""
        self.login_org_admin()
        
        # Test invalid module
        invalid_module_data = {
            "name": "Invalid Module Test",
            "permissions": {
                "invalid_module": ["view"]
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/roles", json=invalid_module_data)
        assert response.status_code == 400, f"Should reject invalid module, got {response.status_code}"
        
        # Test invalid action
        invalid_action_data = {
            "name": "Invalid Action Test",
            "permissions": {
                "donors": ["invalid_action"]
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/roles", json=invalid_action_data)
        assert response.status_code == 400, f"Should reject invalid action, got {response.status_code}"
        
        print("SUCCESS: Role creation validates permissions correctly")
    
    # ==================== PUT /api/roles/{id} (Update) ====================
    def test_update_custom_role(self):
        """PUT /api/roles/{id} updates a custom role"""
        self.login_org_admin()
        
        # First create a role
        role_name = f"TEST_Update_{uuid.uuid4().hex[:8]}"
        create_response = self.session.post(f"{BASE_URL}/api/roles", json={
            "name": role_name,
            "description": "Original description",
            "permissions": {"dashboard": ["view"]}
        })
        assert create_response.status_code == 200
        created_role = create_response.json()
        self.created_role_ids.append(created_role["id"])
        
        # Update the role
        update_data = {
            "name": f"{role_name}_Updated",
            "description": "Updated description",
            "permissions": {
                "dashboard": ["view"],
                "donors": ["view", "create", "edit"]
            }
        }
        
        response = self.session.put(f"{BASE_URL}/api/roles/{created_role['id']}", json=update_data)
        assert response.status_code == 200, f"Failed to update role: {response.text}"
        
        updated_role = response.json()
        assert updated_role["name"] == update_data["name"], "Name should be updated"
        assert updated_role["description"] == update_data["description"], "Description should be updated"
        assert "donors" in updated_role["permissions"], "Permissions should be updated"
        
        # Verify persistence with GET
        get_response = self.session.get(f"{BASE_URL}/api/roles/{created_role['id']}")
        assert get_response.status_code == 200
        fetched_role = get_response.json()
        assert fetched_role["name"] == update_data["name"], "Update should persist"
        
        print(f"SUCCESS: Updated custom role '{created_role['id']}'")
    
    def test_update_system_role_fails(self):
        """PUT /api/roles/{id} should fail for system roles"""
        self.login_org_admin()
        
        # Get a system role
        roles_response = self.session.get(f"{BASE_URL}/api/roles")
        roles = roles_response.json()
        system_role = next((r for r in roles if r.get("is_system_role")), None)
        assert system_role, "Should have at least one system role"
        
        # Try to update it
        response = self.session.put(f"{BASE_URL}/api/roles/{system_role['id']}", json={
            "name": "Hacked Admin"
        })
        assert response.status_code == 403, f"Should reject system role update, got {response.status_code}"
        
        print(f"SUCCESS: System role '{system_role['name']}' cannot be edited")
    
    # ==================== DELETE /api/roles/{id} ====================
    def test_delete_custom_role(self):
        """DELETE /api/roles/{id} deletes a custom role"""
        self.login_org_admin()
        
        # First create a role
        role_name = f"TEST_Delete_{uuid.uuid4().hex[:8]}"
        create_response = self.session.post(f"{BASE_URL}/api/roles", json={
            "name": role_name,
            "permissions": {"dashboard": ["view"]}
        })
        assert create_response.status_code == 200
        created_role = create_response.json()
        role_id = created_role["id"]
        
        # Delete the role
        response = self.session.delete(f"{BASE_URL}/api/roles/{role_id}")
        assert response.status_code == 200, f"Failed to delete role: {response.text}"
        
        # Verify deletion with GET
        get_response = self.session.get(f"{BASE_URL}/api/roles/{role_id}")
        assert get_response.status_code == 404, "Deleted role should return 404"
        
        print(f"SUCCESS: Deleted custom role '{role_id}'")
    
    def test_delete_system_role_fails(self):
        """DELETE /api/roles/{id} should fail for system roles"""
        self.login_org_admin()
        
        # Get a system role
        roles_response = self.session.get(f"{BASE_URL}/api/roles")
        roles = roles_response.json()
        system_role = next((r for r in roles if r.get("is_system_role")), None)
        assert system_role, "Should have at least one system role"
        
        # Try to delete it
        response = self.session.delete(f"{BASE_URL}/api/roles/{system_role['id']}")
        assert response.status_code == 403, f"Should reject system role deletion, got {response.status_code}"
        
        print(f"SUCCESS: System role '{system_role['name']}' cannot be deleted")
    
    # ==================== POST /api/roles/{id}/duplicate ====================
    def test_duplicate_role(self):
        """POST /api/roles/{id}/duplicate duplicates a role"""
        self.login_org_admin()
        
        # First create a role
        role_name = f"TEST_Duplicate_{uuid.uuid4().hex[:8]}"
        create_response = self.session.post(f"{BASE_URL}/api/roles", json={
            "name": role_name,
            "description": "Original role",
            "permissions": {
                "dashboard": ["view"],
                "donors": ["view", "create"]
            }
        })
        assert create_response.status_code == 200
        original_role = create_response.json()
        self.created_role_ids.append(original_role["id"])
        
        # Duplicate the role
        response = self.session.post(f"{BASE_URL}/api/roles/{original_role['id']}/duplicate")
        assert response.status_code == 200, f"Failed to duplicate role: {response.text}"
        
        duplicated_role = response.json()
        self.created_role_ids.append(duplicated_role["id"])
        
        # Verify duplicate
        assert duplicated_role["id"] != original_role["id"], "Duplicate should have different ID"
        assert duplicated_role["name"] == f"{role_name} (Copy)", "Duplicate name should have (Copy) suffix"
        assert duplicated_role["permissions"] == original_role["permissions"], "Permissions should be copied"
        assert duplicated_role["is_system_role"] == False, "Duplicate should not be system role"
        
        print(f"SUCCESS: Duplicated role '{original_role['id']}' to '{duplicated_role['id']}'")
    
    def test_duplicate_system_role(self):
        """Can duplicate a system role to create custom version"""
        self.login_org_admin()
        
        # Get a system role
        roles_response = self.session.get(f"{BASE_URL}/api/roles")
        roles = roles_response.json()
        system_role = next((r for r in roles if r.get("is_system_role")), None)
        assert system_role, "Should have at least one system role"
        
        # Duplicate it
        response = self.session.post(f"{BASE_URL}/api/roles/{system_role['id']}/duplicate")
        assert response.status_code == 200, f"Failed to duplicate system role: {response.text}"
        
        duplicated_role = response.json()
        self.created_role_ids.append(duplicated_role["id"])
        
        assert duplicated_role["is_system_role"] == False, "Duplicated system role should be custom"
        assert duplicated_role["name"] == f"{system_role['name']} (Copy)"
        
        print(f"SUCCESS: Duplicated system role '{system_role['name']}' to custom role")
    
    # ==================== GET /api/roles/{id} (Single Role) ====================
    def test_get_single_role(self):
        """GET /api/roles/{id} returns a specific role"""
        self.login_org_admin()
        
        # Get all roles first
        roles_response = self.session.get(f"{BASE_URL}/api/roles")
        roles = roles_response.json()
        test_role = roles[0]
        
        # Get single role
        response = self.session.get(f"{BASE_URL}/api/roles/{test_role['id']}")
        assert response.status_code == 200, f"Failed to get role: {response.text}"
        
        role = response.json()
        assert role["id"] == test_role["id"], "Role ID should match"
        assert "users_count" in role, "Should include users_count"
        
        print(f"SUCCESS: GET /api/roles/{test_role['id']} returned role '{role['name']}'")
    
    def test_get_nonexistent_role(self):
        """GET /api/roles/{id} returns 404 for nonexistent role"""
        self.login_org_admin()
        
        fake_id = str(uuid.uuid4())
        response = self.session.get(f"{BASE_URL}/api/roles/{fake_id}")
        assert response.status_code == 404, f"Should return 404, got {response.status_code}"
        
        print("SUCCESS: Nonexistent role returns 404")


class TestPermissionMiddleware:
    """Test permission checking middleware"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def login_org_admin(self):
        """Login as org admin"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
        return data
    
    def test_authenticated_user_can_access_roles(self):
        """Authenticated user can access roles endpoints"""
        self.login_org_admin()
        
        # Should be able to access roles
        response = self.session.get(f"{BASE_URL}/api/roles")
        assert response.status_code == 200, "Authenticated user should access roles"
        
        print("SUCCESS: Authenticated user can access roles")
    
    def test_unauthenticated_user_blocked(self):
        """Unauthenticated user cannot access roles"""
        # No login - try to access roles
        response = self.session.get(f"{BASE_URL}/api/roles")
        assert response.status_code == 401, f"Should return 401, got {response.status_code}"
        
        print("SUCCESS: Unauthenticated user blocked from roles")


class TestExistingCustomRole:
    """Test the existing 'Limited Viewer' custom role"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.limited_viewer_id = "ece8b205-d3b7-4c7a-b61f-0f7bba0befeb"
    
    def login_org_admin(self):
        """Login as org admin"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
        return data
    
    def test_limited_viewer_exists(self):
        """Verify the 'Limited Viewer' custom role exists"""
        self.login_org_admin()
        
        response = self.session.get(f"{BASE_URL}/api/roles/{self.limited_viewer_id}")
        
        # Role may or may not exist depending on test environment
        if response.status_code == 200:
            role = response.json()
            assert role["name"] == "Limited Viewer" or "Limited" in role["name"]
            assert role["is_system_role"] == False
            print(f"SUCCESS: Found existing 'Limited Viewer' role: {role['name']}")
        else:
            print(f"INFO: 'Limited Viewer' role not found (may have been deleted)")
            pytest.skip("Limited Viewer role not found in this environment")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
