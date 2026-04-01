"""
Setup FAISS index from precomputed embeddings.
Loads embeddings and manifest, builds index, and saves for later retrieval.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np

try:
    import faiss
except ImportError as exc:
    raise SystemExit("FAISS is required. Install with: pip install faiss-cpu") from exc

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("faiss_setup")

# Paths
EMBEDDINGS_DIR = Path(__file__).parent.parent / "Embeddings_data"
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "bge_base_en_v1_5_embeddings.npy"
MANIFEST_FILE = EMBEDDINGS_DIR / "bge_base_en_v1_5_manifest.jsonl"
INDEX_FILE = EMBEDDINGS_DIR / "faiss_index.bin"
METADATA_FILE = EMBEDDINGS_DIR / "metadata.json"


def load_embeddings_and_manifest() -> Tuple[np.ndarray, List[dict]]:
    """Load embeddings array and manifest metadata."""
    LOGGER.info("Loading embeddings from %s", EMBEDDINGS_FILE)
    embeddings = np.load(EMBEDDINGS_FILE)
    LOGGER.info("Loaded embeddings shape: %s", embeddings.shape)
    
    LOGGER.info("Loading manifest from %s", MANIFEST_FILE)
    metadata = []
    with open(MANIFEST_FILE, "r") as f:
        for line in f:
            if line.strip():
                metadata.append(json.loads(line))
    
    LOGGER.info("Loaded %d metadata records", len(metadata))
    
    if len(embeddings) != len(metadata):
        raise ValueError(
            f"Mismatch: {len(embeddings)} embeddings vs {len(metadata)} metadata"
        )
    
    return embeddings, metadata


def create_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """Create FAISS index using L2 distance (Euclidean)."""
    LOGGER.info("Creating FAISS index...")
    
    # Ensure embeddings are float32 (required by FAISS)
    embeddings = embeddings.astype(np.float32)
    
    # Use L2 (Euclidean) distance - good for normalized embeddings
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    
    # Add embeddings to index
    index.add(embeddings)
    LOGGER.info("Index created with %d vectors", index.ntotal)
    
    return index


def save_index_and_metadata(index: faiss.Index, metadata: List[dict]) -> None:
    """Save FAISS index and metadata to disk."""
    LOGGER.info("Saving index to %s", INDEX_FILE)
    faiss.write_index(index, str(INDEX_FILE))
    
    LOGGER.info("Saving metadata to %s", METADATA_FILE)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)
    
    LOGGER.info("✓ Index and metadata saved successfully")


def setup_faiss() -> None:
    """Main setup function."""
    LOGGER.info("=" * 60)
    LOGGER.info("FAISS Index Setup")
    LOGGER.info("=" * 60)
    
    # Load embeddings and metadata
    embeddings, metadata = load_embeddings_and_manifest()
    
    # Create index
    index = create_faiss_index(embeddings)
    
    # Save
    save_index_and_metadata(index, metadata)
    
    LOGGER.info("=" * 60)
    LOGGER.info("Setup complete! Index ready for retrieval.")
    LOGGER.info("=" * 60)


if __name__ == "__main__":
    setup_faiss()
