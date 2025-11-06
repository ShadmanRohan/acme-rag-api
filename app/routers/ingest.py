"""Ingest router."""
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config import ALLOWED_FILE_EXTENSION
from app.services.language import get_language_service
from app.services.store import get_store_service

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _validate_file(file: UploadFile) -> None:
    """Validate file extension."""
    if file.filename and not file.filename.endswith(ALLOWED_FILE_EXTENSION):
        raise HTTPException(
            status_code=400,
            detail=f"Only {ALLOWED_FILE_EXTENSION} files are supported. Invalid file: {file.filename}"
        )


async def _read_file_content(file: UploadFile) -> str:
    """Read and decode file content."""
    try:
        content_bytes = await file.read()
        return content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"File must contain valid UTF-8 text: {file.filename}"
        )


def _process_content(text_content: str) -> dict:
    """Process text content: detect language and store."""
    if not text_content or not text_content.strip():
        raise HTTPException(status_code=400, detail="Content is empty")
    
    language = get_language_service().detect(text_content)
    store = get_store_service()
    result = store.add(text_content, language)
    
    return {
        "doc_id": result["doc_id"],
        "language": language,
        "added": result["added"],
        "index_size": store.get_size(),
    }


async def _process_file(file: UploadFile) -> dict:
    """Process a single file."""
    _validate_file(file)
    text_content = await _read_file_content(file)
    result = _process_content(text_content)
    result["filename"] = file.filename
    return result


@router.post("")
async def ingest(files: List[UploadFile] = File(...)):
    """Ingest one or more .txt files for QA processing.
    
    Args:
        files: One or more .txt files to upload.
        
    Returns:
        If single file: Dict with doc_id, language, and status.
        If multiple files: Dict with files_processed, results, and index_size.
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    
    results = []
    for file in files:
        results.append(await _process_file(file))
    
    # Return single result for backward compatibility
    if len(results) == 1:
        return results[0]
    
    # Return summary for multiple files
    return {
        "files_processed": len(results),
        "results": results,
        "index_size": get_store_service().get_size(),
    }

