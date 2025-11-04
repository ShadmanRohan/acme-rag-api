"""Mock LLM service for composing answers."""
from typing import Any



class MockLLMService:
    """Mock LLM service that composes deterministic answers from retrieved snippets."""
    
    def compose_answer(
        self,
        query: str,
        results: list[dict[str, Any]],
        language: str = "en",
    ) -> str:
        """Compose a deterministic mock answer from retrieved snippets.
        
        Args:
            query: The user's query.
            results: List of retrieved results with doc_id, snippet, score, language.
            language: Target language for the answer ('en' or 'ja').
            
        Returns:
            Composed answer string with citations.
        """
        if not results:
            if language == "ja":
                return "申し訳ございませんが、関連する情報が見つかりませんでした。"
            return "I'm sorry, but I couldn't find any relevant information."
        
        # Build answer with citations
        if language == "ja":
            answer_parts = [f"質問「{query}」について、以下の情報が見つかりました：\n\n"]
            for i, result in enumerate(results, 1):
                snippet = result.get("snippet", "")
                doc_id = result.get("doc_id", "")
                answer_parts.append(f"{i}. {snippet} [引用: {doc_id}]\n")
            answer_parts.append("\n上記の情報が質問の回答に役立つことを願っています。")
        else:
            answer_parts = [f"Based on your query \"{query}\", I found the following information:\n\n"]
            for i, result in enumerate(results, 1):
                snippet = result.get("snippet", "")
                doc_id = result.get("doc_id", "")
                answer_parts.append(f"{i}. {snippet} [Citation: {doc_id}]\n")
            answer_parts.append("\nI hope this information helps answer your question.")
        
        return "".join(answer_parts)
    
    def get_citations(self, results: list[dict[str, Any]]) -> list[str]:
        """Extract citations from results.
        
        Args:
            results: List of retrieved results with doc_id.
            
        Returns:
            List of citation doc_ids.
        """
        return [result.get("doc_id", "") for result in results if result.get("doc_id")]


# Global instance
_mock_llm_service: MockLLMService | None = None


def get_llm_service() -> MockLLMService:
    """Get or create the global LLM service instance."""
    global _mock_llm_service
    if _mock_llm_service is None:
        _mock_llm_service = MockLLMService()
    return _mock_llm_service


def reset_llm_service():
    """Reset the global LLM service instance (for testing)."""
    global _mock_llm_service
    _mock_llm_service = None

