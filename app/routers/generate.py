"""Generate router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.common.utils import format_snippet
from app.services.embeddings import get_embedding_service
from app.services.language import detect_language
from app.services.llm import get_llm_service
from app.services.store import get_store_service
from app.services.translate import get_translation_service

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
    
    # Validate output_language if provided
    if request.output_language and request.output_language not in ["en", "ja"]:
        raise HTTPException(status_code=400, detail="output_language must be 'en' or 'ja'")
    
    # Always detect query language first
    query_language = detect_language(request.query)
    
    # Retrieve relevant snippets (reuse retrieve logic)
    store = get_store_service()
    embedding_service = get_embedding_service()
    
    # Handle empty corpus gracefully
    if store.get_size() == 0:
        llm_service = get_llm_service()
        answer = llm_service.compose_answer(request.query, [], language=query_language)
        
        # Translate if output_language differs
        final_language = query_language
        if request.output_language and request.output_language != query_language:
            translate_service = get_translation_service()
            answer = translate_service.translate_answer(answer, request.output_language)
            final_language = request.output_language
        
        return GenerateResponse(
            answer=answer,
            citations=[],
            language=final_language,
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
    
    # Compose answer in query language (always)
    llm_service = get_llm_service()
    answer = llm_service.compose_answer(request.query, results, language=query_language)
    
    # Translate if output_language differs from query language
    final_language = query_language
    if request.output_language and request.output_language != query_language:
        translate_service = get_translation_service()
        answer = translate_service.translate_answer(answer, request.output_language)
        final_language = request.output_language
    
    # Extract citations
    citations = llm_service.get_citations(results)
    
    # Ensure at least one citation when results exist
    if not citations and results:
        citations = [result.get("doc_id", "") for result in results if result.get("doc_id")]
    
    return GenerateResponse(
        answer=answer,
        citations=citations,
        language=final_language,
        query=request.query,
    )

