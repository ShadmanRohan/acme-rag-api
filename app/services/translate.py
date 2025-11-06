"""Translation service."""
import os

from fastapi import HTTPException
from openai import OpenAI

from app.config import (
    LANGUAGE_NAME_MAP,
    OPENAI_API_KEY,
    OPENAI_MAX_TOKENS_TRANSLATE,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE_TRANSLATE,
    TRANSLATION_PROMPT_TEMPLATE,
)
from app.services.language import Language, get_language_service


class TranslationService:
    """Service for translating text between languages using OpenAI API."""
    
    def __init__(self):
        """Initialize translation service with OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
    
    def translate(self, text: str, source_language: Language, target_language: Language) -> str:
        """Translate text using OpenAI API.
        
        Args:
            text: Text to translate.
            source_language: Source language ('en' or 'ja').
            target_language: Target language ('en' or 'ja').
            
        Returns:
            Translated text.
        """
        if source_language == target_language:
            return text
        
        source_lang_name = LANGUAGE_NAME_MAP[source_language]
        target_lang_name = LANGUAGE_NAME_MAP[target_language]
        prompt = TRANSLATION_PROMPT_TEMPLATE.format(
            source_language=source_lang_name,
            target_language=target_lang_name,
            text=text
        )
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=OPENAI_TEMPERATURE_TRANSLATE,
                max_tokens=OPENAI_MAX_TOKENS_TRANSLATE,
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to translate text: {str(e)}"
            )
    
    def translate_answer(self, answer: str, target_language: Language) -> str:
        """Translate an answer to target language.
        
        Args:
            answer: Answer text to translate.
            target_language: Target language ('en' or 'ja').
            
        Returns:
            Translated answer.
        """
        source_language = get_language_service().detect(answer)
        if source_language == target_language:
            return answer
        return self.translate(answer, source_language, target_language)


# Global instance
_translation_service: TranslationService | None = None


def get_translation_service() -> TranslationService:
    """Get or create the global translation service instance.
    
    Raises:
        ValueError: If OPENAI_API_KEY is not configured.
    """
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service
