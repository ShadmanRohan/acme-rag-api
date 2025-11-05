"""Common error responses."""
from fastapi import HTTPException, status

from fastapi.responses import JSONResponse


def create_error_response(status_code: int, message: str, details: dict | None = None) -> JSONResponse:
    """Create a uniform error response."""
    error_body = {
        "error": {
            "message": message,
            "status_code": status_code,
        }
    }
    if details:
        error_body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=error_body)


class UnauthorizedError(HTTPException):
    """401 Unauthorized error."""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

