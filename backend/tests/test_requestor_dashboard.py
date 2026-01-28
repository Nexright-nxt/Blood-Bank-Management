"""
Test Requestor Dashboard APIs - Tests for requestor-specific endpoints
- /api/requestors/me/profile - Get requestor profile
- /api/requestors/me/requests - Get/Create blood requests
- /api/blood-link/blood-groups - Public blood availability
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials for requestor
REQUESTOR_EMAIL = "TEST_approve_d3f939f8@test.com"
REQUESTOR_PASSWORD = "TestPass@123"


class TestRequestorLogin:
    """Test requestor login and redirect behavior"""
    
    def test_requestor_login_success(self):
        """Test that requestor can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REQUESTOR_EMAIL,
            "password": REQUESTOR_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        
        user = data["user"]
        assert user["user_type"] == "requestor", f"Expected user_type 'requestor', got {user['user_type']}"
        assert user["role"] == "requestor", f"Expected role 'requestor', got {user['role']}"
        assert user["email"] == REQUESTOR_EMAIL
        
    def test_requestor_login_returns_org_info(self):
        """Test that login returns organization info for requestor"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REQUESTOR_EMAIL,
            "password": REQUESTOR_PASSWORD
        })
        assert response.status_code == 200
        
        data = response.json()
        user = data["user"]
        assert "org_id" in user, "org_id not in user response"
        assert user["org_id"] is not None, "org_id should not be None"


class TestRequestorProfile:
    """Test /api/requestors/me/profile endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for requestor"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REQUESTOR_EMAIL,
            "password": REQUESTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_profile_success(self, auth_token):
        """Test getting requestor profile"""
        response = requests.get(
            f"{BASE_URL}/api/requestors/me/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get profile: {response.text}"
        
        profile = response.json()
        assert "organization_name" in profile
        assert "email" in profile
        assert profile["email"] == REQUESTOR_EMAIL
        assert "requestor_type" in profile
        assert "status" in profile
        assert profile["status"] == "approved"
        
    def test_profile_contains_location_info(self, auth_token):
        """Test that profile contains address/location info"""
        response = requests.get(
            f"{BASE_URL}/api/requestors/me/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        profile = response.json()
        assert "address" in profile
        assert "city" in profile
        assert "state" in profile
        assert "pincode" in profile
        
    def test_profile_unauthorized_without_token(self):
        """Test that profile endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/requestors/me/profile")
        assert response.status_code == 401 or response.status_code == 403


class TestRequestorRequests:
    """Test /api/requestors/me/requests endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for requestor"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REQUESTOR_EMAIL,
            "password": REQUESTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_get_requests_success(self, auth_token):
        """Test getting requestor's blood requests"""
        response = requests.get(
            f"{BASE_URL}/api/requestors/me/requests",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get requests: {response.text}"
        
        requests_list = response.json()
        assert isinstance(requests_list, list), "Response should be a list"
        
    def test_existing_request_has_required_fields(self, auth_token):
        """Test that existing requests have all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/requestors/me/requests",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        requests_list = response.json()
        if len(requests_list) > 0:
            req = requests_list[0]
            assert "id" in req
            assert "blood_group" in req
            assert "status" in req
            assert "patient_name" in req
            assert "units_required" in req
            assert "created_at" in req
            
    def test_create_blood_request(self, auth_token):
        """Test creating a new blood request"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        request_data = {
            "blood_group": "A+",
            "component_type": "whole_blood",
            "units_required": 2,
            "urgency": "normal",
            "patient_name": f"TEST_Patient_{uuid.uuid4().hex[:8]}",
            "patient_age": 35,
            "patient_gender": "female",
            "diagnosis": "Scheduled Surgery",
            "doctor_name": "Dr. Test",
            "required_by_date": tomorrow,
            "notes": "Test request from automated testing",
            "location_type": "delivery",
            "delivery_address": "Test Hospital, Test City"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/requestors/me/requests",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_data
        )
        assert response.status_code == 200, f"Failed to create request: {response.text}"
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
        assert "request" in data
        
        created_request = data["request"]
        assert created_request["blood_group"] == "A+"
        assert created_request["patient_name"] == request_data["patient_name"]
        assert created_request["status"] == "pending"
        
    def test_create_request_with_pickup_location(self, auth_token):
        """Test creating request with self-pickup location type"""
        tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        request_data = {
            "blood_group": "B+",
            "component_type": "prc",
            "units_required": 1,
            "urgency": "urgent",
            "patient_name": f"TEST_Pickup_{uuid.uuid4().hex[:8]}",
            "patient_age": 50,
            "patient_gender": "male",
            "diagnosis": "Emergency",
            "required_by_date": tomorrow,
            "location_type": "pickup"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/requestors/me/requests",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_data
        )
        assert response.status_code == 200, f"Failed to create pickup request: {response.text}"
        
        data = response.json()
        assert data["request"]["location_type"] == "pickup"
        
    def test_created_request_appears_in_list(self, auth_token):
        """Test that newly created request appears in the requests list"""
        tomorrow = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        unique_name = f"TEST_Verify_{uuid.uuid4().hex[:8]}"
        
        # Create request
        request_data = {
            "blood_group": "O-",
            "units_required": 1,
            "urgency": "emergency",
            "patient_name": unique_name,
            "required_by_date": tomorrow,
            "location_type": "delivery"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/requestors/me/requests",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_data
        )
        assert create_response.status_code == 200
        
        # Verify it appears in list
        list_response = requests.get(
            f"{BASE_URL}/api/requestors/me/requests",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert list_response.status_code == 200
        
        requests_list = list_response.json()
        patient_names = [r["patient_name"] for r in requests_list]
        assert unique_name in patient_names, f"Created request not found in list. Names: {patient_names}"


class TestBloodAvailability:
    """Test public blood availability endpoint"""
    
    def test_get_blood_groups_availability(self):
        """Test getting public blood availability"""
        response = requests.get(f"{BASE_URL}/api/blood-link/blood-groups")
        assert response.status_code == 200, f"Failed to get blood groups: {response.text}"
        
        data = response.json()
        # Should have all 8 blood groups
        expected_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for group in expected_groups:
            assert group in data, f"Blood group {group} not in response"
            
    def test_blood_group_has_stock_info(self):
        """Test that each blood group has stock information"""
        response = requests.get(f"{BASE_URL}/api/blood-link/blood-groups")
        assert response.status_code == 200
        
        data = response.json()
        for group, info in data.items():
            assert "whole_blood" in info or "total" in info, f"Stock info missing for {group}"


class TestRequestorNavigation:
    """Test requestor-specific navigation items"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for requestor"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": REQUESTOR_EMAIL,
            "password": REQUESTOR_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_broadcasts_endpoint_accessible(self, auth_token):
        """Test that broadcasts endpoint is accessible to requestors"""
        response = requests.get(
            f"{BASE_URL}/api/broadcasts/active",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should be accessible (200) or empty (200 with empty list)
        assert response.status_code == 200, f"Broadcasts not accessible: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
