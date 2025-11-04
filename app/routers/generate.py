"""Generate router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.embeddings import get_embedding_service
from app.services.language import detect_language
from app.services.llm import get_llm_service
from app.services.store import get_store_service
from app.routers.retrieve import format_snippet

router = APIRouter(prefix="/generate", tags=["generate"])


class GenerateRequest(BaseModel):
    """Request model for generation."""
    query: str = Field(..., description="Query to generate answer for")
    k: int = Field(default=3, ge=1, le=100, description="Number of results to retrieve (default: 3)")
    output_language: str | None = Field(
        default=None,
        description="Target language for answer ('en' or 'ja'). If not provided, uses detected query language."
    )


class GenerateResponse(BaseModel):
    """Response model for generation."""
    answer: str
    citations: list[str]
    language: str
    query: str


@router.post("", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """Generate an answer from retrieved snippets.
    
    Args:
        request: Generate request with query, optional k, and optional output_language.
        
    Returns:
        Generate response with answer, citations, and metadata.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Detect query language if output_language not provided
    if request.output_language:
        if request.output_language not in ["en", "ja"]:
            raise HTTPException(status_code=400, detail="output_language must be 'en' or 'ja'")
        target_language = request.output_language
    else:
        target_language = detect_language(request.query)
    
    # Retrieve relevant snippets (reuse retrieve logic)
    store = get_store_service()
    embedding_service = get_embedding_service()
    
    # Handle empty corpus gracefully
    if store.get_size() == 0:
        llm_service = get_llm_service()
        answer = llm_service.compose_answer(request.query, [], language=target_language)
        return GenerateResponse(
            answer=answer,
            citations=[],
            language=target_language,
            query=request.query,
        )
    
    # Generate query embedding
    query_embedding = embedding_service.embed(request.query)
    
    # Search for similar documents
    search_results = store.search(query_embedding, k=request.k)
    
    # Format results with snippets
    results = []
    for result in search_results:
        snippet = format_snippet(result["content"], max_length=160)
        results.append({
            "doc_id": result["doc_id"],
            "snippet": snippet,
            "score": result["score"],
            "language": result["language"],
        })
    
    # Sort by score for deterministic ordering
    results.sort(key=lambda x: (x["score"], x["doc_id"]))
    results = results[:request.k]
    
    # Compose answer using mock LLM service
    llm_service = get_llm_service()
    answer = llm_service.compose_answer(request.query, results, language=target_language)
    
    # Extract citations
    citations = llm_service.get_citations(results)
    
    # Ensure at least one citation when results exist
    if not citations and results:
        citations = [result.get("doc_id", "") for result in results if result.get("doc_id")]
    
    return GenerateResponse(
        answer=answer,
        citations=citations,
        language=target_language,
        query=request.query,
    )

