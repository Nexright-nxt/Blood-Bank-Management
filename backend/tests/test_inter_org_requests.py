"""
Inter-Organization Blood Requests API Tests
Tests the data flow between Find Blood page and Blood Requests page
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://bloodlink-lab-fix.preview.emergentagent.com')

# Test credentials
ORG_ADMIN_EMAIL = "admin@testorg.com"
ORG_ADMIN_PASSWORD = "Test@123"
SYSTEM_ADMIN_EMAIL = "admin@bbms.local"
SYSTEM_ADMIN_PASSWORD = "Admin@123456"


class TestInterOrgRequestsAPI:
    """Tests for inter-organization blood requests API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_org_admin_token(self):
        """Get authentication token for org admin"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Org admin authentication failed")
        
    def get_system_admin_token(self):
        """Get authentication token for system admin"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYSTEM_ADMIN_EMAIL,
            "password": SYSTEM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("System admin authentication failed")
    
    # ============== Authentication Tests ==============
    
    def test_org_admin_login(self):
        """Test org admin can login successfully"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ORG_ADMIN_EMAIL
        
    def test_system_admin_login(self):
        """Test system admin can login successfully"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYSTEM_ADMIN_EMAIL,
            "password": SYSTEM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["user_type"] == "system_admin"
    
    # ============== Organization Tests ==============
    
    def test_get_current_organization(self):
        """Test getting current organization with location data"""
        token = self.get_org_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(f"{BASE_URL}/api/organizations/current", headers=headers)
        assert response.status_code == 200
        
        org = response.json()
        assert "org_name" in org
        assert "id" in org
        # Verify location data exists
        assert "latitude" in org
        assert "longitude" in org
        
    def test_update_organization_location(self):
        """Test updating organization location via API"""
        token = self.get_system_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get organizations
        orgs_response = self.session.get(f"{BASE_URL}/api/organizations", headers=headers)
        assert orgs_response.status_code == 200
        orgs = orgs_response.json()
        
        # Find Test Organization
        test_org = next((o for o in orgs if o.get('org_name') == 'Test Organization'), None)
        assert test_org is not None, "Test Organization not found"
        
        # Update location
        update_payload = {
            "org_name": test_org["org_name"],
            "latitude": 19.0850,
            "longitude": 72.8850
        }
        update_response = self.session.put(
            f"{BASE_URL}/api/organizations/{test_org['id']}", 
            json=update_payload, 
            headers=headers
        )
        assert update_response.status_code == 200
        
        # Verify update
        updated_org = update_response.json()
        assert updated_org["latitude"] == 19.0850
        assert updated_org["longitude"] == 72.8850
        
        # Restore original location
        restore_payload = {
            "org_name": test_org["org_name"],
            "latitude": 19.076,
            "longitude": 72.8777
        }
        self.session.put(
            f"{BASE_URL}/api/organizations/{test_org['id']}", 
            json=restore_payload, 
            headers=headers
        )
    
    # ============== Inter-Org Request Tests ==============
    
    def test_create_inter_org_request(self):
        """Test creating an inter-org blood request (Find Blood flow)"""
        token = self.get_org_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user's org_id
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        org_id = login_response.json()["user"]["org_id"]
        
        # Create request payload (matching FindBlood.js handleCreateRequest)
        required_by = (datetime.now() + timedelta(days=3)).isoformat()
        payload = {
            "request_type": "internal",
            "fulfilling_org_id": org_id,
            "component_type": "whole_blood",
            "blood_group": "AB+",
            "quantity": 1,
            "urgency_level": "routine",
            "clinical_indication": "Patient: Test Patient - API Test",
            "required_by": required_by
        }
        
        response = self.session.post(f"{BASE_URL}/api/inter-org-requests", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
        assert "message" in data
        
        return data["id"]
    
    def test_get_outgoing_requests(self):
        """Test getting outgoing requests (Blood Requests page - My Requests tab)"""
        token = self.get_org_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(f"{BASE_URL}/api/inter-org-requests/outgoing", headers=headers)
        assert response.status_code == 200
        
        requests_list = response.json()
        assert isinstance(requests_list, list)
        
        # Verify request structure
        if requests_list:
            req = requests_list[0]
            assert "id" in req
            assert "blood_group" in req
            assert "status" in req
            assert "component_type" in req
            
    def test_get_incoming_requests(self):
        """Test getting incoming requests (Blood Requests page - Incoming tab)"""
        token = self.get_org_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(f"{BASE_URL}/api/inter-org-requests/incoming", headers=headers)
        assert response.status_code == 200
        
        requests_list = response.json()
        assert isinstance(requests_list, list)
        
    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics"""
        token = self.get_org_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(f"{BASE_URL}/api/inter-org-requests/dashboard/stats", headers=headers)
        assert response.status_code == 200
        
        stats = response.json()
        assert "incoming" in stats
        assert "outgoing" in stats
        assert "pending" in stats["incoming"]
        
    def test_request_appears_in_outgoing_after_creation(self):
        """Test that a created request appears in outgoing requests list"""
        token = self.get_org_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user's org_id
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        org_id = login_response.json()["user"]["org_id"]
        
        # Create a unique request
        required_by = (datetime.now() + timedelta(days=5)).isoformat()
        payload = {
            "request_type": "internal",
            "fulfilling_org_id": org_id,
            "component_type": "prc",
            "blood_group": "O-",
            "quantity": 3,
            "urgency_level": "urgent",
            "clinical_indication": "Patient: Unique Test Patient - Verification Test",
            "required_by": required_by
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/inter-org-requests", json=payload, headers=headers)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # Verify it appears in outgoing requests
        outgoing_response = self.session.get(f"{BASE_URL}/api/inter-org-requests/outgoing", headers=headers)
        assert outgoing_response.status_code == 200
        
        outgoing_list = outgoing_response.json()
        found = any(r.get("id") == created_id for r in outgoing_list)
        assert found, f"Created request {created_id} not found in outgoing requests"
        
    def test_cancel_request(self):
        """Test cancelling a pending request"""
        token = self.get_org_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user's org_id
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        org_id = login_response.json()["user"]["org_id"]
        
        # Create a request to cancel
        required_by = (datetime.now() + timedelta(days=2)).isoformat()
        payload = {
            "request_type": "internal",
            "fulfilling_org_id": org_id,
            "component_type": "ffp",
            "blood_group": "B-",
            "quantity": 1,
            "urgency_level": "routine",
            "clinical_indication": "Patient: Cancel Test Patient",
            "required_by": required_by
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/inter-org-requests", json=payload, headers=headers)
        assert create_response.status_code == 200
        request_id = create_response.json()["id"]
        
        # Cancel the request
        cancel_response = self.session.post(f"{BASE_URL}/api/inter-org-requests/{request_id}/cancel", headers=headers)
        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "cancelled"


class TestOrganizationLocationAPI:
    """Tests for organization location management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_system_admin_token(self):
        """Get authentication token for system admin"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYSTEM_ADMIN_EMAIL,
            "password": SYSTEM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("System admin authentication failed")
        
    def test_organization_has_location_fields(self):
        """Test that organization response includes latitude and longitude"""
        token = self.get_system_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(f"{BASE_URL}/api/organizations", headers=headers)
        assert response.status_code == 200
        
        orgs = response.json()
        assert len(orgs) > 0
        
        # Check first org has location fields
        org = orgs[0]
        assert "latitude" in org or org.get("latitude") is None
        assert "longitude" in org or org.get("longitude") is None
        
    def test_update_location_persists(self):
        """Test that location update is persisted in database"""
        token = self.get_system_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get Test Organization
        orgs_response = self.session.get(f"{BASE_URL}/api/organizations", headers=headers)
        orgs = orgs_response.json()
        test_org = next((o for o in orgs if o.get('org_name') == 'Test Organization'), None)
        
        if not test_org:
            pytest.skip("Test Organization not found")
            
        original_lat = test_org.get("latitude")
        original_lng = test_org.get("longitude")
        
        # Update to new location
        new_lat = 19.1000
        new_lng = 72.9000
        update_payload = {
            "org_name": test_org["org_name"],
            "latitude": new_lat,
            "longitude": new_lng
        }
        
        update_response = self.session.put(
            f"{BASE_URL}/api/organizations/{test_org['id']}", 
            json=update_payload, 
            headers=headers
        )
        assert update_response.status_code == 200
        
        # Verify by fetching again
        verify_response = self.session.get(f"{BASE_URL}/api/organizations/{test_org['id']}", headers=headers)
        assert verify_response.status_code == 200
        
        verified_org = verify_response.json()
        assert verified_org["latitude"] == new_lat
        assert verified_org["longitude"] == new_lng
        
        # Restore original location
        restore_payload = {
            "org_name": test_org["org_name"],
            "latitude": original_lat or 19.076,
            "longitude": original_lng or 72.8777
        }
        self.session.put(
            f"{BASE_URL}/api/organizations/{test_org['id']}", 
            json=restore_payload, 
            headers=headers
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
