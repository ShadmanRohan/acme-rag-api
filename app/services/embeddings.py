"""Embeddings service."""
import numpy as np


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        """Initialize the embedding model."""
        # Lazy load to avoid import issues
        self._model = None
        self.dimension = 384  # Dimension for this model
    
    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Use a multilingual model that supports both EN and JA
                self._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            except Exception as e:
                raise RuntimeError(f"Failed to load embedding model: {str(e)}") from e
        return self._model
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for text.
        
        Args:
            text: Text to embed.
            
        Returns:
            Numpy array of embeddings.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)
    
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.dimension


# Global instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def reset_embedding_service():
    """Reset the global embedding service instance (for testing)."""
    global _embedding_service
    _embedding_service = None

