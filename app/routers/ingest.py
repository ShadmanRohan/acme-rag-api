"""Ingest router."""
import base64

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.datastructures import FormData

from app.config import ALLOWED_FILE_EXTENSION
from app.services.language import get_language_service
from app.services.store import get_store_service

router = APIRouter(prefix="/ingest", tags=["ingest"])


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
async def ingest(request: Request):
    """Ingest text content via multipart file upload or base64 JSON.
    
    Supports three formats:
    1. Multipart file upload: POST with file in 'file' field
    2. Base64 JSON: POST with JSON body containing 'content' (base64)
    3. Base64 form: POST with 'content' form field containing base64 encoded text
    
    Args:
        request: FastAPI request object.
        
    Returns:
        Dict with doc_id, language, and status.
    """
    text_content: str | None = None
    content_type = request.headers.get("content-type", "")
    
    # Handle JSON body
    if "application/json" in content_type:
        try:
            json_data = await request.json()
            if "content" in json_data:
                decoded_bytes = base64.b64decode(json_data["content"])
                text_content = decoded_bytes.decode("utf-8")
            else:
                raise HTTPException(status_code=400, detail="No content provided in JSON body")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {str(e)}")
    
    # Handle form data (multipart or urlencoded)
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        try:
            form_data: FormData = await request.form()
            
            # Check for file upload
            if "file" in form_data:
                file: UploadFile = form_data["file"]
                if file.filename and not file.filename.endswith(ALLOWED_FILE_EXTENSION):
                    raise HTTPException(status_code=400, detail=f"Only {ALLOWED_FILE_EXTENSION} files are supported")
                
                content_bytes = await file.read()
                text_content = content_bytes.decode("utf-8")
            
            # Check for base64 content in form field
            elif "content" in form_data:
                content_str = form_data["content"]
                if isinstance(content_str, list):
                    content_str = content_str[0]
                decoded_bytes = base64.b64decode(content_str)
                text_content = decoded_bytes.decode("utf-8")
            else:
                raise HTTPException(status_code=400, detail="No file or content field provided in form data")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=400, detail=f"Invalid form data: {str(e)}")
    
    # Unsupported content type
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported content type. Use multipart/form-data, application/x-www-form-urlencoded, or application/json."
        )
    
    return _process_content(text_content)

