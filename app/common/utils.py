"""Common utility functions."""
from app.config import SNIPPET_MAX_LENGTH, SNIPPET_WORD_BOUNDARY_THRESHOLD


def format_snippet(content: str, max_length: int = None) -> str:
    """Format content as a snippet (≤max_length, word-safe, no newlines).
    
    Args:
        content: Full content to format.
        max_length: Maximum length of snippet (default: SNIPPET_MAX_LENGTH).
        
    Returns:
        Formatted snippet string.
    """
    if max_length is None:
        max_length = SNIPPET_MAX_LENGTH
    
    # Remove newlines and normalize whitespace
    text = " ".join(content.split())
    
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length]
    # Find last space before max_length
    last_space = truncated.rfind(" ")
    if last_space > max_length * SNIPPET_WORD_BOUNDARY_THRESHOLD:  # Only use word boundary if it's not too short
        snippet = truncated[:last_space]
    else:
        snippet = truncated
    
    # Ensure no trailing whitespace
    snippet = snippet.rstrip()
    
    return snippet

