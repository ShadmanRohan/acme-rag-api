"""Language detection service."""
import os
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

Language = Literal["en", "ja"]


def detect_language(text: str) -> Language:
    """Detect language using OpenAI API.
    
    Args:
        text: Text to analyze.
        
    Returns:
        'en' for English, 'ja' for Japanese.
    """
    if not text.strip():
        return "en"  # Default to English for empty text
    
    # Use OpenAI API to detect language
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"Detect the language of this text. Respond with only 'en' for English or 'ja' for Japanese.\n\nText: {text[:200]}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5,
        )
        
        result = response.choices[0].message.content.strip().lower()
        return "ja" if "ja" in result or "japanese" in result else "en"
    except Exception:
        # Fallback: basic regex check if API fails
        import re
        japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        japanese_chars = len(japanese_pattern.findall(text))
        non_whitespace = len(re.sub(r'\s+', '', text))
        if non_whitespace > 0 and japanese_chars / non_whitespace > 0.1:
            return "ja"
        return "en"
