"""Ingest router."""
import base64
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.config import ALLOWED_FILE_EXTENSION
from app.services.language import get_language_service
from app.services.store import get_store_service

router = APIRouter(prefix="/ingest", tags=["ingest"])


async def get_json_body(request: Request):
    """Dependency to extract JSON body from request."""
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            return await request.json()
    except Exception:
        pass
    return None


def _process_content(text_content: str) -> dict:
    """Process text content: detect language and store.
    
    Args:
        text_content: Text to process.
        
    Returns:
        Dict with doc_id, language, and status.
    """
    if not text_content or not text_content.strip():
        raise HTTPException(status_code=400, detail="Content is empty")
    
    language = get_language_service().detect(text_content)
    
    # Store content
    store = get_store_service()
    result = store.add(text_content, language)
    
    return {
        "doc_id": result["doc_id"],
        "language": language,
        "added": result["added"],
        "index_size": store.get_size(),
    }


@router.post("")
async def ingest(
    file: Annotated[UploadFile | None, File()] = None,
    content: Annotated[str | None, Form()] = None,
    json_body: dict | None = Depends(get_json_body),
):
    """Ingest text content via multipart file upload or base64 JSON.
    
    Supports three formats:
    1. Multipart file upload: POST with file in 'file' field
    2. Base64 JSON: POST with JSON body containing 'content' (base64)
    3. Base64 form: POST with 'content' form field containing base64 encoded text
    
    Args:
        file: Uploaded file (multipart).
        content: Base64 encoded content (multipart form).
        json_body: JSON body data (if content-type is application/json).
        
    Returns:
        Dict with doc_id, language, and status.
    """
    text_content: str | None = None
    
    # Handle multipart file upload
    if file is not None:
        if file.filename and not file.filename.endswith(ALLOWED_FILE_EXTENSION):
            raise HTTPException(status_code=400, detail=f"Only {ALLOWED_FILE_EXTENSION} files are supported")
        
        content_bytes = await file.read()
        text_content = content_bytes.decode("utf-8")
    
    # Handle base64 content in multipart form
    elif content is not None:
        try:
            decoded_bytes = base64.b64decode(content)
            text_content = decoded_bytes.decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {str(e)}")
    
    # Handle JSON body with base64 content
    elif json_body is not None:
        try:
            if "content" in json_body:
                decoded_bytes = base64.b64decode(json_body["content"])
                text_content = decoded_bytes.decode("utf-8")
            else:
                raise HTTPException(status_code=400, detail="No content provided in JSON body")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {str(e)}")
    
    # No content provided
    else:
        raise HTTPException(status_code=400, detail="No content provided. Use file upload, base64 form field, or JSON body.")
    
    return _process_content(text_content)

