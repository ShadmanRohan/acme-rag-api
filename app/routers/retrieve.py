"""Retrieve router."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.common.utils import search_documents, validate_query
from app.config import DEFAULT_K, MAX_K

router = APIRouter(prefix="/retrieve", tags=["retrieve"])


class RetrieveRequest(BaseModel):
    """Request model for retrieval."""
    query: str = Field(..., description="Search query")
    k: int = Field(default=DEFAULT_K, ge=1, le=MAX_K, description=f"Number of results to return (default: {DEFAULT_K})")


class RetrieveResult(BaseModel):
    """Result model for retrieval."""
    doc_id: str
    score: float
    snippet: str
    language: str


class RetrieveResponse(BaseModel):
    """Response model for retrieval."""
    results: list[RetrieveResult]


@router.post("", response_model=RetrieveResponse)
async def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    """Retrieve similar documents for a query.
    
    Args:
        request: Retrieve request with query and optional k.
        
    Returns:
        Retrieve response with results.
    """
    validate_query(request.query)
    search_results = search_documents(request.query, request.k)
    
    results = [
        RetrieveResult(
            doc_id=r["doc_id"],
            score=r["score"],
            snippet=r["snippet"],
            language=r["language"],
        )
        for r in search_results
    ]
    
    return RetrieveResponse(results=results)

