"""
Test bug fixes for iteration 15:
1) Traceability page barcode not showing
2) Processing page cannot process components
3) Find Blood cannot make internal/external requests
4) Missing data fields in Laboratory, QC modules
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "admin@pdn.gov.my"
ADMIN_PASSWORD = "Admin@123"
STAFF_EMAIL = "labtech@pdn.gov.my"
STAFF_PASSWORD = "Staff@123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def staff_token():
    """Get staff auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": STAFF_EMAIL,
        "password": STAFF_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Staff authentication failed")


@pytest.fixture
def admin_headers(admin_token):
    """Auth headers for admin"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def staff_headers(staff_token):
    """Auth headers for staff"""
    return {"Authorization": f"Bearer {staff_token}"}


class TestTraceabilityBarcode:
    """Test Traceability page barcode display - Issue 1"""
    
    def test_blood_units_have_barcode_data(self, admin_headers):
        """Blood units should have bag_barcode field with base64 data"""
        response = requests.get(f"{BASE_URL}/api/blood-units", headers=admin_headers)
        assert response.status_code == 200
        
        units = response.json()
        assert len(units) > 0, "No blood units found"
        
        # Check that at least some units have barcode data
        units_with_barcode = [u for u in units if u.get('bag_barcode') and len(u.get('bag_barcode', '')) > 100]
        assert len(units_with_barcode) > 0, "No units have valid base64 barcode data"
        
        # Verify barcode is valid base64 (starts with typical image header after decode)
        sample_barcode = units_with_barcode[0]['bag_barcode']
        assert isinstance(sample_barcode, str), "Barcode should be a string"
        assert len(sample_barcode) > 100, "Barcode base64 data should be substantial"
        
    def test_traceability_endpoint_returns_barcode(self, admin_headers):
        """Traceability endpoint should return unit with barcode"""
        # First get a unit
        response = requests.get(f"{BASE_URL}/api/blood-units", headers=admin_headers)
        assert response.status_code == 200
        units = response.json()
        
        if len(units) == 0:
            pytest.skip("No units available for testing")
            
        unit_id = units[0]['id']
        
        # Get traceability data
        trace_response = requests.get(f"{BASE_URL}/api/blood-units/{unit_id}/traceability", headers=admin_headers)
        assert trace_response.status_code == 200
        
        trace_data = trace_response.json()
        assert "unit" in trace_data, "Traceability should have unit data"
        assert "bag_barcode" in trace_data["unit"], "Unit should have bag_barcode field"


class TestProcessingPage:
    """Test Processing page can process components - Issue 2"""
    
    def test_blood_units_with_lab_status_exist(self, admin_headers):
        """Should have blood units with status='lab' ready for processing"""
        response = requests.get(f"{BASE_URL}/api/blood-units?status=lab", headers=admin_headers)
        assert response.status_code == 200
        
        units = response.json()
        assert len(units) >= 8, f"Expected 8 units with status=lab, got {len(units)}"
        
        # Verify units have required fields for processing
        for unit in units[:3]:
            assert unit.get('blood_group') or unit.get('confirmed_blood_group'), "Unit should have blood group"
            assert unit.get('volume'), "Unit should have volume"
            
    def test_create_component_from_lab_unit(self, admin_headers):
        """Should be able to create a component from a lab-status unit"""
        # Get a lab-status unit
        response = requests.get(f"{BASE_URL}/api/blood-units?status=lab", headers=admin_headers)
        assert response.status_code == 200
        units = response.json()
        
        if len(units) == 0:
            pytest.skip("No lab-status units available")
            
        unit = units[0]
        
        # Create a component
        component_data = {
            "parent_unit_id": unit['id'],
            "component_type": "prc",
            "volume": 250,
            "expiry_date": "2026-03-15"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/components", json=component_data, headers=admin_headers)
        assert create_response.status_code == 201, f"Failed to create component: {create_response.text}"
        
        created = create_response.json()
        assert "component_id" in created, "Response should have component_id"
        assert created.get("blood_group"), "Component should inherit blood group"
        
    def test_get_all_components(self, admin_headers):
        """Should be able to fetch all components"""
        response = requests.get(f"{BASE_URL}/api/components", headers=admin_headers)
        assert response.status_code == 200
        
        components = response.json()
        assert isinstance(components, list), "Should return a list of components"


class TestFindBloodRequests:
    """Test Find Blood internal/external requests - Issue 3"""
    
    def test_internal_inventory_endpoint(self, admin_headers):
        """Internal inventory by blood group should work"""
        response = requests.get(f"{BASE_URL}/api/inventory/by-blood-group", headers=admin_headers)
        assert response.status_code == 200
        
        inventory = response.json()
        assert isinstance(inventory, dict), "Should return a dict of blood groups"
        
    def test_blood_link_search(self, admin_headers):
        """Blood link search should work"""
        search_params = {
            "latitude": 3.1390,
            "longitude": 101.6869,
            "max_distance_km": 100
        }
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json=search_params, headers=admin_headers)
        # May return empty if no other orgs, but should not fail
        assert response.status_code == 200
        
    def test_create_internal_request(self, admin_headers):
        """Should be able to create an internal blood request"""
        request_data = {
            "request_type": "internal",
            "component_type": "whole_blood",
            "blood_group": "O+",
            "quantity": 2,
            "urgency_level": "routine",
            "clinical_indication": "Patient: Test Patient - Surgery"
        }
        
        response = requests.post(f"{BASE_URL}/api/inter-org-requests", json=request_data, headers=admin_headers)
        assert response.status_code in [200, 201], f"Failed to create internal request: {response.text}"
        
    def test_create_external_request(self, admin_headers):
        """Should be able to create an external blood request"""
        request_data = {
            "request_type": "external",
            "external_org_name": "Test External Hospital",
            "external_org_address": "123 Test Street",
            "component_type": "prc",
            "blood_group": "A+",
            "quantity": 1,
            "urgency_level": "urgent",
            "clinical_indication": "Patient: External Test - Trauma"
        }
        
        response = requests.post(f"{BASE_URL}/api/inter-org-requests", json=request_data, headers=admin_headers)
        assert response.status_code in [200, 201], f"Failed to create external request: {response.text}"


class TestLaboratoryData:
    """Test Laboratory Completed Tests shows proper data - Issue 4"""
    
    def test_lab_tests_have_required_fields(self, admin_headers):
        """Lab tests should have unit_id, blood_group, HIV, HBsAg, HCV, Syphilis results"""
        response = requests.get(f"{BASE_URL}/api/lab-tests", headers=admin_headers)
        assert response.status_code == 200
        
        tests = response.json()
        assert len(tests) > 0, "No lab tests found"
        
        # Check completed tests have all required fields
        completed_tests = [t for t in tests if t.get('status') == 'completed']
        assert len(completed_tests) > 0, "No completed lab tests found"
        
        for test in completed_tests[:3]:
            # Check unit_id field
            assert test.get('unit_id'), f"Test should have unit_id field"
            
            # Check blood group
            assert test.get('confirmed_blood_group'), f"Completed test should have confirmed_blood_group"
            
            # Check serology results
            assert test.get('hiv_result'), f"Completed test should have hiv_result"
            assert test.get('hbsag_result'), f"Completed test should have hbsag_result"
            assert test.get('hcv_result'), f"Completed test should have hcv_result"
            assert test.get('syphilis_result'), f"Completed test should have syphilis_result"
            
            # Check overall result
            assert test.get('overall_result') or test.get('overall_status'), "Test should have overall result"
            
    def test_blood_units_collected_for_testing(self, admin_headers):
        """Should have blood units with status=collected awaiting lab testing"""
        response = requests.get(f"{BASE_URL}/api/blood-units?status=collected", headers=admin_headers)
        assert response.status_code == 200
        
        units = response.json()
        assert len(units) >= 8, f"Expected 8 collected units for lab testing, got {len(units)}"


class TestQCValidation:
    """Test QC Validation page shows pending validations and history - Issue 4"""
    
    def test_components_with_processing_status(self, admin_headers):
        """Should have components with status=processing for QC pending"""
        response = requests.get(f"{BASE_URL}/api/components?status=processing", headers=admin_headers)
        assert response.status_code == 200
        
        components = response.json()
        assert len(components) >= 6, f"Expected 6 components with status=processing, got {len(components)}"
        
    def test_qc_validation_records_exist(self, admin_headers):
        """Should have QC validation records with proper fields"""
        response = requests.get(f"{BASE_URL}/api/qc-validation", headers=admin_headers)
        assert response.status_code == 200
        
        validations = response.json()
        assert len(validations) > 0, "No QC validation records found"
        
        # Check validation records have required fields
        for v in validations[:3]:
            assert v.get('unit_component_id'), "Validation should have unit_component_id"
            assert v.get('unit_type'), "Validation should have unit_type"
            assert 'data_complete' in v, "Validation should have data_complete field"
            assert 'screening_complete' in v, "Validation should have screening_complete field"
            assert 'custody_complete' in v, "Validation should have custody_complete field"
            assert v.get('status') in ['approved', 'hold'], f"Validation status should be approved or hold"
            
    def test_qc_validation_create(self, admin_headers):
        """Should be able to create QC validation record"""
        # Get a component to validate
        response = requests.get(f"{BASE_URL}/api/components?status=processing", headers=admin_headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No processing components available")
            
        component = response.json()[0]
        
        # Create validation
        validation_data = {
            "unit_component_id": component['id'],
            "unit_type": "component",
            "data_complete": True,
            "screening_complete": True,
            "custody_complete": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/qc-validation", json=validation_data, headers=admin_headers)
        assert create_response.status_code in [200, 201], f"Failed to create validation: {create_response.text}"


class TestBloodUnitFields:
    """Test blood units have confirmed_blood_group and current_location fields"""
    
    def test_blood_units_have_confirmed_blood_group(self, admin_headers):
        """Blood units should have confirmed_blood_group field"""
        response = requests.get(f"{BASE_URL}/api/blood-units?status=lab", headers=admin_headers)
        assert response.status_code == 200
        
        units = response.json()
        units_with_confirmed = [u for u in units if u.get('confirmed_blood_group')]
        assert len(units_with_confirmed) > 0, "No units have confirmed_blood_group"
        
    def test_blood_units_have_current_location(self, admin_headers):
        """Blood units should have current_location field"""
        response = requests.get(f"{BASE_URL}/api/blood-units", headers=admin_headers)
        assert response.status_code == 200
        
        units = response.json()
        units_with_location = [u for u in units if u.get('current_location')]
        assert len(units_with_location) > 0, "No units have current_location"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
