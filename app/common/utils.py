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
    
    # Truncate at word boundary if possible
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * SNIPPET_WORD_BOUNDARY_THRESHOLD:
        return truncated[:last_space].rstrip()
    return truncated.rstrip()


def format_search_results(
    search_results: list[dict],
    max_length: int = SNIPPET_MAX_LENGTH,
    k: int | None = None
) -> list[dict]:
    """Format search results with snippets.
    
    Args:
        search_results: List of search results with doc_id, content, score, language (already sorted).
        max_length: Maximum length for snippets (default: SNIPPET_MAX_LENGTH).
        k: Maximum number of results to return (default: None, returns all).
        
    Returns:
        List of formatted results with doc_id, snippet, score, language (preserves original order).
    """
    results = []
    for result in search_results:
        snippet = format_snippet(result["content"], max_length=max_length)
        results.append({
            "doc_id": result["doc_id"],
            "snippet": snippet,
            "score": result["score"],
            "language": result["language"],
        })
    # Results are already sorted by store.search(), so we just format and limit
    return results[:k] if k else results



