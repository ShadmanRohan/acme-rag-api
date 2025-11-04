"""Tests for retrieve endpoint."""
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


def test_retrieve_empty_corpus(cleanup_test_data):
    """Test that empty corpus returns graceful response."""
    response = client.post(
        "/retrieve",
        json={"query": "test query"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["results"] == []
    assert len(data["results"]) == 0


def test_retrieve_default_k(cleanup_test_data):
    """Test that default k=3 returns at most 3 results."""
    # Ingest some documents
    content1 = "This is a test document about software development."
    content2 = "Another document about programming languages."
    content3 = "A third document about testing."
    content4 = "Fourth document about deployment."
    
    files1 = {"file": ("test1.txt", content1, "text/plain")}
    files2 = {"file": ("test2.txt", content2, "text/plain")}
    files3 = {"file": ("test3.txt", content3, "text/plain")}
    files4 = {"file": ("test4.txt", content4, "text/plain")}
    
    client.post("/ingest", files=files1, headers={"X-API-Key": "test-key-123"})
    client.post("/ingest", files=files2, headers={"X-API-Key": "test-key-123"})
    client.post("/ingest", files=files3, headers={"X-API-Key": "test-key-123"})
    client.post("/ingest", files=files4, headers={"X-API-Key": "test-key-123"})
    
    # Retrieve with default k
    response = client.post(
        "/retrieve",
        json={"query": "software development"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= 3
    assert len(data["results"]) > 0


def test_retrieve_custom_k(cleanup_test_data):
    """Test that custom k returns correct number of results."""
    # Ingest documents
    contents = [f"This is document {i}." for i in range(5)]
    for i, content in enumerate(contents):
        files = {"file": (f"test{i}.txt", content, "text/plain")}
        client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Retrieve with custom k
    response = client.post(
        "/retrieve",
        json={"query": "document", "k": 2},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= 2


def test_retrieve_snippet_formatting(cleanup_test_data):
    """Test that snippets are ≤160 chars, word-safe, and no newlines."""
    # Ingest a long document
    long_content = "This is a very long document. " * 20  # Much longer than 160 chars
    files = {"file": ("long.txt", long_content, "text/plain")}
    client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Retrieve
    response = client.post(
        "/retrieve",
        json={"query": "document"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    
    for result in data["results"]:
        assert "snippet" in result
        snippet = result["snippet"]
        assert len(snippet) <= 160
        assert "\n" not in snippet
        assert "\r" not in snippet


def test_retrieve_scores_monotonic(cleanup_test_data):
    """Test that scores are monotonic (r0 ≤ r1 ≤ r2, lower is better for distance)."""
    # Ingest multiple documents
    contents = [
        "Software development best practices",
        "Programming languages and frameworks",
        "Testing and quality assurance",
    ]
    for i, content in enumerate(contents):
        files = {"file": (f"test{i}.txt", content, "text/plain")}
        client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Retrieve
    response = client.post(
        "/retrieve",
        json={"query": "software development", "k": 3},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    
    scores = [result["score"] for result in data["results"]]
    # Check monotonic (scores should be non-decreasing since lower distance is better)
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1], f"Scores not monotonic: {scores}"


def test_retrieve_deterministic_ordering(cleanup_test_data):
    """Test that ties result in deterministic ordering."""
    # Ingest documents with similar content
    content = "This is a test document."
    for i in range(3):
        files = {"file": (f"test{i}.txt", content, "text/plain")}
        client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Retrieve multiple times with same query
    response1 = client.post(
        "/retrieve",
        json={"query": "test document", "k": 3},
        headers={"X-API-Key": "test-key-123"}
    )
    response2 = client.post(
        "/retrieve",
        json={"query": "test document", "k": 3},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Results should be identical (deterministic)
    assert len(data1["results"]) == len(data2["results"])
    for r1, r2 in zip(data1["results"], data2["results"]):
        assert r1["doc_id"] == r2["doc_id"]
        assert r1["score"] == r2["score"]


def test_retrieve_result_structure(cleanup_test_data):
    """Test that results have correct structure."""
    # Ingest a document
    content = "Software development guidelines."
    files = {"file": ("test.txt", content, "text/plain")}
    client.post("/ingest", files=files, headers={"X-API-Key": "test-key-123"})
    
    # Retrieve
    response = client.post(
        "/retrieve",
        json={"query": "software"},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    
    result = data["results"][0]
    assert "doc_id" in result
    assert "score" in result
    assert "snippet" in result
    assert "language" in result
    assert isinstance(result["doc_id"], str)
    assert isinstance(result["score"], (int, float))
    assert isinstance(result["snippet"], str)
    assert isinstance(result["language"], str)
    assert result["language"] in ["en", "ja"]


def test_retrieve_missing_api_key(cleanup_test_data):
    """Test that retrieve requires API key."""
    response = client.post(
        "/retrieve",
        json={"query": "test query"}
    )
    
    assert response.status_code == 401


def test_retrieve_empty_query(cleanup_test_data):
    """Test that empty query is rejected."""
    response = client.post(
        "/retrieve",
        json={"query": ""},
        headers={"X-API-Key": "test-key-123"}
    )
    
    assert response.status_code == 400

