"""Language detection service."""
import os
import re
from typing import Literal

from openai import OpenAI

from app.config import (
    LANGUAGE_DEFAULT,
    LANGUAGE_DETECTION_PATTERN,
    LANGUAGE_DETECTION_TEXT_LIMIT,
    LANGUAGE_DETECTION_THRESHOLD,
    OPENAI_API_KEY,
    OPENAI_MAX_TOKENS_DETECT,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE_DETECT,
    LANGUAGE_DETECTION_PROMPT_TEMPLATE,
)

Language = Literal["en", "ja"]


class LanguageService:
    """Service for detecting language using OpenAI API."""
    
    def __init__(self):
        """Initialize the language service."""
        api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
    
    def detect(self, text: str) -> Language:
        """Detect language using OpenAI API. If fails, use a basic regex check.
        
        Args:
            text: Text to analyze.
            
        Returns:
            'en' for English, 'ja' for Japanese.
        """
        if not text.strip():
            return LANGUAGE_DEFAULT
        
        text_sample = text[:LANGUAGE_DETECTION_TEXT_LIMIT]
        prompt = LANGUAGE_DETECTION_PROMPT_TEMPLATE.format(text=text_sample)
        
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=OPENAI_TEMPERATURE_DETECT,
                max_tokens=OPENAI_MAX_TOKENS_DETECT,
            )
            
            result = response.choices[0].message.content.strip().lower()
            return "ja" if "ja" in result or "japanese" in result else "en"
        except Exception:
            # Fallback: basic regex check if API fails
            japanese_pattern = re.compile(LANGUAGE_DETECTION_PATTERN)
            japanese_chars = len(japanese_pattern.findall(text))
            non_whitespace = len(re.sub(r'\s+', '', text))
            if non_whitespace > 0 and japanese_chars / non_whitespace > LANGUAGE_DETECTION_THRESHOLD:
                return "ja"
            return "en"


# Global instance
_language_service: LanguageService | None = None


def get_language_service() -> LanguageService:
    """Get or create the global language service instance.
    
    Raises:
        ValueError: If OPENAI_API_KEY is not configured.
    """
    global _language_service
    if _language_service is None:
        _language_service = LanguageService()
    return _language_service
