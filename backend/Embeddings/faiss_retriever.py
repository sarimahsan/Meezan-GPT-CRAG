"""
FAISS-based retriever for semantic search over embeddings.
Provides efficient similarity search and ranking.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    import faiss
except ImportError as exc:
    raise SystemExit("FAISS is required. Install with: pip install faiss-cpu") from exc

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("faiss_retriever")

# Paths
EMBEDDINGS_DIR = Path(__file__).parent.parent / "Embeddings_data"
INDEX_FILE = EMBEDDINGS_DIR / "faiss_index.bin"
METADATA_FILE = EMBEDDINGS_DIR / "metadata.json"


class FAISSRetriever:
    """Retriever using FAISS for efficient similarity search."""
    
    def __init__(self, index_path: Optional[str] = None, metadata_path: Optional[str] = None):
        """
        Initialize retriever with FAISS index and metadata.
        
        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
        """
        self.index_path = Path(index_path) if index_path else INDEX_FILE
        self.metadata_path = Path(metadata_path) if metadata_path else METADATA_FILE
        
        self.index = None
        self.metadata = None
        self._load_index_and_metadata()
    
    def _load_index_and_metadata(self) -> None:
        """Load FAISS index and metadata from disk."""
        if not self.index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {self.index_path}. "
                f"Run setup_faiss.py first."
            )
        
        if not self.metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata not found at {self.metadata_path}. "
                f"Run setup_faiss.py first."
            )
        
        LOGGER.info("Loading FAISS index from %s", self.index_path)
        self.index = faiss.read_index(str(self.index_path))
        
        LOGGER.info("Loading metadata from %s", self.metadata_path)
        with open(self.metadata_path, "r") as f:
            self.metadata = json.load(f)
        
        LOGGER.info("✓ Loaded index with %d vectors", self.index.ntotal)
        LOGGER.info("✓ Loaded %d metadata records", len(self.metadata))
    
    def retrieve(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        return_scores: bool = True
    ) -> List[Tuple[dict, float]]:
        """
        Retrieve top-k similar documents for a query embedding.
        
        Args:
            query_embedding: Query embedding (768-dim numpy array)
            k: Number of results to return
            return_scores: Whether to return similarity scores
        
        Returns:
            List of tuples: (metadata_dict, distance_score)
        """
        if self.index is None:
            raise RuntimeError("Index not loaded. Call _load_index_and_metadata() first.")
        
        # Ensure query is float32
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding, k)
        distances = distances[0]
        indices = indices[0]
        
        # Convert L2 distance to similarity (lower distance = higher similarity)
        # Similarity score: 1 / (1 + distance)
        similarities = 1.0 / (1.0 + distances)
        
        results = []
        for idx, sim in zip(indices, similarities):
            if idx < len(self.metadata):
                results.append((self.metadata[int(idx)], float(sim)))
        
        return results
    
    def retrieve_raw(
        self,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> Tuple[List[dict], np.ndarray]:
        """
        Retrieve top-k results with raw distances.
        
        Args:
            query_embedding: Query embedding (768-dim numpy array)
            k: Number of results to return
        
        Returns:
            Tuple of (metadata_list, distances_array)
        """
        if self.index is None:
            raise RuntimeError("Index not loaded. Call _load_index_and_metadata() first.")
        
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        distances, indices = self.index.search(query_embedding, k)
        
        metadata_list = [self.metadata[int(idx)] for idx in indices[0] if idx < len(self.metadata)]
        return metadata_list, distances[0]
    
    def info(self) -> dict:
        """Get retriever information."""
        return {
            "index_size": self.index.ntotal if self.index else 0,
            "metadata_count": len(self.metadata) if self.metadata else 0,
            "index_path": str(self.index_path),
            "metadata_path": str(self.metadata_path)
        }


# Convenience function
def get_retriever(index_path: Optional[str] = None, metadata_path: Optional[str] = None) -> FAISSRetriever:
    """Get a FAISS retriever instance."""
    return FAISSRetriever(index_path, metadata_path)
