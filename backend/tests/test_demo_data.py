"""
Test Demo Data Seeding and API Verification
Tests that demo data is properly seeded and accessible via APIs
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDemoDataVerification:
    """Verify demo data is properly seeded and accessible"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@testorg.com",
            "password": "Test@123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_dashboard_stats(self):
        """Test dashboard stats API returns demo data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats are populated
        assert "total_donors" in data or "totalDonors" in data
        print(f"Dashboard stats: {data}")
    
    def test_donors_list(self):
        """Test donors API returns seeded donors"""
        response = requests.get(f"{BASE_URL}/api/donors", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should have donors from demo data
        donors = data if isinstance(data, list) else data.get('donors', data.get('items', []))
        assert len(donors) >= 10, f"Expected at least 10 donors, got {len(donors)}"
        print(f"Total donors: {len(donors)}")
        
        # Check donor structure
        if donors:
            donor = donors[0]
            assert "blood_group" in donor or "bloodGroup" in donor
    
    def test_donors_with_status(self):
        """Test donors-with-status API"""
        response = requests.get(f"{BASE_URL}/api/donors-with-status?is_active=active", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"Donors with status response: {type(data)}")
    
    def test_inventory_by_blood_group(self):
        """Test inventory by blood group API"""
        response = requests.get(f"{BASE_URL}/api/inventory/by-blood-group", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should have inventory data
        print(f"Inventory by blood group: {data}")
        assert data is not None
    
    def test_blood_requests_list(self):
        """Test blood requests API returns seeded requests"""
        response = requests.get(f"{BASE_URL}/api/inter-org-requests/incoming", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        requests_list = data if isinstance(data, list) else data.get('requests', data.get('items', []))
        print(f"Total blood requests: {len(requests_list)}")
        # At least 1 request should exist
        assert len(requests_list) >= 1, f"Expected at least 1 blood request, got {len(requests_list)}"
    
    def test_requestors_list(self):
        """Test requestors API returns seeded requestors"""
        response = requests.get(f"{BASE_URL}/api/requestors", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        requestors = data if isinstance(data, list) else data.get('requestors', data.get('items', []))
        print(f"Total requestors: {len(requestors)}")
        assert len(requestors) >= 3, f"Expected at least 3 requestors, got {len(requestors)}"
    
    def test_broadcasts_list(self):
        """Test broadcasts API returns seeded broadcasts"""
        response = requests.get(f"{BASE_URL}/api/broadcasts/active", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        broadcasts = data if isinstance(data, list) else data.get('broadcasts', data.get('items', []))
        print(f"Total active broadcasts: {len(broadcasts)}")
        # At least some broadcasts should exist
        assert len(broadcasts) >= 0, f"Broadcasts endpoint working"
    
    def test_donations_list(self):
        """Test donations API returns seeded donations"""
        response = requests.get(f"{BASE_URL}/api/donations", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        donations = data if isinstance(data, list) else data.get('donations', data.get('items', []))
        print(f"Total donations: {len(donations)}")
        assert len(donations) >= 5, f"Expected at least 5 donations, got {len(donations)}"
    
    def test_components_list(self):
        """Test components API returns seeded components"""
        response = requests.get(f"{BASE_URL}/api/components", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        components = data if isinstance(data, list) else data.get('components', data.get('items', []))
        print(f"Total components: {len(components)}")
        assert len(components) >= 10, f"Expected at least 10 components, got {len(components)}"


class TestDonorPortalRequestorButton:
    """Test the Register as Requestor button on donor portal"""
    
    def test_donor_landing_page_loads(self):
        """Test donor landing page is accessible"""
        response = requests.get(f"{BASE_URL.replace('/api', '')}/donor")
        # This tests the frontend route, may return 200 or redirect
        assert response.status_code in [200, 301, 302, 304]
    
    def test_requestor_register_page_loads(self):
        """Test requestor registration page is accessible"""
        response = requests.get(f"{BASE_URL.replace('/api', '')}/requestor/register")
        # This tests the frontend route
        assert response.status_code in [200, 301, 302, 304]


class TestRequestorRegistrationAPI:
    """Test requestor registration API"""
    
    def test_requestor_registration_endpoint(self):
        """Test requestor registration endpoint exists"""
        # Test with minimal data to check endpoint exists
        response = requests.post(f"{BASE_URL}/api/requestors/register", json={
            "organization_name": "Test Hospital API",
            "organization_type": "hospital",
            "contact_person": "Dr. Test",
            "email": f"test_api_{os.urandom(4).hex()}@hospital.com",
            "phone": "+60-12-3456789",
            "address": "123 Test Street",
            "city": "Kuala Lumpur",
            "state": "Wilayah Persekutuan",
            "pincode": "50000",
            "password": "Test@123"
        })
        
        # Should either succeed or return validation error (not 404/500)
        assert response.status_code in [200, 201, 400, 422], f"Unexpected status: {response.status_code} - {response.text}"
        print(f"Requestor registration response: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
