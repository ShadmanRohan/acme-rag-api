"""Generate router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.common.utils import format_search_results
from app.config import DEFAULT_K, MAX_K, SUPPORTED_LANGUAGES
from app.services.embeddings import get_embedding_service
from app.services.language import get_language_service
from app.services.llm import get_llm_service
from app.services.store import get_store_service
from app.services.translate import get_translation_service

router = APIRouter(prefix="/generate", tags=["generate"])


class GenerateRequest(BaseModel):
    """Request model for generation."""
    query: str = Field(..., description="Query to generate answer for", min_length=1)
    k: int = Field(default=DEFAULT_K, ge=1, le=MAX_K, description=f"Number of results to retrieve (default: {DEFAULT_K})")
    output_language: str | None = Field(
        default=None,
        description=f"Target language for answer ({', '.join(SUPPORTED_LANGUAGES)}). If not provided, uses detected query language."
    )


@router.post("")
async def generate(request: GenerateRequest) -> dict:
    """Generate an answer from retrieved snippets.
    
    Args:
        request: Generate request with query, optional k, and optional output_language.
        
    Returns:
        Dict with answer, language, and query.
    """
    # Validate output language
    if request.output_language and request.output_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"output_language must be one of {SUPPORTED_LANGUAGES}"
        )
    
    # Detect query language
    query_language = get_language_service().detect(request.query)
    
    # Search and retrieve documents
    store = get_store_service()
    if store.get_size() == 0:
        results = []
    else:
        embedding_service = get_embedding_service()
        query_embedding = embedding_service.embed(request.query)
        search_results = store.search(query_embedding, k=request.k)
        results = format_search_results(search_results, k=request.k)
    
    # Generate answer
    llm_service = get_llm_service()
    answer = llm_service.compose_answer(request.query, results, language=query_language)
    
    # Translate if needed
    final_language = query_language
    if request.output_language and request.output_language != query_language:
        translate_service = get_translation_service()
        answer = translate_service.translate_answer(answer, request.output_language)
        final_language = request.output_language
    
    return {
        "answer": answer,
        "language": final_language,
        "query": request.query,
    }

