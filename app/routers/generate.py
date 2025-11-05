"""Generate router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.common.utils import search_documents, validate_query
from app.config import DEFAULT_K, MAX_K, SUPPORTED_LANGUAGES
from app.services.language import get_language_service
from app.services.llm import get_llm_service
from app.services.translate import get_translation_service

router = APIRouter(prefix="/generate", tags=["generate"])


class GenerateRequest(BaseModel):
    """Request model for generation."""
    query: str = Field(..., description="Query to generate answer for")
    k: int = Field(default=DEFAULT_K, ge=1, le=MAX_K, description=f"Number of results to retrieve (default: {DEFAULT_K})")
    output_language: str | None = Field(
        default=None,
        description=f"Target language for answer ({', '.join(SUPPORTED_LANGUAGES)}). If not provided, uses detected query language."
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
    validate_query(request.query)
    
    if request.output_language and request.output_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"output_language must be one of {SUPPORTED_LANGUAGES}")
    
    query_language = get_language_service().detect(request.query)
    results = search_documents(request.query, request.k)
    
    llm_service = get_llm_service()
    translate_service = get_translation_service()
    
    answer = llm_service.compose_answer(request.query, results, language=query_language)
    
    final_language = query_language
    if request.output_language and request.output_language != query_language:
        answer = translate_service.translate_answer(answer, request.output_language)
        final_language = request.output_language
    
    citations = llm_service.get_citations(results)
    if not citations and results:
        citations = [r.get("doc_id", "") for r in results if r.get("doc_id")]
    
    return GenerateResponse(
        answer=answer,
        citations=citations,
        language=final_language,
        query=request.query,
    )

