"""
Test Broadcasts API - Share Availability Feature
Tests for urgent needs and surplus alerts broadcasting across the blood bank network
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_ORG_ADMIN = {"email": "admin@testorg.com", "password": "Test@123"}
SYSTEM_ADMIN = {"email": "admin@bloodbank.com", "password": "adminpassword"}


class TestBroadcastsPublicEndpoints:
    """Test public broadcast endpoints (no auth required)"""
    
    def test_get_active_broadcasts(self):
        """GET /api/broadcasts/active - Returns active broadcasts"""
        response = requests.get(f"{BASE_URL}/api/broadcasts/active")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "broadcasts" in data
        assert isinstance(data["broadcasts"], list)
        print(f"✓ GET /api/broadcasts/active - Found {data['count']} active broadcasts")
    
    def test_get_active_broadcasts_with_type_filter(self):
        """GET /api/broadcasts/active with broadcast_type filter"""
        response = requests.get(f"{BASE_URL}/api/broadcasts/active?broadcast_type=urgent_need")
        assert response.status_code == 200
        data = response.json()
        # All returned broadcasts should be urgent_need type
        for broadcast in data["broadcasts"]:
            assert broadcast["broadcast_type"] == "urgent_need"
        print(f"✓ GET /api/broadcasts/active?broadcast_type=urgent_need - Filter works")
    
    def test_get_active_broadcasts_with_blood_group_filter(self):
        """GET /api/broadcasts/active with blood_group filter"""
        response = requests.get(f"{BASE_URL}/api/broadcasts/active?blood_group=O-")
        assert response.status_code == 200
        data = response.json()
        for broadcast in data["broadcasts"]:
            assert broadcast["blood_group"] == "O-"
        print(f"✓ GET /api/broadcasts/active?blood_group=O- - Filter works")
    
    def test_get_broadcast_stats(self):
        """GET /api/broadcasts/stats - Returns network statistics"""
        response = requests.get(f"{BASE_URL}/api/broadcasts/stats")
        assert response.status_code == 200
        data = response.json()
        assert "urgent_needs_active" in data
        assert "surplus_alerts_active" in data
        assert "total_fulfilled" in data
        assert "total_responses" in data
        assert isinstance(data["urgent_needs_active"], int)
        assert isinstance(data["surplus_alerts_active"], int)
        print(f"✓ GET /api/broadcasts/stats - Stats: urgent={data['urgent_needs_active']}, surplus={data['surplus_alerts_active']}")


class TestBroadcastsAuthenticated:
    """Test authenticated broadcast endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for test org admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_ORG_ADMIN)
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.user = response.json()["user"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_my_broadcasts(self):
        """GET /api/broadcasts/my-broadcasts - Returns user's org broadcasts"""
        response = requests.get(f"{BASE_URL}/api/broadcasts/my-broadcasts", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "broadcasts" in data
        assert isinstance(data["broadcasts"], list)
        # All broadcasts should belong to user's org
        for broadcast in data["broadcasts"]:
            assert broadcast["org_id"] == self.user["org_id"]
        print(f"✓ GET /api/broadcasts/my-broadcasts - Found {data['count']} broadcasts for org")
    
    def test_create_urgent_need_broadcast(self):
        """POST /api/broadcasts - Create urgent need broadcast"""
        payload = {
            "broadcast_type": "urgent_need",
            "blood_group": "A+",
            "title": f"TEST_Urgent A+ needed - {uuid.uuid4().hex[:8]}",
            "description": "Test urgent need broadcast",
            "units_needed": 3,
            "priority": "high",
            "visibility": "network_wide",
            "expires_in_hours": 24
        }
        response = requests.post(f"{BASE_URL}/api/broadcasts", json=payload, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "broadcast" in data
        broadcast = data["broadcast"]
        assert broadcast["broadcast_type"] == "urgent_need"
        assert broadcast["blood_group"] == "A+"
        assert broadcast["units_needed"] == 3
        assert broadcast["priority"] == "high"
        assert broadcast["status"] == "active"
        assert "id" in broadcast
        self.created_broadcast_id = broadcast["id"]
        print(f"✓ POST /api/broadcasts - Created urgent need broadcast: {broadcast['id']}")
        
        # Cleanup - delete the test broadcast
        requests.delete(f"{BASE_URL}/api/broadcasts/{broadcast['id']}", headers=self.headers)
    
    def test_create_surplus_alert_broadcast(self):
        """POST /api/broadcasts - Create surplus alert broadcast"""
        payload = {
            "broadcast_type": "surplus_alert",
            "blood_group": "B+",
            "title": f"TEST_Surplus B+ available - {uuid.uuid4().hex[:8]}",
            "description": "Test surplus alert broadcast",
            "units_available": 10,
            "expiry_date": "2026-02-15",
            "priority": "normal",
            "visibility": "network_wide",
            "expires_in_hours": 48
        }
        response = requests.post(f"{BASE_URL}/api/broadcasts", json=payload, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        broadcast = data["broadcast"]
        assert broadcast["broadcast_type"] == "surplus_alert"
        assert broadcast["blood_group"] == "B+"
        assert broadcast["units_available"] == 10
        print(f"✓ POST /api/broadcasts - Created surplus alert broadcast: {broadcast['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/broadcasts/{broadcast['id']}", headers=self.headers)
    
    def test_create_broadcast_missing_required_fields(self):
        """POST /api/broadcasts - Should fail without required fields"""
        payload = {
            "broadcast_type": "urgent_need"
            # Missing blood_group and title
        }
        response = requests.post(f"{BASE_URL}/api/broadcasts", json=payload, headers=self.headers)
        assert response.status_code == 422  # Validation error
        print("✓ POST /api/broadcasts - Validation error for missing fields")
    
    def test_get_single_broadcast(self):
        """GET /api/broadcasts/{id} - Get broadcast details"""
        # First get an active broadcast
        active_response = requests.get(f"{BASE_URL}/api/broadcasts/active")
        broadcasts = active_response.json()["broadcasts"]
        if not broadcasts:
            pytest.skip("No active broadcasts to test")
        
        broadcast_id = broadcasts[0]["id"]
        response = requests.get(f"{BASE_URL}/api/broadcasts/{broadcast_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == broadcast_id
        assert "responses" in data  # Should include responses
        print(f"✓ GET /api/broadcasts/{broadcast_id} - Retrieved broadcast details")
    
    def test_get_nonexistent_broadcast(self):
        """GET /api/broadcasts/{id} - Should return 404 for invalid ID"""
        response = requests.get(f"{BASE_URL}/api/broadcasts/nonexistent-id-12345")
        assert response.status_code == 404
        print("✓ GET /api/broadcasts/nonexistent-id - Returns 404")


class TestBroadcastResponses:
    """Test broadcast response functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup with system admin (different org) to test responses"""
        # Login as system admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SYSTEM_ADMIN)
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.user = response.json()["user"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("System admin authentication failed")
        
        # Also get test org admin token
        response2 = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_ORG_ADMIN)
        if response2.status_code == 200:
            self.org_token = response2.json()["token"]
            self.org_headers = {"Authorization": f"Bearer {self.org_token}"}
    
    def test_respond_to_broadcast(self):
        """POST /api/broadcasts/{id}/respond - Respond to a broadcast"""
        # Get active broadcasts
        active_response = requests.get(f"{BASE_URL}/api/broadcasts/active")
        broadcasts = active_response.json()["broadcasts"]
        if not broadcasts:
            pytest.skip("No active broadcasts to respond to")
        
        # Find a broadcast not from system admin's org
        target_broadcast = None
        for b in broadcasts:
            if b["org_id"] != self.user.get("org_id"):
                target_broadcast = b
                break
        
        if not target_broadcast:
            pytest.skip("No broadcasts from other orgs to respond to")
        
        payload = {
            "message": "TEST_We can help with 2 units",
            "units_offered": 2,
            "contact_phone": "+1987654321"
        }
        response = requests.post(
            f"{BASE_URL}/api/broadcasts/{target_broadcast['id']}/respond",
            json=payload,
            headers=self.headers
        )
        # System admin has no org_id, so this should fail
        if response.status_code == 400:
            print("✓ POST /api/broadcasts/{id}/respond - Correctly requires org association")
        elif response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            print(f"✓ POST /api/broadcasts/{target_broadcast['id']}/respond - Response sent")
    
    def test_cannot_respond_to_own_broadcast(self):
        """POST /api/broadcasts/{id}/respond - Cannot respond to own broadcast"""
        # Get broadcasts from test org
        my_response = requests.get(f"{BASE_URL}/api/broadcasts/my-broadcasts", headers=self.org_headers)
        my_broadcasts = my_response.json()["broadcasts"]
        
        if not my_broadcasts:
            pytest.skip("No own broadcasts to test")
        
        own_broadcast = my_broadcasts[0]
        payload = {
            "message": "TEST_Trying to respond to own broadcast",
            "units_offered": 1
        }
        response = requests.post(
            f"{BASE_URL}/api/broadcasts/{own_broadcast['id']}/respond",
            json=payload,
            headers=self.org_headers
        )
        assert response.status_code == 400
        assert "own broadcast" in response.json()["detail"].lower()
        print("✓ POST /api/broadcasts/{id}/respond - Cannot respond to own broadcast")


class TestBroadcastManagement:
    """Test broadcast close and delete functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_ORG_ADMIN)
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_close_broadcast_as_fulfilled(self):
        """PUT /api/broadcasts/{id}/close - Close broadcast as fulfilled"""
        # Create a test broadcast first
        payload = {
            "broadcast_type": "urgent_need",
            "blood_group": "AB-",
            "title": f"TEST_Close test - {uuid.uuid4().hex[:8]}",
            "units_needed": 1,
            "expires_in_hours": 24
        }
        create_response = requests.post(f"{BASE_URL}/api/broadcasts", json=payload, headers=self.headers)
        assert create_response.status_code == 200
        broadcast_id = create_response.json()["broadcast"]["id"]
        
        # Close it
        close_response = requests.put(
            f"{BASE_URL}/api/broadcasts/{broadcast_id}/close?reason=fulfilled",
            headers=self.headers
        )
        assert close_response.status_code == 200
        assert close_response.json()["status"] == "success"
        print(f"✓ PUT /api/broadcasts/{broadcast_id}/close - Broadcast marked as fulfilled")
        
        # Verify it's closed
        get_response = requests.get(f"{BASE_URL}/api/broadcasts/{broadcast_id}")
        assert get_response.json()["status"] == "fulfilled"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/broadcasts/{broadcast_id}", headers=self.headers)
    
    def test_delete_own_broadcast(self):
        """DELETE /api/broadcasts/{id} - Delete own broadcast"""
        # Create a test broadcast
        payload = {
            "broadcast_type": "surplus_alert",
            "blood_group": "O+",
            "title": f"TEST_Delete test - {uuid.uuid4().hex[:8]}",
            "units_available": 5,
            "expires_in_hours": 24
        }
        create_response = requests.post(f"{BASE_URL}/api/broadcasts", json=payload, headers=self.headers)
        assert create_response.status_code == 200
        broadcast_id = create_response.json()["broadcast"]["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/broadcasts/{broadcast_id}", headers=self.headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "success"
        print(f"✓ DELETE /api/broadcasts/{broadcast_id} - Broadcast deleted")
        
        # Verify it's gone
        get_response = requests.get(f"{BASE_URL}/api/broadcasts/{broadcast_id}")
        assert get_response.status_code == 404
    
    def test_get_broadcast_responses(self):
        """GET /api/broadcasts/{id}/responses - Get responses to a broadcast"""
        # Get my broadcasts
        my_response = requests.get(f"{BASE_URL}/api/broadcasts/my-broadcasts", headers=self.headers)
        my_broadcasts = my_response.json()["broadcasts"]
        
        if not my_broadcasts:
            pytest.skip("No broadcasts to get responses for")
        
        broadcast_id = my_broadcasts[0]["id"]
        response = requests.get(f"{BASE_URL}/api/broadcasts/{broadcast_id}/responses", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "responses" in data
        print(f"✓ GET /api/broadcasts/{broadcast_id}/responses - Found {data['count']} responses")


class TestBroadcastValidation:
    """Test broadcast validation and edge cases"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_ORG_ADMIN)
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_create_broadcast_with_all_fields(self):
        """POST /api/broadcasts - Create with all optional fields"""
        payload = {
            "broadcast_type": "urgent_need",
            "blood_group": "A-",
            "component_type": "prc",
            "title": f"TEST_Full fields - {uuid.uuid4().hex[:8]}",
            "description": "Complete test with all fields",
            "units_needed": 5,
            "priority": "critical",
            "visibility": "nearby_only",
            "radius_km": 50.0,
            "contact_name": "Test Contact",
            "contact_phone": "+1122334455",
            "expires_in_hours": 12
        }
        response = requests.post(f"{BASE_URL}/api/broadcasts", json=payload, headers=self.headers)
        assert response.status_code == 200
        broadcast = response.json()["broadcast"]
        assert broadcast["component_type"] == "prc"
        assert broadcast["priority"] == "critical"
        assert broadcast["visibility"] == "nearby_only"
        assert broadcast["radius_km"] == 50.0
        print(f"✓ POST /api/broadcasts - Created with all fields: {broadcast['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/broadcasts/{broadcast['id']}", headers=self.headers)
    
    def test_unauthenticated_create_fails(self):
        """POST /api/broadcasts - Should fail without auth"""
        payload = {
            "broadcast_type": "urgent_need",
            "blood_group": "O+",
            "title": "TEST_Unauth test"
        }
        response = requests.post(f"{BASE_URL}/api/broadcasts", json=payload)
        assert response.status_code in [401, 403]
        print("✓ POST /api/broadcasts - Correctly requires authentication")
    
    def test_unauthenticated_my_broadcasts_fails(self):
        """GET /api/broadcasts/my-broadcasts - Should fail without auth"""
        response = requests.get(f"{BASE_URL}/api/broadcasts/my-broadcasts")
        assert response.status_code in [401, 403]
        print("✓ GET /api/broadcasts/my-broadcasts - Correctly requires authentication")


# Cleanup fixture to remove test data
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_broadcasts():
    """Cleanup TEST_ prefixed broadcasts after all tests"""
    yield
    # Login and cleanup
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_ORG_ADMIN)
    if response.status_code == 200:
        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all broadcasts and delete TEST_ ones
        my_response = requests.get(f"{BASE_URL}/api/broadcasts/my-broadcasts", headers=headers)
        if my_response.status_code == 200:
            for broadcast in my_response.json()["broadcasts"]:
                if broadcast["title"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/broadcasts/{broadcast['id']}", headers=headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
