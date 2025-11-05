"""Language detection service."""
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


def detect_language(text: str) -> Language:
    """Detect language using OpenAI API. If fails, use a basic regex check.
    
    Args:
        text: Text to analyze.
        
    Returns:
        'en' for English, 'ja' for Japanese.
    """
    if not text.strip():
        return LANGUAGE_DEFAULT
    
    # Use OpenAI API to detect language
    import os
    api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    client = OpenAI(api_key=api_key)
    
    text_sample = text[:LANGUAGE_DETECTION_TEXT_LIMIT]
    prompt = LANGUAGE_DETECTION_PROMPT_TEMPLATE.format(text=text_sample)
    
    try:
        response = client.chat.completions.create(
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
