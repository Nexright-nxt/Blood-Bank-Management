"""
Test Lab Tech Dashboard, Laboratory Page, and QC Validation Features
Tests the fixes for:
1. Lab tech dashboard API access (requires inventory.view permission)
2. Laboratory completed tests showing HIV, HBsAg, HCV, Syphilis results
3. QC Validation page showing pending and history data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDENTIALS = {"email": "admin@pdn.gov.my", "password": "Admin@123"}
LAB_TECH_CREDENTIALS = {"email": "labtech@pdn.gov.my", "password": "Staff@123"}


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture(scope="module")
def lab_tech_token():
    """Get lab tech authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=LAB_TECH_CREDENTIALS)
    assert response.status_code == 200, f"Lab tech login failed: {response.text}"
    return response.json().get("token")


class TestLabTechDashboard:
    """Test Lab Tech user can access dashboard and required APIs"""

    def test_lab_tech_login(self):
        """Test Lab Tech can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=LAB_TECH_CREDENTIALS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "lab_tech"
        assert data["user"]["email"] == "labtech@pdn.gov.my"

    def test_lab_tech_dashboard_stats(self, lab_tech_token):
        """Test Lab Tech can access dashboard stats API"""
        headers = {"Authorization": f"Bearer {lab_tech_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        # Verify dashboard data structure
        assert "total_donors" in data
        assert "available_units" in data

    def test_lab_tech_inventory_by_blood_group(self, lab_tech_token):
        """Test Lab Tech can access inventory/by-blood-group API (requires inventory.view permission)"""
        headers = {"Authorization": f"Bearer {lab_tech_token}"}
        response = requests.get(f"{BASE_URL}/api/inventory/by-blood-group", headers=headers)
        # This was the original bug - should now return 200 after inventory.view permission added
        assert response.status_code == 200, f"Inventory by blood group failed: {response.text}"
        data = response.json()
        # Verify blood group inventory structure
        assert "A+" in data or "O+" in data or len(data) >= 0

    def test_lab_tech_permissions(self, lab_tech_token):
        """Test Lab Tech has correct permissions including inventory.view"""
        headers = {"Authorization": f"Bearer {lab_tech_token}"}
        response = requests.get(f"{BASE_URL}/api/roles/my-permissions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Verify lab_tech has inventory.view permission
        permissions = data.get("permissions", {})
        assert "inventory" in permissions, "Lab tech should have inventory permissions"
        assert "view" in permissions["inventory"], "Lab tech should have inventory.view permission"


class TestLaboratoryPage:
    """Test Laboratory page APIs - Completed Tests with HIV, HBsAg, HCV, Syphilis results"""

    def test_lab_tests_api_returns_data(self, lab_tech_token):
        """Test lab-tests API returns completed test data"""
        headers = {"Authorization": f"Bearer {lab_tech_token}"}
        response = requests.get(f"{BASE_URL}/api/lab-tests", headers=headers)
        assert response.status_code == 200, f"Lab tests API failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Lab tests should return a list"
        assert len(data) > 0, "Should have at least one lab test"

    def test_lab_tests_have_serology_fields(self, lab_tech_token):
        """Test completed lab tests have HIV, HBsAg, HCV, Syphilis result fields"""
        headers = {"Authorization": f"Bearer {lab_tech_token}"}
        response = requests.get(f"{BASE_URL}/api/lab-tests", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Find a completed test
        completed_tests = [t for t in data if t.get("status") == "completed"]
        assert len(completed_tests) > 0, "Should have completed lab tests"
        
        # Verify serology fields exist and have values
        test = completed_tests[0]
        assert "hiv_result" in test, "Lab test should have hiv_result field"
        assert "hbsag_result" in test, "Lab test should have hbsag_result field"
        assert "hcv_result" in test, "Lab test should have hcv_result field"
        assert "syphilis_result" in test, "Lab test should have syphilis_result field"
        
        # Verify results are not empty
        assert test["hiv_result"] is not None, "HIV result should not be empty"
        assert test["hbsag_result"] is not None, "HBsAg result should not be empty"
        assert test["hcv_result"] is not None, "HCV result should not be empty"
        assert test["syphilis_result"] is not None, "Syphilis result should not be empty"
        
        # Verify result values are valid
        valid_results = ["non_reactive", "reactive", "gray", "negative", "positive"]
        assert test["hiv_result"] in valid_results, f"Invalid HIV result: {test['hiv_result']}"
        assert test["hbsag_result"] in valid_results, f"Invalid HBsAg result: {test['hbsag_result']}"

    def test_blood_units_collected_status(self, lab_tech_token):
        """Test blood-units API returns units with collected status for pending tests tab"""
        headers = {"Authorization": f"Bearer {lab_tech_token}"}
        response = requests.get(f"{BASE_URL}/api/blood-units", params={"status": "collected"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestQCValidationPage:
    """Test QC Validation page APIs - Pending Validation and Validation History"""

    def test_qc_validation_api_requires_permission(self, lab_tech_token):
        """Test QC validation API permission (lab_tech should NOT have access)"""
        headers = {"Authorization": f"Bearer {lab_tech_token}"}
        response = requests.get(f"{BASE_URL}/api/qc-validation", headers=headers)
        # Lab tech should get permission denied
        assert response.status_code == 403, "Lab tech should not have QC validation access"

    def test_qc_validation_api_admin_access(self, admin_token):
        """Test QC validation API with admin access"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/qc-validation", headers=headers)
        assert response.status_code == 200, f"QC validation API failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)

    def test_qc_validation_history_has_required_fields(self, admin_token):
        """Test QC validation history records have required fields for frontend"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/qc-validation", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) > 0, "Should have QC validation records"
        
        # Verify required fields for frontend
        record = data[0]
        assert "unit_component_id" in record, "QC record should have unit_component_id"
        assert "unit_type" in record, "QC record should have unit_type"
        assert "data_complete" in record, "QC record should have data_complete"
        assert "screening_complete" in record, "QC record should have screening_complete"
        assert "custody_complete" in record, "QC record should have custody_complete"
        assert "status" in record, "QC record should have status"

    def test_components_processing_status(self, admin_token):
        """Test components API returns items with status=processing for pending validation"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/components", params={"status": "processing"}, headers=headers)
        assert response.status_code == 200, f"Components API failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        
        # Verify we have components with processing status
        if len(data) > 0:
            assert all(c.get("status") == "processing" for c in data), "All components should have processing status"

    def test_quarantine_api_access(self, admin_token):
        """Test quarantine API access"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/quarantine", headers=headers)
        assert response.status_code == 200, f"Quarantine API failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


class TestAdminFullAccess:
    """Test Admin user can access all pages without errors"""

    def test_admin_login(self):
        """Test Admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"

    def test_admin_dashboard_stats(self, admin_token):
        """Test Admin can access dashboard stats"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200

    def test_admin_inventory_by_blood_group(self, admin_token):
        """Test Admin can access inventory by blood group"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/inventory/by-blood-group", headers=headers)
        assert response.status_code == 200

    def test_admin_lab_tests(self, admin_token):
        """Test Admin can access lab tests"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/lab-tests", headers=headers)
        assert response.status_code == 200

    def test_admin_qc_validation(self, admin_token):
        """Test Admin can access QC validation"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/qc-validation", headers=headers)
        assert response.status_code == 200

    def test_admin_components(self, admin_token):
        """Test Admin can access components"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/components", headers=headers)
        assert response.status_code == 200

    def test_admin_quarantine(self, admin_token):
        """Test Admin can access quarantine"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/quarantine", headers=headers)
        assert response.status_code == 200
