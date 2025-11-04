"""Translation service."""
import os

from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI

from app.services.language import Language, detect_language

# Load environment variables
load_dotenv()


class TranslationService:
    """Service for translating text between languages using OpenAI API."""
    
    def __init__(self):
        """Initialize translation service with OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
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
        
        lang_map = {"en": "English", "ja": "Japanese"}
        prompt = f"""Translate the following text from {lang_map[source_language]} to {lang_map[target_language]}.

Important: Preserve all citation markers in the format [Citation: doc_id]. Do not translate citations.

Text to translate:
{text}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
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
        # Detect source language
        source_language = detect_language(answer)
        
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


def reset_translation_service():
    """Reset the global translation service instance (for testing)."""
    global _translation_service
    _translation_service = None
