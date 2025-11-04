"""Translation service."""
from app.services.language import Language


class TranslationService:
    """Service for translating text between languages."""
    
    def translate(self, text: str, target_language: Language) -> str:
        """Translate text to target language.
        
        Args:
            text: Text to translate.
            target_language: Target language ('en' or 'ja').
            
        Returns:
            Translated text (mock implementation - returns original for now).
        """
        # Mock implementation - in a real system, this would use a translation API
        # For now, we'll return the original text as the mock LLM service
        # already handles language-specific formatting
        return text
    
    def translate_answer(self, answer: str, target_language: Language) -> str:
        """Translate an answer to target language.
        
        Args:
            answer: Answer text to translate.
            target_language: Target language ('en' or 'ja').
            
        Returns:
            Translated answer.
        """
        # Mock implementation - the LLM service already generates language-specific answers
        return answer


# Global instance
_translation_service: TranslationService | None = None


def get_translation_service() -> TranslationService:
    """Get or create the global translation service instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service


def reset_translation_service():
    """Reset the global translation service instance (for testing)."""
    global _translation_service
    _translation_service = None

