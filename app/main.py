"""Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.errors import UnauthorizedError, create_error_response
from app.routers import ingest

app = FastAPI(title="Acme API", version="0.1.0")

# Register routers
app.include_router(ingest.router)


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError):
    """Handle 401 Unauthorized errors."""
    return create_error_response(401, str(exc.detail))


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with uniform error envelope."""
    return create_error_response(exc.status_code, exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with uniform error envelope."""
    errors = exc.errors()
    details = {error["loc"][-1]: error["msg"] for error in errors}
    return create_error_response(422, "Validation error", details)


# Apply auth dependency globally to all routes except /health
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Apply authentication to all routes except /health."""
    if request.url.path == "/health":
        return await call_next(request)
    
    # Check for X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return create_error_response(401, "Missing X-API-Key header")
    
    # Validate the API key
    import os
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        return create_error_response(500, "API key not configured on server")
    if api_key != expected_key:
        return create_error_response(401, "Invalid or missing API key")
    
    return await call_next(request)


@app.get("/health")
async def health():
    """Health check endpoint (no auth required)."""
    return {"status": "ok"}

