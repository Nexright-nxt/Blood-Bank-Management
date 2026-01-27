"""
Test Requestor API Endpoints
Tests for:
- Public Registration API - POST /api/requestors/register
- Duplicate email prevention
- Admin API - GET /api/requestors (list all)
- Admin API - GET /api/requestors/stats (statistics)
- Admin API - GET /api/requestors/pending (pending registrations)
- Admin API - PUT /api/requestors/{id}/approve (approve/reject)
- Admin API - PUT /api/requestors/{id}/suspend (suspend)
- Admin API - PUT /api/requestors/{id}/reactivate (reactivate)
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@testorg.com"
ADMIN_PASSWORD = "Test@123"
SYSTEM_ADMIN_EMAIL = "admin@bbms.local"
SYSTEM_ADMIN_PASSWORD = "Admin@123456"


class TestRequestorPublicRegistration:
    """Test public requestor registration endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.unique_id = str(uuid.uuid4())[:8]
        self.test_email = f"TEST_hospital_{self.unique_id}@test.com"
        
    def test_register_requestor_success(self):
        """Test successful requestor registration"""
        payload = {
            "organization_name": f"TEST Hospital {self.unique_id}",
            "requestor_type": "hospital",
            "contact_person": "Test Contact Person",
            "email": self.test_email,
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456",
            "license_number": "LIC123",
            "registration_number": "REG456",
            "notes": "Test registration"
        }
        
        response = requests.post(f"{BASE_URL}/api/requestors/register", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        assert "requestor_id" in data
        assert "pending" in data["message"].lower() or "submitted" in data["message"].lower()
        print(f"SUCCESS: Requestor registered with ID: {data['requestor_id']}")
        
    def test_register_requestor_duplicate_email(self):
        """Test duplicate email prevention"""
        # First registration
        payload = {
            "organization_name": f"TEST Hospital Dup {self.unique_id}",
            "requestor_type": "hospital",
            "contact_person": "Test Contact",
            "email": f"TEST_dup_{self.unique_id}@test.com",
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456"
        }
        
        response1 = requests.post(f"{BASE_URL}/api/requestors/register", json=payload)
        assert response1.status_code == 200, f"First registration failed: {response1.text}"
        
        # Second registration with same email
        payload["organization_name"] = f"TEST Hospital Dup2 {self.unique_id}"
        response2 = requests.post(f"{BASE_URL}/api/requestors/register", json=payload)
        
        assert response2.status_code == 400, f"Expected 400 for duplicate, got {response2.status_code}"
        data = response2.json()
        assert "pending" in data["detail"].lower() or "already" in data["detail"].lower()
        print(f"SUCCESS: Duplicate email correctly rejected: {data['detail']}")
        
    def test_register_requestor_invalid_data(self):
        """Test registration with invalid data"""
        # Missing required fields
        payload = {
            "organization_name": "Test",
            "email": "invalid-email"  # Invalid email format
        }
        
        response = requests.post(f"{BASE_URL}/api/requestors/register", json=payload)
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"
        print("SUCCESS: Invalid data correctly rejected with 422")
        
    def test_register_requestor_all_types(self):
        """Test registration with different requestor types"""
        types = ["hospital", "clinic", "emergency_service", "research_lab", "other"]
        
        for req_type in types:
            unique = str(uuid.uuid4())[:8]
            payload = {
                "organization_name": f"TEST {req_type.title()} {unique}",
                "requestor_type": req_type,
                "contact_person": "Test Contact",
                "email": f"TEST_{req_type}_{unique}@test.com",
                "phone": "1234567890",
                "password": "TestPass@123",
                "address": "123 Test Street, Test Building",
                "city": "Test City",
                "state": "Test State",
                "pincode": "123456"
            }
            
            response = requests.post(f"{BASE_URL}/api/requestors/register", json=payload)
            assert response.status_code == 200, f"Failed for type {req_type}: {response.text}"
            print(f"SUCCESS: Registered requestor type: {req_type}")


class TestRequestorAdminAPIs:
    """Test admin requestor management APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token"""
        # Try org admin first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print(f"Logged in as org admin: {ADMIN_EMAIL}")
        else:
            # Try system admin
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": SYSTEM_ADMIN_EMAIL,
                "password": SYSTEM_ADMIN_PASSWORD
            })
            assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
            self.token = login_response.json().get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print(f"Logged in as system admin: {SYSTEM_ADMIN_EMAIL}")
    
    def test_get_all_requestors(self):
        """Test GET /api/requestors - list all requestors"""
        response = requests.get(f"{BASE_URL}/api/requestors", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of requestors"
        print(f"SUCCESS: Retrieved {len(data)} requestors")
        
        # Verify structure of requestor objects
        if len(data) > 0:
            requestor = data[0]
            assert "id" in requestor
            assert "organization_name" in requestor
            assert "email" in requestor
            assert "status" in requestor
            print(f"SUCCESS: Requestor structure verified - {requestor['organization_name']}")
    
    def test_get_requestors_with_status_filter(self):
        """Test GET /api/requestors with status filter"""
        for status in ["pending", "approved", "rejected", "suspended"]:
            response = requests.get(f"{BASE_URL}/api/requestors?status={status}", headers=self.headers)
            assert response.status_code == 200, f"Failed for status {status}: {response.text}"
            data = response.json()
            # All returned requestors should have the filtered status
            for req in data:
                assert req["status"] == status, f"Expected status {status}, got {req['status']}"
            print(f"SUCCESS: Status filter '{status}' returned {len(data)} requestors")
    
    def test_get_requestors_with_search(self):
        """Test GET /api/requestors with search"""
        response = requests.get(f"{BASE_URL}/api/requestors?search=hospital", headers=self.headers)
        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()
        print(f"SUCCESS: Search 'hospital' returned {len(data)} requestors")
    
    def test_get_requestor_stats(self):
        """Test GET /api/requestors/stats"""
        response = requests.get(f"{BASE_URL}/api/requestors/stats", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify stats structure
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data
        assert "suspended" in data
        assert "by_type" in data
        
        print(f"SUCCESS: Stats - Total: {data['total']}, Pending: {data['pending']}, Approved: {data['approved']}")
    
    def test_get_pending_requestors(self):
        """Test GET /api/requestors/pending"""
        response = requests.get(f"{BASE_URL}/api/requestors/pending", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of pending requestors"
        
        # All should be pending
        for req in data:
            assert req["status"] == "pending", f"Expected pending status, got {req['status']}"
        
        print(f"SUCCESS: Retrieved {len(data)} pending requestors")
    
    def test_get_single_requestor(self):
        """Test GET /api/requestors/{id}"""
        # First get list to find an ID
        list_response = requests.get(f"{BASE_URL}/api/requestors", headers=self.headers)
        assert list_response.status_code == 200
        requestors = list_response.json()
        
        if len(requestors) > 0:
            requestor_id = requestors[0]["id"]
            response = requests.get(f"{BASE_URL}/api/requestors/{requestor_id}", headers=self.headers)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert data["id"] == requestor_id
            print(f"SUCCESS: Retrieved requestor: {data['organization_name']}")
        else:
            pytest.skip("No requestors to test")
    
    def test_get_nonexistent_requestor(self):
        """Test GET /api/requestors/{id} with invalid ID"""
        response = requests.get(f"{BASE_URL}/api/requestors/nonexistent-id-12345", headers=self.headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: Nonexistent requestor returns 404")


class TestRequestorApprovalWorkflow:
    """Test requestor approval/rejection workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token and create test requestor"""
        # Login as admin
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code != 200:
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": SYSTEM_ADMIN_EMAIL,
                "password": SYSTEM_ADMIN_PASSWORD
            })
        
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get organizations for approval
        orgs_response = requests.get(f"{BASE_URL}/api/organizations", headers=self.headers)
        if orgs_response.status_code == 200:
            orgs = orgs_response.json()
            self.org_id = orgs[0]["id"] if len(orgs) > 0 else None
        else:
            self.org_id = None
    
    def test_approve_requestor(self):
        """Test approving a pending requestor"""
        # Create a new requestor
        unique_id = str(uuid.uuid4())[:8]
        register_payload = {
            "organization_name": f"TEST Approve Hospital {unique_id}",
            "requestor_type": "hospital",
            "contact_person": "Test Approve Contact",
            "email": f"TEST_approve_{unique_id}@test.com",
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/requestors/register", json=register_payload)
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        requestor_id = reg_response.json()["requestor_id"]
        
        # Get org ID if not available
        if not self.org_id:
            orgs_response = requests.get(f"{BASE_URL}/api/organizations", headers=self.headers)
            if orgs_response.status_code == 200 and len(orgs_response.json()) > 0:
                self.org_id = orgs_response.json()[0]["id"]
            else:
                pytest.skip("No organizations available for approval")
        
        # Approve the requestor
        approve_payload = {
            "action": "approve",
            "associated_org_id": self.org_id
        }
        
        response = requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/approve",
            json=approve_payload,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Approval failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        assert "user_id" in data, "User account should be created"
        print(f"SUCCESS: Requestor approved, user created: {data['user_id']}")
        
        # Verify requestor status changed
        get_response = requests.get(f"{BASE_URL}/api/requestors/{requestor_id}", headers=self.headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "approved"
        print("SUCCESS: Requestor status verified as 'approved'")
    
    def test_reject_requestor(self):
        """Test rejecting a pending requestor"""
        # Create a new requestor
        unique_id = str(uuid.uuid4())[:8]
        register_payload = {
            "organization_name": f"TEST Reject Hospital {unique_id}",
            "requestor_type": "clinic",
            "contact_person": "Test Reject Contact",
            "email": f"TEST_reject_{unique_id}@test.com",
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/requestors/register", json=register_payload)
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        requestor_id = reg_response.json()["requestor_id"]
        
        # Reject the requestor
        reject_payload = {
            "action": "reject",
            "rejection_reason": "Test rejection - incomplete documentation"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/approve",
            json=reject_payload,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Rejection failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        print("SUCCESS: Requestor rejected")
        
        # Verify requestor status changed
        get_response = requests.get(f"{BASE_URL}/api/requestors/{requestor_id}", headers=self.headers)
        assert get_response.status_code == 200
        req_data = get_response.json()
        assert req_data["status"] == "rejected"
        assert req_data["rejection_reason"] == "Test rejection - incomplete documentation"
        print("SUCCESS: Requestor status verified as 'rejected' with reason")
    
    def test_approve_without_org_id(self):
        """Test approval without associated_org_id fails"""
        # Create a new requestor
        unique_id = str(uuid.uuid4())[:8]
        register_payload = {
            "organization_name": f"TEST NoOrg Hospital {unique_id}",
            "requestor_type": "hospital",
            "contact_person": "Test Contact",
            "email": f"TEST_noorg_{unique_id}@test.com",
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/requestors/register", json=register_payload)
        assert reg_response.status_code == 200
        requestor_id = reg_response.json()["requestor_id"]
        
        # Try to approve without org_id
        approve_payload = {
            "action": "approve"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/approve",
            json=approve_payload,
            headers=self.headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("SUCCESS: Approval without org_id correctly rejected")
    
    def test_reject_without_reason(self):
        """Test rejection without reason fails"""
        # Create a new requestor
        unique_id = str(uuid.uuid4())[:8]
        register_payload = {
            "organization_name": f"TEST NoReason Hospital {unique_id}",
            "requestor_type": "hospital",
            "contact_person": "Test Contact",
            "email": f"TEST_noreason_{unique_id}@test.com",
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/requestors/register", json=register_payload)
        assert reg_response.status_code == 200
        requestor_id = reg_response.json()["requestor_id"]
        
        # Try to reject without reason
        reject_payload = {
            "action": "reject"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/approve",
            json=reject_payload,
            headers=self.headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("SUCCESS: Rejection without reason correctly rejected")


class TestRequestorSuspendReactivate:
    """Test suspend and reactivate functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code != 200:
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": SYSTEM_ADMIN_EMAIL,
                "password": SYSTEM_ADMIN_PASSWORD
            })
        
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get org ID
        orgs_response = requests.get(f"{BASE_URL}/api/organizations", headers=self.headers)
        if orgs_response.status_code == 200 and len(orgs_response.json()) > 0:
            self.org_id = orgs_response.json()[0]["id"]
        else:
            self.org_id = None
    
    def test_suspend_approved_requestor(self):
        """Test suspending an approved requestor"""
        if not self.org_id:
            pytest.skip("No organizations available")
        
        # Create and approve a requestor
        unique_id = str(uuid.uuid4())[:8]
        register_payload = {
            "organization_name": f"TEST Suspend Hospital {unique_id}",
            "requestor_type": "hospital",
            "contact_person": "Test Suspend Contact",
            "email": f"TEST_suspend_{unique_id}@test.com",
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/requestors/register", json=register_payload)
        assert reg_response.status_code == 200
        requestor_id = reg_response.json()["requestor_id"]
        
        # Approve first
        approve_response = requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/approve",
            json={"action": "approve", "associated_org_id": self.org_id},
            headers=self.headers
        )
        assert approve_response.status_code == 200
        
        # Now suspend
        response = requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/suspend?reason=Test%20suspension",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Suspend failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        print("SUCCESS: Requestor suspended")
        
        # Verify status
        get_response = requests.get(f"{BASE_URL}/api/requestors/{requestor_id}", headers=self.headers)
        assert get_response.json()["status"] == "suspended"
        print("SUCCESS: Requestor status verified as 'suspended'")
    
    def test_reactivate_suspended_requestor(self):
        """Test reactivating a suspended requestor"""
        if not self.org_id:
            pytest.skip("No organizations available")
        
        # Create, approve, and suspend a requestor
        unique_id = str(uuid.uuid4())[:8]
        register_payload = {
            "organization_name": f"TEST Reactivate Hospital {unique_id}",
            "requestor_type": "hospital",
            "contact_person": "Test Reactivate Contact",
            "email": f"TEST_reactivate_{unique_id}@test.com",
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/requestors/register", json=register_payload)
        assert reg_response.status_code == 200
        requestor_id = reg_response.json()["requestor_id"]
        
        # Approve
        requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/approve",
            json={"action": "approve", "associated_org_id": self.org_id},
            headers=self.headers
        )
        
        # Suspend
        requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/suspend?reason=Test",
            headers=self.headers
        )
        
        # Reactivate
        response = requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/reactivate",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Reactivate failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        print("SUCCESS: Requestor reactivated")
        
        # Verify status
        get_response = requests.get(f"{BASE_URL}/api/requestors/{requestor_id}", headers=self.headers)
        assert get_response.json()["status"] == "approved"
        print("SUCCESS: Requestor status verified as 'approved' after reactivation")
    
    def test_suspend_pending_requestor_fails(self):
        """Test that suspending a pending requestor fails"""
        # Create a pending requestor
        unique_id = str(uuid.uuid4())[:8]
        register_payload = {
            "organization_name": f"TEST SuspendPending Hospital {unique_id}",
            "requestor_type": "hospital",
            "contact_person": "Test Contact",
            "email": f"TEST_suspendpending_{unique_id}@test.com",
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/requestors/register", json=register_payload)
        assert reg_response.status_code == 200
        requestor_id = reg_response.json()["requestor_id"]
        
        # Try to suspend pending requestor
        response = requests.put(
            f"{BASE_URL}/api/requestors/{requestor_id}/suspend?reason=Test",
            headers=self.headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("SUCCESS: Suspending pending requestor correctly rejected")


class TestRequestorCheckStatus:
    """Test public status check endpoint"""
    
    def test_check_status_existing(self):
        """Test checking status of existing registration"""
        # Create a requestor first
        unique_id = str(uuid.uuid4())[:8]
        email = f"TEST_checkstatus_{unique_id}@test.com"
        register_payload = {
            "organization_name": f"TEST CheckStatus Hospital {unique_id}",
            "requestor_type": "hospital",
            "contact_person": "Test Contact",
            "email": email,
            "phone": "1234567890",
            "password": "TestPass@123",
            "address": "123 Test Street, Test Building",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/requestors/register", json=register_payload)
        assert reg_response.status_code == 200
        
        # Check status
        response = requests.get(f"{BASE_URL}/api/requestors/check-status/{email}")
        
        assert response.status_code == 200, f"Status check failed: {response.text}"
        data = response.json()
        assert data["status"] == "pending"
        assert data["organization_name"] == f"TEST CheckStatus Hospital {unique_id}"
        print(f"SUCCESS: Status check returned: {data['status']}")
    
    def test_check_status_nonexistent(self):
        """Test checking status of non-existent email"""
        response = requests.get(f"{BASE_URL}/api/requestors/check-status/nonexistent@test.com")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: Non-existent email returns 404")


class TestRequestorUnauthenticated:
    """Test that admin endpoints require authentication"""
    
    def test_get_requestors_unauthenticated(self):
        """Test GET /api/requestors without auth"""
        response = requests.get(f"{BASE_URL}/api/requestors")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("SUCCESS: Unauthenticated access to /api/requestors blocked")
    
    def test_get_stats_unauthenticated(self):
        """Test GET /api/requestors/stats without auth"""
        response = requests.get(f"{BASE_URL}/api/requestors/stats")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("SUCCESS: Unauthenticated access to /api/requestors/stats blocked")
    
    def test_get_pending_unauthenticated(self):
        """Test GET /api/requestors/pending without auth"""
        response = requests.get(f"{BASE_URL}/api/requestors/pending")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("SUCCESS: Unauthenticated access to /api/requestors/pending blocked")


# Cleanup fixture to remove test data
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_requestors():
    """Cleanup TEST_ prefixed requestors after all tests"""
    yield
    
    # Login as admin
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if login_response.status_code != 200:
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYSTEM_ADMIN_EMAIL,
            "password": SYSTEM_ADMIN_PASSWORD
        })
    
    if login_response.status_code == 200:
        token = login_response.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all requestors and delete TEST_ ones
        response = requests.get(f"{BASE_URL}/api/requestors", headers=headers)
        if response.status_code == 200:
            requestors = response.json()
            test_count = sum(1 for r in requestors if r.get("organization_name", "").startswith("TEST"))
            print(f"\nCleanup: Found {test_count} TEST_ requestors (not deleting - no delete endpoint)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
