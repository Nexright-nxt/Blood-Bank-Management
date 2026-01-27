"""
Blood Link Search Feature - Backend API Tests
Tests the Blood Link (Nearby Geo-Availability) feature endpoints:
- POST /api/blood-link/search - Search nearby blood banks
- GET /api/blood-link/blood-groups - Get blood group summary
- GET /api/blood-link/availability/{org_id} - Get specific blood bank availability
- GET /api/blood-link/emergency-contacts - Get 24x7 blood banks
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test coordinates (Test Organization location)
TEST_LAT = 19.076
TEST_LON = 72.8777


class TestBloodLinkSearch:
    """Blood Link Search API tests"""
    
    def test_search_nearby_blood_banks_basic(self):
        """Test basic search with coordinates only"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "max_distance_km": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "search_location" in data
        assert "filters" in data
        assert "results_count" in data
        assert "blood_banks" in data
        
        # Verify search location
        assert data["search_location"]["latitude"] == TEST_LAT
        assert data["search_location"]["longitude"] == TEST_LON
        
        # Verify filters
        assert data["filters"]["max_distance_km"] == 50
        
        # Verify results
        assert data["results_count"] >= 1
        assert len(data["blood_banks"]) >= 1
        print(f"✓ Basic search: Found {data['results_count']} blood banks")
    
    def test_search_returns_blood_bank_details(self):
        """Test that search returns complete blood bank details"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "max_distance_km": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["blood_banks"]) >= 1
        bank = data["blood_banks"][0]
        
        # Verify blood bank structure
        assert "org_id" in bank
        assert "org_name" in bank
        assert "address" in bank
        assert "city" in bank
        assert "state" in bank
        assert "latitude" in bank
        assert "longitude" in bank
        assert "distance_km" in bank
        assert "availability" in bank
        assert "total_units" in bank
        
        # Verify Test Organization
        assert bank["org_name"] == "Test Organization"
        assert bank["distance_km"] == 0.0  # Same location
        assert bank["total_units"] >= 4  # 4 demo units
        print(f"✓ Blood bank details: {bank['org_name']} with {bank['total_units']} units")
    
    def test_search_with_blood_group_filter(self):
        """Test search with blood group filter"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "blood_group": "A+",
            "max_distance_km": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify filter applied
        assert data["filters"]["blood_group"] == "A+"
        
        # Verify results contain only A+ blood
        if data["results_count"] > 0:
            for bank in data["blood_banks"]:
                assert "A+" in bank["availability"]
        print(f"✓ Blood group filter (A+): Found {data['results_count']} blood banks")
    
    def test_search_with_nonexistent_blood_group(self):
        """Test search with blood group that has no stock"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "blood_group": "O+",  # No O+ in test data
            "max_distance_km": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty results
        assert data["results_count"] == 0
        assert len(data["blood_banks"]) == 0
        print("✓ Non-existent blood group filter: Returns empty results")
    
    def test_search_with_component_type_filter(self):
        """Test search with component type filter"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "component_type": "whole_blood",
            "max_distance_km": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify filter applied
        assert data["filters"]["component_type"] == "whole_blood"
        
        # Verify results contain whole blood
        if data["results_count"] > 0:
            for bank in data["blood_banks"]:
                for bg, components in bank["availability"].items():
                    assert "whole_blood" in components
        print(f"✓ Component type filter (whole_blood): Found {data['results_count']} blood banks")
    
    def test_search_with_distance_filter(self):
        """Test search with different distance radius"""
        # Search with very small radius
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "max_distance_km": 1  # 1km radius
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should find Test Organization (0km away)
        assert data["results_count"] >= 1
        
        # All results should be within 1km
        for bank in data["blood_banks"]:
            assert bank["distance_km"] <= 1
        print(f"✓ Distance filter (1km): Found {data['results_count']} blood banks")
    
    def test_search_with_min_units_filter(self):
        """Test search with minimum units filter"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "min_units": 4,
            "max_distance_km": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # All results should have at least 4 units
        for bank in data["blood_banks"]:
            assert bank["total_units"] >= 4
        print(f"✓ Min units filter (4): Found {data['results_count']} blood banks")
    
    def test_search_with_high_min_units(self):
        """Test search with high minimum units (should return empty)"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "min_units": 100,  # Very high
            "max_distance_km": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty results
        assert data["results_count"] == 0
        print("✓ High min units filter: Returns empty results")
    
    def test_search_far_location(self):
        """Test search from a far location"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": 28.6139,  # Delhi coordinates
            "longitude": 77.2090,
            "max_distance_km": 50  # 50km radius
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty (Test Organization is in Mumbai)
        assert data["results_count"] == 0
        print("✓ Far location search: Returns empty results")
    
    def test_search_invalid_coordinates(self):
        """Test search with invalid coordinates"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": "invalid",
            "longitude": TEST_LON,
            "max_distance_km": 50
        })
        assert response.status_code == 422  # Validation error
        print("✓ Invalid coordinates: Returns 422 validation error")
    
    def test_search_missing_coordinates(self):
        """Test search with missing coordinates"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "max_distance_km": 50
        })
        assert response.status_code == 422  # Validation error
        print("✓ Missing coordinates: Returns 422 validation error")


class TestBloodGroupsSummary:
    """Blood Groups Summary API tests"""
    
    def test_get_blood_groups_summary(self):
        """Test getting blood groups summary"""
        response = requests.get(f"{BASE_URL}/api/blood-link/blood-groups")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all blood groups present
        expected_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for bg in expected_groups:
            assert bg in data
            assert "whole_blood" in data[bg]
            assert "components" in data[bg]
            assert "total" in data[bg]
            assert "blood_banks_with_stock" in data[bg]
        
        # Verify test data blood groups have stock
        assert data["A+"]["total"] >= 1
        assert data["A-"]["total"] >= 1
        assert data["B+"]["total"] >= 1
        assert data["B-"]["total"] >= 1
        print(f"✓ Blood groups summary: A+={data['A+']['total']}, A-={data['A-']['total']}, B+={data['B+']['total']}, B-={data['B-']['total']}")


class TestBloodBankAvailability:
    """Blood Bank Availability API tests"""
    
    def test_get_availability_valid_org(self):
        """Test getting availability for valid organization"""
        # First get org_id from search
        search_response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "max_distance_km": 50
        })
        assert search_response.status_code == 200
        search_data = search_response.json()
        
        if search_data["results_count"] > 0:
            org_id = search_data["blood_banks"][0]["org_id"]
            
            # Get availability
            response = requests.get(f"{BASE_URL}/api/blood-link/availability/{org_id}")
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert data["org_id"] == org_id
            assert "org_name" in data
            assert "availability" in data
            assert "total_units" in data
            assert "expiring_within_7_days" in data
            assert "last_updated" in data
            print(f"✓ Availability for {data['org_name']}: {data['total_units']} units")
        else:
            pytest.skip("No blood banks found for availability test")
    
    def test_get_availability_invalid_org(self):
        """Test getting availability for invalid organization"""
        response = requests.get(f"{BASE_URL}/api/blood-link/availability/invalid-org-id")
        assert response.status_code == 404
        print("✓ Invalid org availability: Returns 404")


class TestEmergencyContacts:
    """Emergency Contacts API tests"""
    
    def test_get_emergency_contacts(self):
        """Test getting 24x7 emergency blood bank contacts"""
        response = requests.get(f"{BASE_URL}/api/blood-link/emergency-contacts")
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        # If there are 24x7 blood banks, verify structure
        for contact in data:
            assert "org_name" in contact
            assert "total_units_available" in contact
        print(f"✓ Emergency contacts: Found {len(data)} 24x7 blood banks")


class TestHaversineDistance:
    """Test distance calculation accuracy"""
    
    def test_distance_same_location(self):
        """Test distance is 0 for same location"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "max_distance_km": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # Test Organization should be at 0km
        if data["results_count"] > 0:
            bank = data["blood_banks"][0]
            assert bank["distance_km"] == 0.0
            print("✓ Same location distance: 0 km")
    
    def test_distance_sorted_by_proximity(self):
        """Test results are sorted by distance"""
        response = requests.post(f"{BASE_URL}/api/blood-link/search", json={
            "latitude": TEST_LAT,
            "longitude": TEST_LON,
            "max_distance_km": 500  # Large radius
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify sorted by distance
        if len(data["blood_banks"]) > 1:
            distances = [bank["distance_km"] for bank in data["blood_banks"]]
            assert distances == sorted(distances)
            print(f"✓ Results sorted by distance: {distances}")
        else:
            print("✓ Only one result, sorting verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
