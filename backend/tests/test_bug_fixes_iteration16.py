"""
Test suite for Bug Fixes Iteration 16
Tests data fix for: Quarantine, Find Blood Internal Inventory, Pre-Lab QC, Returns, Discards
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://bloodlink-lab-fix.preview.emergentagent.com').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pdn.gov.my",
            "password": "Admin@123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@pdn.gov.my"
        return data["token"]


class TestFindBloodInternalInventory:
    """Test Find Blood Internal Inventory (by-blood-group endpoint) - Issue #1"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pdn.gov.my",
            "password": "Admin@123"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_by_blood_group_returns_total_whole_blood_components(self):
        """Test that by-blood-group endpoint returns total, whole_blood, components fields"""
        response = requests.get(f"{BASE_URL}/api/inventory/by-blood-group", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check all blood groups have the expected structure
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        for bg in blood_groups:
            assert bg in data, f"Blood group {bg} missing from response"
            bg_data = data[bg]
            assert "total" in bg_data, f"'total' field missing for {bg}"
            assert "whole_blood" in bg_data, f"'whole_blood' field missing for {bg}"
            assert "components" in bg_data, f"'components' field missing for {bg}"
            # Verify total is the sum of whole_blood and components
            assert bg_data["total"] == bg_data["whole_blood"] + bg_data["components"], \
                f"total != whole_blood + components for {bg}"
    
    def test_inventory_has_data(self):
        """Test that at least some blood groups have inventory"""
        response = requests.get(f"{BASE_URL}/api/inventory/by-blood-group", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check that at least one blood group has units
        total_units = sum(data[bg]["total"] for bg in data)
        assert total_units > 0, "No units found in inventory"


class TestPreLabQCBloodGroup:
    """Test Pre-Lab QC blood group display - Issue #2"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pdn.gov.my",
            "password": "Admin@123"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_pending_units_have_blood_group(self):
        """Test that pending units in Pre-Lab QC have blood_group field populated"""
        response = requests.get(f"{BASE_URL}/api/pre-lab-qc/pending", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check that blood_group is populated for all pending units
        for unit in data:
            assert "blood_group" in unit, f"blood_group field missing for unit {unit.get('unit_id')}"
            # Either blood_group or confirmed_blood_group should be populated
            has_blood_group = unit.get("blood_group") or unit.get("confirmed_blood_group")
            assert has_blood_group is not None, f"No blood group data for unit {unit.get('unit_id')}"
    
    def test_pending_units_have_required_fields(self):
        """Test that pending units have all required display fields"""
        response = requests.get(f"{BASE_URL}/api/pre-lab-qc/pending", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['unit_id', 'blood_group', 'collection_date', 'volume', 'status']
        for unit in data:
            for field in required_fields:
                assert field in unit, f"Missing field '{field}' in unit {unit.get('unit_id')}"


class TestQuarantineManagement:
    """Test Quarantine Management - Issue #3"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pdn.gov.my",
            "password": "Admin@123"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_quarantine_items_have_unit_component_id(self):
        """Test that quarantine items have unit_component_id field"""
        response = requests.get(f"{BASE_URL}/api/quarantine", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for item in data:
            assert "unit_component_id" in item, f"unit_component_id missing for quarantine item {item.get('id')}"
            assert item["unit_component_id"] is not None, f"unit_component_id is null for quarantine item {item.get('id')}"
    
    def test_quarantine_items_have_reason(self):
        """Test that quarantine items have reason field"""
        response = requests.get(f"{BASE_URL}/api/quarantine", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for item in data:
            assert "reason" in item, f"reason missing for quarantine item {item.get('id')}"
            assert item["reason"] is not None, f"reason is null for quarantine item {item.get('id')}"
    
    def test_quarantine_items_have_unit_type(self):
        """Test that quarantine items have unit_type field"""
        response = requests.get(f"{BASE_URL}/api/quarantine", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for item in data:
            assert "unit_type" in item, f"unit_type missing for quarantine item {item.get('id')}"
            assert item["unit_type"] in ["unit", "component"], f"Invalid unit_type for quarantine item {item.get('id')}"
    
    def test_quarantine_items_have_disposition(self):
        """Test that quarantine items have disposition field (can be null)"""
        response = requests.get(f"{BASE_URL}/api/quarantine", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for item in data:
            assert "disposition" in item, f"disposition field missing for quarantine item {item.get('id')}"


class TestReturnsManagement:
    """Test Returns Management - Issue #4"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pdn.gov.my",
            "password": "Admin@123"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_returns_have_source_field(self):
        """Test that returns have source field"""
        response = requests.get(f"{BASE_URL}/api/returns", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for ret in data:
            assert "source" in ret, f"source field missing for return {ret.get('return_id')}"
            assert ret["source"] is not None, f"source is null for return {ret.get('return_id')}"
    
    def test_returns_have_hospital_name_field(self):
        """Test that returns have hospital_name field"""
        response = requests.get(f"{BASE_URL}/api/returns", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for ret in data:
            assert "hospital_name" in ret, f"hospital_name field missing for return {ret.get('return_id')}"
    
    def test_returns_have_reason_field(self):
        """Test that returns have reason field"""
        response = requests.get(f"{BASE_URL}/api/returns", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for ret in data:
            assert "reason" in ret, f"reason field missing for return {ret.get('return_id')}"
            assert ret["reason"] is not None, f"reason is null for return {ret.get('return_id')}"
    
    def test_returns_have_qc_pass_field(self):
        """Test that returns have qc_pass field"""
        response = requests.get(f"{BASE_URL}/api/returns", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for ret in data:
            assert "qc_pass" in ret, f"qc_pass field missing for return {ret.get('return_id')}"
    
    def test_returns_have_decision_field(self):
        """Test that returns have decision field"""
        response = requests.get(f"{BASE_URL}/api/returns", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for ret in data:
            assert "decision" in ret, f"decision field missing for return {ret.get('return_id')}"
    
    def test_returns_have_storage_location_field(self):
        """Test that returns have storage_location field"""
        response = requests.get(f"{BASE_URL}/api/returns", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for ret in data:
            assert "storage_location" in ret or "storage_location_id" in ret, \
                f"storage_location field missing for return {ret.get('return_id')}"


class TestDiscardsManagement:
    """Test Discards Management - Issue #5"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@pdn.gov.my",
            "password": "Admin@123"
        })
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_discards_have_reason_field(self):
        """Test that discards have reason field with valid enum values"""
        response = requests.get(f"{BASE_URL}/api/discards", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        valid_reasons = ['expired', 'failed_qc', 'rejected_return', 'reactive', 'damaged', 'other']
        for disc in data:
            assert "reason" in disc, f"reason field missing for discard {disc.get('discard_id')}"
            assert disc["reason"] is not None, f"reason is null for discard {disc.get('discard_id')}"
            assert disc["reason"] in valid_reasons, \
                f"Invalid reason '{disc['reason']}' for discard {disc.get('discard_id')}"
    
    def test_discards_have_destruction_date_field(self):
        """Test that discards have destruction_date field"""
        response = requests.get(f"{BASE_URL}/api/discards", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for disc in data:
            assert "destruction_date" in disc, f"destruction_date field missing for discard {disc.get('discard_id')}"
    
    def test_discards_have_discard_date_field(self):
        """Test that discards have discard_date field"""
        response = requests.get(f"{BASE_URL}/api/discards", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for disc in data:
            assert "discard_date" in disc, f"discard_date field missing for discard {disc.get('discard_id')}"
            assert disc["discard_date"] is not None, f"discard_date is null for discard {disc.get('discard_id')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
