"""Tests for ingest endpoint."""
import base64
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.embeddings import reset_embedding_service
from app.services.store import reset_store_service

client = TestClient(app)

# Clean up test data directory
TEST_DATA_DIR = Path("app/data")


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data before and after each test."""
    os.environ["OPENAI_API_KEY"] = "test-key-123"
    # Reset global service instances
    reset_embedding_service()
    reset_store_service()
    # Clean up before test
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)
    yield
    # Clean up after test
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)
    # Reset global service instances
    reset_embedding_service()
    reset_store_service()


def test_ingest_multipart_file(cleanup_test_data):
    """Test ingesting via multipart file upload."""
    # Create test file content
    content = "This is a test document in English."
    
    # Create a test file
    files = {"file": ("test.txt", content, "text/plain")}
    response = client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    assert response.status_code == 200
    data = response.json()
    assert "doc_id" in data
    assert data["language"] == "en"
    assert data["added"] is True
    assert data["index_size"] == 1


def test_ingest_base64_json(cleanup_test_data):
    """Test ingesting via base64 JSON."""
    # Create test content
    content = "This is another test document."
    content_base64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    # Send as JSON
    json_data = {
        "content": content_base64,
        "filename": "test.txt"
    }
    
    response = client.post(
        "/ingest",
        json=json_data,
        headers={"X-API-Key": "test-key-123", "Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "doc_id" in data
    assert data["language"] == "en"
    assert data["added"] is True


def test_ingest_base64_form(cleanup_test_data):
    """Test ingesting via base64 form field."""
    # Create test content
    content = "This is a form test document."
    content_base64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    # Send as form data
    form_data = {"content": content_base64}
    
    response = client.post(
        "/ingest",
        data=form_data,
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "doc_id" in data
    assert data["language"] == "en"


def test_ingest_detects_japanese(cleanup_test_data):
    """Test that Japanese text is detected correctly."""
    # Japanese content
    content = "これは日本語のテストドキュメントです。"
    
    files = {"file": ("test_ja.txt", content, "text/plain")}
    response = client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "ja"


def test_ingest_detects_english(cleanup_test_data):
    """Test that English text is detected correctly."""
    # English content
    content = "This is an English test document."
    
    files = {"file": ("test_en.txt", content, "text/plain")}
    response = client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"


def test_ingest_idempotent(cleanup_test_data):
    """Test that re-uploading same content is idempotent."""
    content = "This is a unique test document."
    
    # First upload
    files1 = {"file": ("test1.txt", content, "text/plain")}
    response1 = client.post("/ingest", files=files1, headers={"X-API-Key": "test-key-123"})
    
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["added"] is True
    doc_id1 = data1["doc_id"]
    index_size1 = data1["index_size"]
    
    # Second upload of same content
    files2 = {"file": ("test2.txt", content, "text/plain")}
    response2 = client.post("/ingest", files=files2, headers={"X-API-Key": "test-key-123"})
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["added"] is False  # Should not be added again
    assert data2["doc_id"] == doc_id1  # Same doc_id
    assert data2["index_size"] == index_size1  # Index size should not increase


def test_ingest_index_size_increases(cleanup_test_data):
    """Test that index size increases with new content."""
    # First document
    content1 = "First document."
    files1 = {"file": ("test1.txt", content1, "text/plain")}
    response1 = client.post("/ingest", files=files1, headers={"X-API-Key": "test-key-123"})
    
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["index_size"] == 1
    
    # Second document
    content2 = "Second document."
    files2 = {"file": ("test2.txt", content2, "text/plain")}
    response2 = client.post("/ingest", files=files2, headers={"X-API-Key": "test-key-123"})
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["index_size"] == 2


def test_ingest_missing_api_key(cleanup_test_data):
    """Test that ingest requires API key."""
    content = "Test document."
    files = {"file": ("test.txt", content, "text/plain")}
    response = client.post("/ingest", files=files)
    
    assert response.status_code == 401


def test_ingest_empty_content(cleanup_test_data):
    """Test that empty content is rejected."""
    content = ""
    files = {"file": ("test.txt", content, "text/plain")}
    response = client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    assert response.status_code == 400

