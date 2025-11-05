"""Retrieve router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.common.utils import format_snippet
from app.services.embeddings import get_embedding_service
from app.services.store import get_store_service

router = APIRouter(prefix="/retrieve", tags=["retrieve"])


class RetrieveRequest(BaseModel):
    """Request model for retrieval."""
    query: str = Field(..., description="Search query")
    k: int = Field(default=3, ge=1, le=100, description="Number of results to return (default: 3)")


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
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    store = get_store_service()
    embedding_service = get_embedding_service()
    
    # Handle empty corpus gracefully
    if store.get_size() == 0:
        return RetrieveResponse(results=[])
    
    # Generate query embedding
    query_embedding = embedding_service.embed(request.query)
    
    # Search for similar documents
    search_results = store.search(query_embedding, k=request.k)
    
    # Format results with snippets and deterministic ordering
    results = []
    for result in search_results:
        snippet = format_snippet(result["content"], max_length=160)
        results.append(
            RetrieveResult(
                doc_id=result["doc_id"],
                score=result["score"],
                snippet=snippet,
                language=result["language"],
            )
        )
    
    # Ensure deterministic ordering on ties (by doc_id)
    # Results are already sorted by score from FAISS, but we need to handle ties
    # Sort by (score ASC, doc_id ASC) for deterministic ordering (lower score is better)
    results.sort(key=lambda x: (x.score, x.doc_id))
    
    # Ensure we return at most k results
    results = results[:request.k]
    
    return RetrieveResponse(results=results)

