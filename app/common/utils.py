"""Common utility functions."""


def format_snippet(content: str, max_length: int = 160) -> str:
    """Format content as a snippet (≤max_length, word-safe, no newlines).
    
    Args:
        content: Full content to format.
        max_length: Maximum length of snippet (default: 160).
        
    Returns:
        Formatted snippet string.
    """
    # Remove newlines and normalize whitespace
    text = " ".join(content.split())
    
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length]
    # Find last space before max_length
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.7:  # Only use word boundary if it's not too short
        snippet = truncated[:last_space]
    else:
        snippet = truncated
    
    # Ensure no trailing whitespace
    snippet = snippet.rstrip()
    
    return snippet

