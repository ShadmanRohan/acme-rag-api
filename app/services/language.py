"""Language detection service."""
import re
from typing import Literal

Language = Literal["en", "ja"]


def detect_language(text: str) -> Language:
    """Detect if text is English or Japanese.
    
    Args:
        text: Text to analyze.
        
    Returns:
        'en' for English, 'ja' for Japanese.
    """
    if not text.strip():
        return "en"  # Default to English for empty text
    
    # Check for Japanese characters (Hiragana, Katakana, Kanji)
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
    japanese_chars = len(japanese_pattern.findall(text))
    
    # If significant portion of text contains Japanese characters, it's Japanese
    # Threshold: if >10% of non-whitespace chars are Japanese, consider it JA
    non_whitespace = len(re.sub(r'\s+', '', text))
    if non_whitespace > 0 and japanese_chars / non_whitespace > 0.1:
        return "ja"
    
    return "en"

