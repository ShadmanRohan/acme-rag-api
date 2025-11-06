"""LLM service for composing answers using OpenAI API."""
import os
from typing import Any

from fastapi import HTTPException
from openai import OpenAI

from app.config import (
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
    
    def _get_empty_result_message(self, language: str) -> str:
        """Get empty result message for the given language."""
        return EMPTY_RESULT_MESSAGE_JA if language == "ja" else EMPTY_RESULT_MESSAGE_EN
    
    def _build_context(self, results: list[dict[str, Any]]) -> str:
        """Build context string from retrieved snippets."""
        snippets = [result.get("snippet", "") for result in results]
        return "\n\n".join(snippets)
    
    def _build_prompts(self, query: str, context: str, language: str) -> tuple[str, str]:
        """Build system and user prompts based on language.
        
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        if language == "ja":
            system_prompt = LLM_SYSTEM_PROMPT_JA
            user_prompt = LLM_USER_PROMPT_TEMPLATE_JA.format(query=query, context=context)
        else:
            system_prompt = LLM_SYSTEM_PROMPT_EN
            user_prompt = LLM_USER_PROMPT_TEMPLATE_EN.format(query=query, context=context)
        return system_prompt, user_prompt
    
    def _call_openai_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API and return the answer."""
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=OPENAI_TEMPERATURE_LLM,
            max_tokens=OPENAI_MAX_TOKENS_LLM,
        )
        return response.choices[0].message.content.strip()
    
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
            Composed answer string.
            
        Raises:
            HTTPException: If OpenAI API call fails.
        """
        if not results:
            return self._get_empty_result_message(language)
        
        try:
            context = self._build_context(results)
            system_prompt, user_prompt = self._build_prompts(query, context, language)
            return self._call_openai_api(system_prompt, user_prompt)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate answer using OpenAI API: {str(e)}"
            )


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
