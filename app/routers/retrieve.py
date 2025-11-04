"""Retrieve router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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


def format_snippet(content: str, max_length: int = 160) -> str:
    """Format content as a snippet (≤max_length, word-safe, no newlines).
    
    Args:
        content: Full content to format.
        max_length: Maximum length of snippet (default: 160).
        
    Returns:
        Formatted snippet string.
    """
    # Remove newlines and normalize whitespace
    text = " ".join(content.split())
    
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length]
    # Find last space before max_length
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.7:  # Only use word boundary if it's not too short
        snippet = truncated[:last_space]
    else:
        snippet = truncated
    
    # Ensure no trailing whitespace
    snippet = snippet.rstrip()
    
    return snippet


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
    # Sort by (score DESC, doc_id ASC) for deterministic ordering
    results.sort(key=lambda x: (-x.score, x.doc_id))
    
    # Ensure we return at most k results
    results = results[:request.k]
    
    return RetrieveResponse(results=results)

