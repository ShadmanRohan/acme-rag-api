"""Tests for generate endpoint."""
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
    os.environ["API_KEY"] = "test-key-123"
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


def test_generate_empty_corpus(cleanup_test_data):
    """Test that empty corpus returns graceful message."""
    response = client.post(
        "/generate",
        json={"query": "test query"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert "language" in data
    assert "query" in data
    assert data["citations"] == []
    assert "sorry" in data["answer"].lower() or "申し訳" in data["answer"]


def test_generate_with_citations(cleanup_test_data):
    """Test that generate includes citations when results exist."""
    # Ingest some documents
    content1 = "Software development best practices."
    content2 = "Programming languages overview."
    content3 = "Testing methodologies."
    
    files1 = {"file": ("test1.txt", content1, "text/plain")}
    files2 = {"file": ("test2.txt", content2, "text/plain")}
    files3 = {"file": ("test3.txt", content3, "text/plain")}
    
    client.post("/ingest", files=files1, headers={"X-API-Key": "test-key-123"})
    client.post("/ingest", files=files2, headers={"X-API-Key": "test-key-123"})
    client.post("/ingest", files=files3, headers={"X-API-Key": "test-key-123"})
    
    # Generate answer
    response = client.post(
        "/generate",
        json={"query": "software development", "k": 3},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert len(data["citations"]) >= 1  # Should have at least one citation
    assert all(isinstance(cite, str) for cite in data["citations"])
    assert data["citations"][0].startswith("doc_")  # Citations should be doc_ids


def test_generate_output_language_en(cleanup_test_data):
    """Test that output_language='en' produces English answer."""
    # Ingest a document
    content = "Software development guidelines."
    files = {"file": ("test.txt", content, "text/plain")}
    client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Generate with explicit English
    response = client.post(
        "/generate",
        json={"query": "software", "output_language": "en"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    # Answer should be in English (check for English patterns)
    assert "Based on" in data["answer"] or "Citation" in data["answer"]


def test_generate_output_language_ja(cleanup_test_data):
    """Test that output_language='ja' produces Japanese answer."""
    # Ingest a document
    content = "ソフトウェア開発のガイドライン。"
    files = {"file": ("test_ja.txt", content, "text/plain")}
    client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Generate with explicit Japanese
    response = client.post(
        "/generate",
        json={"query": "ソフトウェア", "output_language": "ja"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "ja"
    # Answer should contain Japanese characters
    assert any(ord(char) >= 0x3040 and ord(char) <= 0x9FAF for char in data["answer"])


def test_generate_detects_query_language(cleanup_test_data):
    """Test that generate detects query language when output_language not provided."""
    # Ingest documents
    content = "Software development."
    files = {"file": ("test.txt", content, "text/plain")}
    client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Generate with English query (should detect as English)
    response = client.post(
        "/generate",
        json={"query": "software development"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    
    # Generate with Japanese query (should detect as Japanese)
    response2 = client.post(
        "/generate",
        json={"query": "ソフトウェア開発"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["language"] == "ja"


def test_generate_invalid_output_language(cleanup_test_data):
    """Test that invalid output_language is rejected."""
    response = client.post(
        "/generate",
        json={"query": "test", "output_language": "fr"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 400
    assert "output_language" in str(response.json()).lower() or "en" in str(response.json()).lower()


def test_generate_empty_query(cleanup_test_data):
    """Test that empty query is rejected."""
    response = client.post(
        "/generate",
        json={"query": ""},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 400


def test_generate_missing_api_key(cleanup_test_data):
    """Test that generate requires API key."""
    response = client.post(
        "/generate",
        json={"query": "test query"}
    )
    
    assert response.status_code == 401


def test_generate_response_structure(cleanup_test_data):
    """Test that generate response has correct structure."""
    # Ingest a document
    content = "Software development best practices."
    files = {"file": ("test.txt", content, "text/plain")}
    client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Generate
    response = client.post(
        "/generate",
        json={"query": "software", "k": 2},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "answer" in data
    assert "citations" in data
    assert "language" in data
    assert "query" in data
    
    # Check types
    assert isinstance(data["answer"], str)
    assert isinstance(data["citations"], list)
    assert isinstance(data["language"], str)
    assert isinstance(data["query"], str)
    
    # Check language value
    assert data["language"] in ["en", "ja"]
    
    # Check that query matches
    assert data["query"] == "software"


def test_generate_custom_k(cleanup_test_data):
    """Test that custom k parameter works."""
    # Ingest multiple documents
    for i in range(5):
        content = f"Document {i} about software."
        files = {"file": (f"test{i}.txt", content, "text/plain")}
        client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Generate with custom k
    response = client.post(
        "/generate",
        json={"query": "software", "k": 2},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should have citations based on k=2
    assert len(data["citations"]) <= 2

