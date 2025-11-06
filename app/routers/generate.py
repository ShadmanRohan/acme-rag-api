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
    language: str
    query: str


def _validate_output_language(output_language: str | None) -> None:
    """Validate output language if provided."""
    if output_language and output_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"output_language must be one of {SUPPORTED_LANGUAGES}"
        )


def _detect_query_language(query: str) -> str:
    """Detect the language of the query."""
    return get_language_service().detect(query)


def _generate_answer(query: str, query_language: str, k: int) -> str:
    """Generate answer from retrieved documents."""
    results = search_documents(query, k)
    llm_service = get_llm_service()
    return llm_service.compose_answer(query, results, language=query_language)


def _translate_answer_if_needed(
    answer: str,
    query_language: str,
    output_language: str | None,
) -> tuple[str, str]:
    """Translate answer if output_language is specified and different from query language.
    
    Returns:
        Tuple of (translated_answer, final_language)
    """
    if not output_language or output_language == query_language:
        return answer, query_language
    
    translate_service = get_translation_service()
    translated_answer = translate_service.translate_answer(answer, output_language)
    return translated_answer, output_language


@router.post("", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """Generate an answer from retrieved snippets.
    
    Args:
        request: Generate request with query, optional k, and optional output_language.
        
    Returns:
        Generate response with answer and metadata.
    """
    validate_query(request.query)
    _validate_output_language(request.output_language)
    
    query_language = _detect_query_language(request.query)
    answer = _generate_answer(request.query, query_language, request.k)
    final_answer, final_language = _translate_answer_if_needed(
        answer, query_language, request.output_language
    )
    
    return GenerateResponse(
        answer=final_answer,
        language=final_language,
        query=request.query,
    )

