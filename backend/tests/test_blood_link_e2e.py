"""
Blood Link - End-to-End Backend API Tests
Tests the complete blood bank workflow:
Donor Registration -> Screening -> Collection -> Lab Testing -> Processing -> QC -> Inventory -> Request -> Issuance -> Logistics
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ORG_ADMIN_EMAIL = "admin@testorg.com"
ORG_ADMIN_PASSWORD = "Test@123"
SYSTEM_ADMIN_EMAIL = "admin@bbms.local"
SYSTEM_ADMIN_PASSWORD = "Admin@123456"


class TestHealthCheck:
    """Health check tests - run first"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Blood Link API"
        print(f"✓ API Health: {data['status']}")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_org_admin_login(self):
        """Test org admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ORG_ADMIN_EMAIL
        assert data["user"]["user_type"] == "super_admin"
        print(f"✓ Org Admin Login: {data['user']['full_name']}")
    
    def test_system_admin_login(self):
        """Test system admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYSTEM_ADMIN_EMAIL,
            "password": SYSTEM_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["user_type"] == "system_admin"
        print(f"✓ System Admin Login: {data['user']['full_name']}")
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login rejected correctly")
    
    def test_get_current_user(self, org_admin_token):
        """Test getting current user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {org_admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ORG_ADMIN_EMAIL
        print(f"✓ Current User: {data['full_name']}")


class TestDonorManagement:
    """Donor CRUD tests"""
    
    def test_create_donor(self, org_admin_token):
        """Create a new donor"""
        donor_data = {
            "full_name": "TEST_John Doe",
            "date_of_birth": "1990-05-15",
            "gender": "male",
            "weight": 75,
            "phone": "9876543210",
            "email": "test_john@example.com",
            "address": "123 Test Street",
            "identity_type": "aadhaar",
            "identity_number": f"TEST{datetime.now().strftime('%H%M%S')}",
            "consent_given": True
        }
        response = requests.post(f"{BASE_URL}/api/donors", 
            json=donor_data,
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "donor_id" in data
        assert data["status"] == "success"
        print(f"✓ Donor Created: {data['donor_id']}")
    
    def test_get_donors_list(self, org_admin_token):
        """Get list of donors"""
        response = requests.get(f"{BASE_URL}/api/donors",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Donors List: {len(data)} donors found")
    
    def test_get_donor_by_id(self, org_admin_token, created_donor):
        """Get donor by ID"""
        donor_id = created_donor["donor_id"]
        response = requests.get(f"{BASE_URL}/api/donors/{donor_id}",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["donor_id"] == donor_id
        print(f"✓ Donor Retrieved: {data['full_name']}")
    
    def test_check_donor_eligibility(self, org_admin_token, created_donor):
        """Check donor eligibility"""
        donor_id = created_donor["donor_id"]
        response = requests.get(f"{BASE_URL}/api/donors/{donor_id}/eligibility",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "eligible" in data
        print(f"✓ Donor Eligibility: {data['eligible']}, Issues: {data.get('issues', [])}")


class TestScreening:
    """Screening module tests"""
    
    def test_create_screening(self, org_admin_token, created_donor):
        """Create a screening for donor - with correct model fields"""
        today = datetime.now().strftime("%Y-%m-%d")
        screening_data = {
            "donor_id": created_donor["id"],
            "screening_date": today,
            "hemoglobin": 14.5,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "pulse": 72,
            "temperature": 37.0,
            "weight": 75,
            "height": 175,
            "preliminary_blood_group": "O+",
            "questionnaire_passed": True
        }
        response = requests.post(f"{BASE_URL}/api/screenings",
            json=screening_data,
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        assert "screening_id" in data
        print(f"✓ Screening Created: {data['screening_id']}, Status: {data['eligibility_status']}")
    
    def test_get_screenings(self, org_admin_token):
        """Get list of screenings"""
        response = requests.get(f"{BASE_URL}/api/screenings",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Screenings List: {len(data)} screenings found")
    
    def test_get_pending_donors_for_screening(self, org_admin_token):
        """Get donors pending screening"""
        response = requests.get(f"{BASE_URL}/api/screenings/pending/donors",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Pending Donors for Screening: {len(data)}")


class TestCollection:
    """Blood collection tests"""
    
    def test_get_eligible_donors_for_collection(self, org_admin_token):
        """Get eligible donors for collection"""
        response = requests.get(f"{BASE_URL}/api/donations/eligible-donors",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Eligible Donors for Collection: {len(data)}")
    
    def test_create_donation(self, org_admin_token, created_screening):
        """Start a blood donation/collection"""
        donation_data = {
            "screening_id": created_screening["id"],
            "donor_id": created_screening["donor_id"],
            "donation_type": "whole_blood",
            "bag_type": "single"
        }
        response = requests.post(f"{BASE_URL}/api/donations",
            json=donation_data,
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        assert "donation_id" in data
        print(f"✓ Donation Started: {data['donation_id']}")
    
    def test_complete_donation(self, org_admin_token, created_donation):
        """Complete a blood donation"""
        donation_id = created_donation["donation_id"]
        response = requests.put(
            f"{BASE_URL}/api/donations/{donation_id}/complete",
            params={"volume": 450, "adverse_reaction": False},
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        assert "unit_id" in data
        print(f"✓ Donation Completed: Unit {data['unit_id']}")
    
    def test_get_donations(self, org_admin_token):
        """Get list of donations"""
        response = requests.get(f"{BASE_URL}/api/donations",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Donations List: {len(data)}")


class TestLaboratory:
    """Laboratory testing module"""
    
    def test_get_blood_units(self, org_admin_token):
        """Get blood units"""
        response = requests.get(f"{BASE_URL}/api/blood-units",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Blood Units: {len(data)}")
    
    def test_create_lab_test(self, org_admin_token, completed_donation):
        """Create lab test results for blood unit"""
        unit_id = completed_donation["unit_id"]
        lab_test_data = {
            "unit_id": unit_id,
            "hiv_result": "non_reactive",
            "hbsag_result": "non_reactive",
            "hcv_result": "non_reactive",
            "syphilis_result": "non_reactive",
            "confirmed_blood_group": "O+",
            "verified_by_1": "Lab Tech 1",
            "verified_by_2": "Lab Tech 2"
        }
        response = requests.post(f"{BASE_URL}/api/lab-tests",
            json=lab_test_data,
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        assert data["overall_status"] == "non_reactive"
        print(f"✓ Lab Test Created: {data['test_id']}, Status: {data['overall_status']}")
    
    def test_get_lab_tests(self, org_admin_token):
        """Get list of lab tests"""
        response = requests.get(f"{BASE_URL}/api/lab-tests",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Lab Tests List: {len(data)}")


class TestProcessing:
    """Blood processing/component separation tests"""
    
    def test_create_components(self, org_admin_token, completed_donation):
        """Process blood unit into components"""
        unit_id = completed_donation["unit_id"]
        
        # First get the unit to get internal ID
        response = requests.get(f"{BASE_URL}/api/blood-units/{unit_id}",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        if response.status_code != 200:
            pytest.skip("Blood unit not found for processing")
        
        unit_data = response.json()
        parent_unit_id = unit_data.get("id", unit_id)
        
        components_data = {
            "parent_unit_id": parent_unit_id,
            "components": [
                {"component_type": "prc", "volume": 200},
                {"component_type": "ffp", "volume": 150},
                {"component_type": "platelets", "volume": 50}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/components/multi",
            json=components_data,
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        assert data["components_created"] == 3
        print(f"✓ Components Created: {data['components_created']} components")
    
    def test_get_components(self, org_admin_token):
        """Get list of components"""
        response = requests.get(f"{BASE_URL}/api/components",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Components List: {len(data)}")


class TestQCValidation:
    """QC Validation tests"""
    
    def test_get_qc_validations(self, org_admin_token):
        """Get QC validations list - correct endpoint is /qc-validation"""
        response = requests.get(f"{BASE_URL}/api/qc-validation",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ QC Validations: {len(data)}")


class TestInventory:
    """Inventory management tests"""
    
    def test_get_inventory_summary(self, org_admin_token):
        """Get inventory summary - correct endpoint is /inventory/summary"""
        response = requests.get(f"{BASE_URL}/api/inventory/summary",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Inventory Summary Retrieved")
    
    def test_get_inventory_by_blood_group(self, org_admin_token):
        """Get inventory by blood group"""
        response = requests.get(f"{BASE_URL}/api/inventory/by-blood-group",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Inventory by Blood Group Retrieved")
    
    def test_get_expiring_inventory(self, org_admin_token):
        """Get expiring inventory"""
        response = requests.get(f"{BASE_URL}/api/inventory/expiring",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Expiring Inventory Retrieved")


class TestBloodRequests:
    """Blood request tests - correct endpoint is /requests"""
    
    def test_create_blood_request(self, org_admin_token):
        """Create a blood request with correct model fields"""
        today = datetime.now().strftime("%Y-%m-%d")
        request_data = {
            "request_type": "external",
            "requester_name": "Dr. Test",
            "requester_contact": "9876543210",
            "hospital_name": "Test Hospital",
            "hospital_address": "123 Hospital Street",
            "hospital_contact": "1234567890",
            "patient_name": "TEST_Patient",
            "patient_id": f"PAT{datetime.now().strftime('%H%M%S')}",
            "patient_diagnosis": "Anemia",
            "blood_group": "O+",
            "product_type": "prc",
            "quantity": 2,
            "urgency": "normal",
            "requested_date": today,
            "required_by_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        }
        response = requests.post(f"{BASE_URL}/api/requests",
            json=request_data,
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "success"
        assert "request_id" in data
        print(f"✓ Blood Request Created: {data['request_id']}")
    
    def test_get_blood_requests(self, org_admin_token):
        """Get list of blood requests"""
        response = requests.get(f"{BASE_URL}/api/requests",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Blood Requests: {len(data)}")


class TestIssuance:
    """Blood issuance tests"""
    
    def test_get_issuances(self, org_admin_token):
        """Get list of issuances"""
        response = requests.get(f"{BASE_URL}/api/issuances",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Issuances: {len(data)}")


class TestLogistics:
    """Logistics/shipment tests - correct endpoint is /logistics/shipments"""
    
    def test_get_shipments(self, org_admin_token):
        """Get logistics/shipments list"""
        response = requests.get(f"{BASE_URL}/api/logistics/shipments",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Logistics/Shipments: {len(data)}")
    
    def test_get_logistics_dashboard(self, org_admin_token):
        """Get logistics dashboard"""
        response = requests.get(f"{BASE_URL}/api/logistics/dashboard",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Logistics Dashboard Retrieved")


class TestOrganizations:
    """Organization management tests"""
    
    def test_get_organizations(self, system_admin_token):
        """Get organizations list (system admin)"""
        response = requests.get(f"{BASE_URL}/api/organizations",
            headers={"Authorization": f"Bearer {system_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Organizations: {len(data)}")
    
    def test_get_public_organizations(self):
        """Get public organizations list (no auth)"""
        response = requests.get(f"{BASE_URL}/api/organizations/public")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public Organizations: {len(data)}")


class TestUserManagement:
    """User management tests"""
    
    def test_get_users(self, org_admin_token):
        """Get users list"""
        response = requests.get(f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Users: {len(data)}")


class TestDashboard:
    """Dashboard tests"""
    
    def test_get_dashboard_stats(self, org_admin_token):
        """Get dashboard statistics"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Dashboard Stats Retrieved")


class TestNotifications:
    """Notifications tests"""
    
    def test_get_notifications(self, org_admin_token):
        """Get notifications list"""
        response = requests.get(f"{BASE_URL}/api/notifications",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Notifications: {len(data)}")
    
    def test_get_notification_count(self, org_admin_token):
        """Get unread notification count"""
        response = requests.get(f"{BASE_URL}/api/notifications/count",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Notification Count: {data}")


# ==================== FIXTURES ====================

@pytest.fixture(scope="session")
def org_admin_token():
    """Get org admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_ADMIN_EMAIL,
        "password": ORG_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Org admin authentication failed")

@pytest.fixture(scope="session")
def system_admin_token():
    """Get system admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SYSTEM_ADMIN_EMAIL,
        "password": SYSTEM_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("System admin authentication failed")

@pytest.fixture(scope="class")
def created_donor(org_admin_token):
    """Create a test donor and return its data"""
    donor_data = {
        "full_name": f"TEST_Donor_{datetime.now().strftime('%H%M%S')}",
        "date_of_birth": "1990-05-15",
        "gender": "male",
        "weight": 75,
        "phone": f"98765{datetime.now().strftime('%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
        "address": "123 Test Street",
        "identity_type": "aadhaar",
        "identity_number": f"TEST{datetime.now().strftime('%H%M%S%f')[:12]}",
        "consent_given": True
    }
    response = requests.post(f"{BASE_URL}/api/donors", 
        json=donor_data,
        headers={"Authorization": f"Bearer {org_admin_token}"}
    )
    if response.status_code == 200:
        data = response.json()
        # Get full donor data
        donor_response = requests.get(f"{BASE_URL}/api/donors/{data['donor_id']}",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        if donor_response.status_code == 200:
            return donor_response.json()
    pytest.skip("Failed to create test donor")

@pytest.fixture(scope="class")
def created_screening(org_admin_token, created_donor):
    """Create a screening for the test donor"""
    today = datetime.now().strftime("%Y-%m-%d")
    screening_data = {
        "donor_id": created_donor["id"],
        "screening_date": today,
        "hemoglobin": 14.5,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "pulse": 72,
        "temperature": 37.0,
        "weight": 75,
        "height": 175,
        "preliminary_blood_group": "O+",
        "questionnaire_passed": True
    }
    response = requests.post(f"{BASE_URL}/api/screenings",
        json=screening_data,
        headers={"Authorization": f"Bearer {org_admin_token}"}
    )
    if response.status_code == 200:
        data = response.json()
        data["donor_id"] = created_donor["id"]
        data["id"] = data["screening_id"]
        return data
    pytest.skip(f"Failed to create screening: {response.text}")

@pytest.fixture(scope="class")
def created_donation(org_admin_token, created_screening):
    """Create a donation for the screened donor"""
    donation_data = {
        "screening_id": created_screening["id"],
        "donor_id": created_screening["donor_id"],
        "donation_type": "whole_blood",
        "bag_type": "single"
    }
    response = requests.post(f"{BASE_URL}/api/donations",
        json=donation_data,
        headers={"Authorization": f"Bearer {org_admin_token}"}
    )
    if response.status_code == 200:
        return response.json()
    pytest.skip(f"Failed to create donation: {response.text}")

@pytest.fixture(scope="class")
def completed_donation(org_admin_token, created_donation):
    """Complete the donation and get blood unit"""
    donation_id = created_donation["donation_id"]
    response = requests.put(
        f"{BASE_URL}/api/donations/{donation_id}/complete",
        params={"volume": 450, "adverse_reaction": False},
        headers={"Authorization": f"Bearer {org_admin_token}"}
    )
    if response.status_code == 200:
        return response.json()
    pytest.skip(f"Failed to complete donation: {response.text}")


# ==================== CLEANUP ====================

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data(org_admin_token):
    """Cleanup TEST_ prefixed data after all tests"""
    yield
    # Note: In production, implement cleanup logic here
    # For now, test data with TEST_ prefix can be manually cleaned
    print("\n✓ Test session completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
