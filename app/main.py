"""Main FastAPI application."""
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.errors import create_error_response
from app.config import (
    API_KEY_HEADER,
    APP_NAME,
    APP_VERSION,
    HEALTH_CHECK_PATH,
    OPENAI_API_KEY,
)
from app.routers import generate, ingest, retrieve

# Load environment variables once at application startup
load_dotenv()

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# Register routers
app.include_router(ingest.router)
app.include_router(retrieve.router)
app.include_router(generate.router)


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
    if request.url.path == HEALTH_CHECK_PATH:
        return await call_next(request)
    
    # Check for API key header
    api_key = request.headers.get(API_KEY_HEADER)
    if not api_key:
        return create_error_response(401, f"Missing {API_KEY_HEADER} header")
    
    # Validate the API key (read from environment dynamically for tests)
    import os
    expected_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
    if not expected_key:
        return create_error_response(500, "API key not configured on server")
    if api_key != expected_key:
        return create_error_response(401, "Invalid or missing API key")
    
    return await call_next(request)


@app.get(HEALTH_CHECK_PATH)
async def health():
    """Health check endpoint (no auth required)."""
    return {"status": "ok"}

