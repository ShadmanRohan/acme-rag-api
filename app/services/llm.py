"""LLM service for composing answers using OpenAI API."""
import os
from typing import Any

from fastapi import HTTPException
from openai import OpenAI

from app.config import (
    CITATION_FINAL_FORMAT,
    CITATION_TEMP_FORMAT,
    EMPTY_RESULT_MESSAGE_EN,
    EMPTY_RESULT_MESSAGE_JA,
    LLM_SYSTEM_PROMPT_EN,
    LLM_SYSTEM_PROMPT_JA,
    LLM_USER_PROMPT_TEMPLATE_EN,
    LLM_USER_PROMPT_TEMPLATE_JA,
    OPENAI_API_KEY,
    OPENAI_MAX_TOKENS_LLM,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE_LLM,
)


class LLMService:
    """LLM service that composes answers from retrieved snippets using OpenAI API."""
    
    def __init__(self):
        """Initialize the LLM service."""
        api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
    
    def compose_answer(
        self,
        query: str,
        results: list[dict[str, Any]],
        language: str = "en",
    ) -> str:
        """Compose an answer from retrieved snippets using OpenAI API.
        
        Args:
            query: The user's query.
            results: List of retrieved results with doc_id, snippet, score, language.
            language: Target language for the answer ('en' or 'ja').
            
        Returns:
            Composed answer string with citations.
            
        Raises:
            HTTPException: If OpenAI API call fails.
        """
        if not results:
            if language == "ja":
                return EMPTY_RESULT_MESSAGE_JA
            return EMPTY_RESULT_MESSAGE_EN
        
        try:
            # Build context from retrieved snippets
            context_parts = []
            citations_map = {}
            for i, result in enumerate(results, 1):
                snippet = result.get("snippet", "")
                doc_id = result.get("doc_id", "")
                temp_citation = CITATION_TEMP_FORMAT.format(index=i)
                citations_map[temp_citation] = doc_id
                context_parts.append(f"{temp_citation} {snippet}")
            
            context = "\n\n".join(context_parts)
            
            # Build prompt based on language
            if language == "ja":
                system_prompt = LLM_SYSTEM_PROMPT_JA
                user_prompt = LLM_USER_PROMPT_TEMPLATE_JA.format(query=query, context=context)
            else:
                system_prompt = LLM_SYSTEM_PROMPT_EN
                user_prompt = LLM_USER_PROMPT_TEMPLATE_EN.format(query=query, context=context)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=OPENAI_TEMPERATURE_LLM,
                max_tokens=OPENAI_MAX_TOKENS_LLM,
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Replace temporary citation references with final citation format
            for ref, doc_id in citations_map.items():
                final_citation = CITATION_FINAL_FORMAT.format(doc_id=doc_id)
                answer = answer.replace(ref, final_citation)
            
            return answer
            
        except Exception as e:
            # Raise HTTP exception if API call fails
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate answer using OpenAI API: {str(e)}"
            )
    
    def get_citations(self, results: list[dict[str, Any]]) -> list[str]:
        """Extract citations from results.
        
        Args:
            results: List of retrieved results with doc_id.
            
        Returns:
            List of citation doc_ids.
        """
        return [result.get("doc_id", "") for result in results if result.get("doc_id")]


# Global instance
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance.
    
    Raises:
        ValueError: If OPENAI_API_KEY is not configured.
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def reset_llm_service():
    """Reset the global LLM service instance (for testing)."""
    global _llm_service
    _llm_service = None
