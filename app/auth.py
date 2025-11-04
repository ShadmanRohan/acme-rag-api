"""Authentication module."""
import os
from fastapi import Header, HTTPException, status

from app.common.errors import UnauthorizedError


def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Dependency to require X-API-Key header.
    
    Args:
        x_api_key: The API key from the X-API-Key header.
        
    Returns:
        The API key if valid.
        
    Raises:
        UnauthorizedError: If the API key is missing or invalid.
    """
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured on server"
        )
    if x_api_key != expected_key:
        raise UnauthorizedError("Invalid or missing API key")
    return x_api_key
