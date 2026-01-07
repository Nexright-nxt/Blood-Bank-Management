"""
Phase F: Document Management API Tests
Tests document upload, list, download, verify, delete, and stats endpoints.
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_ORG_ID = "61d41b01-1b7d-4064-9cff-3fa8a0fd554b"

# Test credentials
SYSTEM_ADMIN = {"email": "admin@bloodbank.com", "password": "adminpassword"}
SUPER_ADMIN = {"email": "superadmin@bloodlink.com", "password": "superadmin123", "org_id": TEST_ORG_ID}


class TestDocumentManagement:
    """Document Management API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.uploaded_doc_ids = []
        yield
        # Cleanup: Delete test documents
        for doc_id in self.uploaded_doc_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/{doc_id}")
            except:
                pass
    
    def get_auth_token(self, credentials, org_id=None):
        """Get authentication token"""
        payload = {"email": credentials["email"], "password": credentials["password"]}
        if org_id:
            payload["org_id"] = org_id
        response = self.session.post(f"{BASE_URL}/api/auth/login", json=payload)
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return token
        return None
    
    # ==================== Authentication Tests ====================
    
    def test_01_system_admin_login(self):
        """Test System Admin can login"""
        token = self.get_auth_token(SYSTEM_ADMIN)
        assert token is not None, "System Admin login failed"
        print("✓ System Admin login successful")
    
    def test_02_super_admin_login(self):
        """Test Super Admin can login with org"""
        token = self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        assert token is not None, "Super Admin login failed"
        print("✓ Super Admin login successful")
    
    # ==================== Document Stats API Tests ====================
    
    def test_03_get_document_stats_empty(self):
        """Test GET /api/documents/{org_id}/summary/stats returns stats"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        response = self.session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/summary/stats")
        
        assert response.status_code == 200, f"Stats API failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify stats structure
        assert "total" in data, "Missing 'total' in stats"
        assert "verified" in data, "Missing 'verified' in stats"
        assert "unverified" in data, "Missing 'unverified' in stats"
        assert "expired" in data, "Missing 'expired' in stats"
        assert "expiring_soon" in data, "Missing 'expiring_soon' in stats"
        
        print(f"✓ Document stats API working - Total: {data['total']}, Verified: {data['verified']}")
    
    # ==================== Document List API Tests ====================
    
    def test_04_get_documents_list(self):
        """Test GET /api/documents/{org_id} returns document list"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        response = self.session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}")
        
        assert response.status_code == 200, f"List API failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Document list API working - Found {len(data)} documents")
    
    # ==================== Document Upload API Tests ====================
    
    def test_05_upload_document_success(self):
        """Test POST /api/documents/{org_id} uploads document successfully"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        
        # Create a test file
        test_content = b"This is a test document content for Phase F testing."
        files = {
            'file': ('TEST_license_doc.txt', io.BytesIO(test_content), 'text/plain')
        }
        data = {
            'title': 'TEST_License Document',
            'doc_type': 'license',
            'description': 'Test license document for Phase F',
            'issuing_authority': 'Test Authority',
            'reference_number': 'TEST-LIC-001',
            'tags': 'test,license,phase-f'
        }
        
        # Remove Content-Type header for multipart upload
        headers = {"Authorization": self.session.headers.get("Authorization")}
        response = requests.post(
            f"{BASE_URL}/api/documents/{TEST_ORG_ID}",
            files=files,
            data=data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.status_code} - {response.text}"
        result = response.json()
        
        assert result.get("status") == "success", "Upload status should be success"
        assert "document" in result, "Response should contain document info"
        assert result["document"].get("id"), "Document should have an ID"
        
        # Store for cleanup
        self.uploaded_doc_ids.append(result["document"]["id"])
        print(f"✓ Document upload successful - ID: {result['document']['id']}")
        return result["document"]["id"]
    
    def test_06_upload_document_missing_title(self):
        """Test upload fails without required title"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        
        test_content = b"Test content"
        files = {'file': ('test.txt', io.BytesIO(test_content), 'text/plain')}
        data = {'doc_type': 'other'}  # Missing title
        
        headers = {"Authorization": self.session.headers.get("Authorization")}
        response = requests.post(
            f"{BASE_URL}/api/documents/{TEST_ORG_ID}",
            files=files,
            data=data,
            headers=headers
        )
        
        # Should fail with 422 (validation error) since title is required
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Upload correctly rejects missing title")
    
    def test_07_upload_document_invalid_extension(self):
        """Test upload fails with invalid file extension"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        
        test_content = b"Test content"
        files = {'file': ('test.exe', io.BytesIO(test_content), 'application/octet-stream')}
        data = {'title': 'Test Invalid', 'doc_type': 'other'}
        
        headers = {"Authorization": self.session.headers.get("Authorization")}
        response = requests.post(
            f"{BASE_URL}/api/documents/{TEST_ORG_ID}",
            files=files,
            data=data,
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Upload correctly rejects invalid file extension")
    
    # ==================== Document Get Single API Tests ====================
    
    def test_08_get_single_document(self):
        """Test GET /api/documents/{org_id}/{doc_id} returns document details"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        
        # First upload a document
        test_content = b"Test document for single get"
        files = {'file': ('TEST_single_doc.txt', io.BytesIO(test_content), 'text/plain')}
        data = {'title': 'TEST_Single Document', 'doc_type': 'certification'}
        
        headers = {"Authorization": self.session.headers.get("Authorization")}
        upload_response = requests.post(
            f"{BASE_URL}/api/documents/{TEST_ORG_ID}",
            files=files,
            data=data,
            headers=headers
        )
        
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        doc_id = upload_response.json()["document"]["id"]
        self.uploaded_doc_ids.append(doc_id)
        
        # Now get the document
        response = self.session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/{doc_id}")
        
        assert response.status_code == 200, f"Get single doc failed: {response.status_code}"
        doc = response.json()
        
        assert doc.get("id") == doc_id, "Document ID mismatch"
        assert doc.get("title") == "TEST_Single Document", "Title mismatch"
        assert doc.get("doc_type") == "certification", "Doc type mismatch"
        assert "is_verified" in doc, "Missing is_verified field"
        assert "is_expired" in doc, "Missing is_expired computed field"
        
        print(f"✓ Get single document working - Title: {doc['title']}")
    
    # ==================== Document Download API Tests ====================
    
    def test_09_download_document(self):
        """Test GET /api/documents/{org_id}/{doc_id}/download returns file"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        
        # First upload a document
        test_content = b"Test document content for download test"
        files = {'file': ('TEST_download_doc.txt', io.BytesIO(test_content), 'text/plain')}
        data = {'title': 'TEST_Download Document', 'doc_type': 'policy'}
        
        headers = {"Authorization": self.session.headers.get("Authorization")}
        upload_response = requests.post(
            f"{BASE_URL}/api/documents/{TEST_ORG_ID}",
            files=files,
            data=data,
            headers=headers
        )
        
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        doc_id = upload_response.json()["document"]["id"]
        self.uploaded_doc_ids.append(doc_id)
        
        # Now download the document
        response = self.session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/{doc_id}/download")
        
        assert response.status_code == 200, f"Download failed: {response.status_code}"
        assert len(response.content) > 0, "Downloaded content is empty"
        assert response.content == test_content, "Downloaded content doesn't match uploaded"
        
        print(f"✓ Document download working - Size: {len(response.content)} bytes")
    
    # ==================== Document Verify API Tests ====================
    
    def test_10_verify_document(self):
        """Test PUT /api/documents/{org_id}/{doc_id}/verify marks document as verified"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        
        # First upload a document
        test_content = b"Test document for verification"
        files = {'file': ('TEST_verify_doc.txt', io.BytesIO(test_content), 'text/plain')}
        data = {'title': 'TEST_Verify Document', 'doc_type': 'compliance'}
        
        headers = {"Authorization": self.session.headers.get("Authorization")}
        upload_response = requests.post(
            f"{BASE_URL}/api/documents/{TEST_ORG_ID}",
            files=files,
            data=data,
            headers=headers
        )
        
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        doc_id = upload_response.json()["document"]["id"]
        self.uploaded_doc_ids.append(doc_id)
        
        # Verify the document is not verified initially
        get_response = self.session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/{doc_id}")
        assert get_response.json().get("is_verified") == False, "Document should not be verified initially"
        
        # Now verify the document
        verify_response = self.session.put(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/{doc_id}/verify")
        
        assert verify_response.status_code == 200, f"Verify failed: {verify_response.status_code}"
        result = verify_response.json()
        assert result.get("status") == "success", "Verify status should be success"
        
        # Confirm verification
        get_response = self.session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/{doc_id}")
        assert get_response.json().get("is_verified") == True, "Document should be verified now"
        
        print(f"✓ Document verification working - ID: {doc_id}")
    
    # ==================== Document Delete API Tests ====================
    
    def test_11_delete_document(self):
        """Test DELETE /api/documents/{org_id}/{doc_id} removes document"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        
        # First upload a document
        test_content = b"Test document for deletion"
        files = {'file': ('TEST_delete_doc.txt', io.BytesIO(test_content), 'text/plain')}
        data = {'title': 'TEST_Delete Document', 'doc_type': 'other'}
        
        headers = {"Authorization": self.session.headers.get("Authorization")}
        upload_response = requests.post(
            f"{BASE_URL}/api/documents/{TEST_ORG_ID}",
            files=files,
            data=data,
            headers=headers
        )
        
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        doc_id = upload_response.json()["document"]["id"]
        
        # Delete the document
        delete_response = self.session.delete(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/{doc_id}")
        
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.status_code}"
        result = delete_response.json()
        assert result.get("status") == "success", "Delete status should be success"
        
        # Confirm deletion
        get_response = self.session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/{doc_id}")
        assert get_response.status_code == 404, "Document should not exist after deletion"
        
        print(f"✓ Document deletion working - ID: {doc_id}")
    
    # ==================== Access Control Tests ====================
    
    def test_12_unauthorized_access_denied(self):
        """Test that unauthenticated requests are denied"""
        # Clear auth header
        session = requests.Session()
        
        response = session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}")
        # Either 401 (Unauthorized) or 403 (Forbidden) is acceptable for unauthenticated requests
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"
        
        print("✓ Unauthorized access correctly denied")
    
    def test_13_stats_after_operations(self):
        """Test stats reflect document operations"""
        self.get_auth_token(SUPER_ADMIN, SUPER_ADMIN.get("org_id"))
        
        # Get initial stats
        initial_response = self.session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/summary/stats")
        initial_stats = initial_response.json()
        initial_total = initial_stats.get("total", 0)
        
        # Upload a document
        test_content = b"Test document for stats"
        files = {'file': ('TEST_stats_doc.txt', io.BytesIO(test_content), 'text/plain')}
        data = {'title': 'TEST_Stats Document', 'doc_type': 'training'}
        
        headers = {"Authorization": self.session.headers.get("Authorization")}
        upload_response = requests.post(
            f"{BASE_URL}/api/documents/{TEST_ORG_ID}",
            files=files,
            data=data,
            headers=headers
        )
        
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["document"]["id"]
        self.uploaded_doc_ids.append(doc_id)
        
        # Get updated stats
        updated_response = self.session.get(f"{BASE_URL}/api/documents/{TEST_ORG_ID}/summary/stats")
        updated_stats = updated_response.json()
        
        assert updated_stats.get("total") == initial_total + 1, "Total should increase by 1"
        assert updated_stats.get("unverified") >= 1, "Unverified count should be at least 1"
        
        print(f"✓ Stats correctly updated - Total: {initial_total} -> {updated_stats['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
