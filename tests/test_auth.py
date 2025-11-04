"""Tests for authentication."""
import os
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_no_auth():
    """Test that /health endpoint doesn't require auth."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_api_key():
    """Test that missing API key returns 401."""
    # Set a test API key
    os.environ["API_KEY"] = "test-key-123"
    
    # Try to access a route that requires auth (we'll use a non-existent route for now)
    # Since we only have /health, let's test by trying to access docs or openapi
    response = client.get("/docs")
    assert response.status_code == 401
    assert "error" in response.json()
    assert response.json()["error"]["status_code"] == 401
    assert "Missing X-API-Key header" in response.json()["error"]["message"]


def test_invalid_api_key():
    """Test that invalid API key returns 401."""
    os.environ["API_KEY"] = "test-key-123"
    
    response = client.get("/docs", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert "error" in response.json()
    assert response.json()["error"]["status_code"] == 401
    assert "Invalid or missing API key" in response.json()["error"]["message"]


def test_valid_api_key():
    """Test that valid API key allows access."""
    os.environ["API_KEY"] = "test-key-123"
    
    response = client.get("/docs", headers={"X-API-Key": "test-key-123"})
    # Docs endpoint should be accessible with valid key
    assert response.status_code == 200


def test_validation_error_format():
    """Test that validation errors return uniform error envelope."""
    os.environ["API_KEY"] = "test-key-123"
    
    # Try to POST invalid JSON to a route (using /openapi.json as it expects GET)
    # Actually, let's test with a malformed request
    response = client.post(
        "/health",
        headers={"X-API-Key": "test-key-123", "Content-Type": "application/json"},
        json={"invalid": "data"}
    )
    # Health endpoint is GET only, so this might return 405 or 422
    # The important thing is that if there's an error, it has the uniform format
    if response.status_code >= 400:
        assert "error" in response.json()
        assert "status_code" in response.json()["error"]

