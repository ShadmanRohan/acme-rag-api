"""Retrieve router."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.common.utils import format_search_results
from app.config import DEFAULT_K, MAX_K
from app.services.embeddings import get_embedding_service
from app.services.store import get_store_service

router = APIRouter(prefix="/retrieve", tags=["retrieve"])


class RetrieveRequest(BaseModel):
    """Request model for retrieval."""
    query: str = Field(..., description="Search query", min_length=1)
    k: int = Field(default=DEFAULT_K, ge=1, le=MAX_K, description=f"Number of results to return (default: {DEFAULT_K})")


@router.post("")
async def retrieve(request: RetrieveRequest) -> dict:
    """Retrieve similar documents for a query.
    
    Args:
        request: Retrieve request with query and optional k.
        
    Returns:
        Dict with results list.
    """
    store = get_store_service()
    if store.get_size() == 0:
        return {"results": []}
    
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.embed(request.query)
    search_results = store.search(query_embedding, k=request.k)
    results = format_search_results(search_results, k=request.k)
    
    return {"results": results}

