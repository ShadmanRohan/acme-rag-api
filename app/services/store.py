"""FAISS store service."""
import hashlib
import pickle
from typing import Any

import faiss
import numpy as np

from app.config import (
    DATA_DIR,
    DEFAULT_K,
    DOC_ID_PREFIX,
    FAISS_INDEX_TYPE,
    INDEX_FILE,
    METADATA_FILE,
    SEARCH_K_MULTIPLIER,
)
from app.services.embeddings import get_embedding_service


class StoreService:
    """Service for storing and retrieving embeddings with FAISS."""
    
    def __init__(self):
        """Initialize the store service."""
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = INDEX_FILE
        self.metadata_file = METADATA_FILE
        
        self.embedding_service = get_embedding_service()
        self.dimension = self.embedding_service.embedding_dimension
        
        self.index: faiss.IndexFlatL2 | None = None
        self.metadata: list[dict[str, Any]] = []
        
        self._load()
    
    def _load(self):
        """Load existing index and metadata."""
        if self.index_file.exists() and self.metadata_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.metadata_file, "rb") as f:
                    self.metadata = pickle.load(f)
            except Exception:
                # If loading fails, start fresh
                self.index = None
                self.metadata = []
        else:
            self.index = None
            self.metadata = []
    
    def _save(self):
        """Save index and metadata to disk."""
        # Ensure directory exists before saving
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_file))
        with open(self.metadata_file, "wb") as f:
            pickle.dump(self.metadata, f)
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def add(self, content: str, language: str) -> dict[str, Any]:
        """Add content to the store.
        
        Args:
            content: Text content to add.
            language: Language code ('en' or 'ja').
            
        Returns:
            Dict with doc_id, hash, and whether it was a new addition.
        """
        content_hash = self._compute_hash(content)
        
        # Check if content already exists (idempotent by hash)
        for meta in self.metadata:
            if meta.get("hash") == content_hash:
                # Content already exists, return existing doc_id
                return {
                    "doc_id": meta["doc_id"],
                    "hash": content_hash,
                    "added": False,
                }
        
        # Generate embedding
        embedding = self.embedding_service.embed(content)
        
        # Initialize index if needed
        if self.index is None:
            index_class = getattr(faiss, FAISS_INDEX_TYPE)
            self.index = index_class(self.dimension)
        
        # Add embedding to index
        embedding_array = embedding.reshape(1, -1)
        self.index.add(embedding_array)
        
        # Create metadata
        doc_id = f"{DOC_ID_PREFIX}{len(self.metadata)}"
        metadata_entry = {
            "doc_id": doc_id,
            "hash": content_hash,
            "language": language,
            "content": content,
            "index": len(self.metadata),
        }
        
        self.metadata.append(metadata_entry)
        self._save()
        
        return {
            "doc_id": doc_id,
            "hash": content_hash,
            "added": True,
        }
    
    def search(self, query_embedding: np.ndarray, k: int = None) -> list[dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector.
            k: Number of results to return.
            
        Returns:
            List of results with doc_id, score, and metadata, sorted by score (ascending, lower is better).
        """
        if k is None:
            k = DEFAULT_K
        if self.index is None or len(self.metadata) == 0:
            return []
        
        query_array = query_embedding.reshape(1, -1)
        # Search for more results than needed to handle ties
        search_k = min(k * SEARCH_K_MULTIPLIER, len(self.metadata))
        distances, indices = self.index.search(query_array, search_k)
        
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            
            meta = self.metadata[idx]
            results.append({
                "doc_id": meta["doc_id"],
                "score": float(distance),
                "language": meta["language"],
                "content": meta["content"],
            })
        
        # Sort by score (ascending, lower distance is better) then by doc_id for deterministic ordering
        results.sort(key=lambda x: (x["score"], x["doc_id"]))
        
        # Return top k results
        return results[:k]
    
    def get_size(self) -> int:
        """Get the number of documents in the store."""
        return len(self.metadata) if self.metadata else 0


# Global instance
_store_service: StoreService | None = None


def get_store_service() -> StoreService:
    """Get or create the global store service instance."""
    global _store_service
    if _store_service is None:
        _store_service = StoreService()
    return _store_service


def reset_store_service():
    """Reset the global store service instance (for testing)."""
    global _store_service
    _store_service = None

