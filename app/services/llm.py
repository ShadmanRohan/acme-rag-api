"""LLM service for composing answers using OpenAI API."""
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI

# Load environment variables
load_dotenv()


class LLMService:
    """LLM service that composes answers from retrieved snippets using OpenAI API."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=self.api_key)
    
    def compose_answer(
        self,
        query: str,
        results: list[dict[str, Any]],
        language: str = "en",
    ) -> str:
        """Compose an answer from retrieved snippets using OpenAI API.
        
        Args:
            query: The user's query.
            results: List of retrieved results with doc_id, snippet, score, language.
            language: Target language for the answer ('en' or 'ja').
            
        Returns:
            Composed answer string with citations.
            
        Raises:
            HTTPException: If OpenAI API call fails.
        """
        if not results:
            if language == "ja":
                return "申し訳ございませんが、関連する情報が見つかりませんでした。"
            return "I'm sorry, but I couldn't find any relevant information."
        
        try:
            # Build context from retrieved snippets
            context_parts = []
            citations_map = {}
            for i, result in enumerate(results, 1):
                snippet = result.get("snippet", "")
                doc_id = result.get("doc_id", "")
                citations_map[f"[doc_{i}]"] = doc_id
                context_parts.append(f"[doc_{i}] {snippet}")
            
            context = "\n\n".join(context_parts)
            
            # Build prompt based on language
            if language == "ja":
                system_prompt = "あなたは質問に答えるアシスタントです。提供されたコンテキスト情報を使用して、質問に正確に答えてください。各回答には[doc_N]形式の引用を含めてください。"
                user_prompt = f"質問: {query}\n\nコンテキスト情報:\n{context}\n\n上記のコンテキスト情報を使用して質問に答えてください。"
            else:
                system_prompt = "You are a helpful assistant that answers questions using the provided context. Include citations in the format [doc_N] for each piece of information used."
                user_prompt = f"Question: {query}\n\nContext information:\n{context}\n\nPlease answer the question using the context information above."
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using cost-effective model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # Lower temperature for more deterministic answers
                max_tokens=1000,
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Replace [doc_N] references with actual doc_ids
            for ref, doc_id in citations_map.items():
                answer = answer.replace(ref, f"[Citation: {doc_id}]")
            
            return answer
            
        except Exception as e:
            # Raise HTTP exception if API call fails
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate answer using OpenAI API: {str(e)}"
            )
    
    def get_citations(self, results: list[dict[str, Any]]) -> list[str]:
        """Extract citations from results.
        
        Args:
            results: List of retrieved results with doc_id.
            
        Returns:
            List of citation doc_ids.
        """
        return [result.get("doc_id", "") for result in results if result.get("doc_id")]


# Global instance
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance.
    
    Raises:
        ValueError: If OPENAI_API_KEY is not configured.
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def reset_llm_service():
    """Reset the global LLM service instance (for testing)."""
    global _llm_service
    _llm_service = None
