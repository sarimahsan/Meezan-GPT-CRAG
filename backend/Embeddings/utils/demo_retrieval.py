"""
Demo script to test FAISS retriever with a sample query.
Shows how to use the retriever in your CRAG pipeline.
"""

import logging
from typing import List, Tuple

import numpy as np

from faiss_retriever import get_retriever

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("demo")


def demo_retrieve(query_embedding: np.ndarray, k: int = 5) -> None:
    """Demonstrate retrieval with a sample query embedding."""
    LOGGER.info("Initializing retriever...")
    retriever = get_retriever()
    
    LOGGER.info(f"Retriever info: {retriever.info()}")
    
    LOGGER.info(f"\nSearching for top-{k} similar documents...")
    results = retriever.retrieve(query_embedding, k=k)
    
    LOGGER.info(f"\n{'='*80}")
    LOGGER.info(f"Top-{k} Retrieved Results")
    LOGGER.info(f"{'='*80}")
    
    for i, (metadata, similarity) in enumerate(results, 1):
        LOGGER.info(f"\n[{i}] Similarity Score: {similarity:.4f}")
        LOGGER.info(f"    ID: {metadata.get('id', 'N/A')}")
        LOGGER.info(f"    Title: {metadata.get('metadata', {}).get('source_title', 'N/A')}")
        LOGGER.info(f"    URL: {metadata.get('metadata', {}).get('source_url', 'N/A')}")
        LOGGER.info(f"    Chars: {metadata.get('chars', 'N/A')}")


def demo_batch_retrieve(query_embeddings: np.ndarray, k: int = 3) -> None:
    """Demonstrate batch retrieval with multiple queries."""
    LOGGER.info(f"Running batch retrieval on {len(query_embeddings)} queries...")
    retriever = get_retriever()
    
    for idx, query_emb in enumerate(query_embeddings):
        LOGGER.info(f"\n{'='*60}")
        LOGGER.info(f"Query {idx + 1}")
        LOGGER.info(f"{'='*60}")
        
        results = retriever.retrieve(query_emb, k=k)
        for i, (metadata, similarity) in enumerate(results, 1):
            LOGGER.info(
                f"  {i}. [{similarity:.4f}] {metadata.get('id', 'N/A')}"
            )


if __name__ == "__main__":
    # Example 1: Single query (use first embedding from dataset as example)
    LOGGER.info("FAISS Retriever Demo\n")
    
    # Load embeddings to get a sample query
    embeddings = np.load(
        "../Embeddings_data/bge_base_en_v1_5_embeddings.npy"
    )
    
    # Use first embedding as query
    sample_query = embeddings[0]
    LOGGER.info(f"Sample query shape: {sample_query.shape}\n")
    
    demo_retrieve(sample_query, k=5)
    
    # Example 2: Batch retrieval
    LOGGER.info("\n" + "="*80)
    LOGGER.info("BATCH RETRIEVAL DEMO")
    LOGGER.info("="*80)
    sample_queries = embeddings[:3]  # First 3 embeddings
    demo_batch_retrieve(sample_queries, k=3)
