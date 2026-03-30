"""
RAG Data Processor
Prepares scraped data for embedding and RAG model training
"""

import json
import os
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRAPPED_DATA_FOLDER = "ScrappedData"
OUTPUT_FOLDER = "RAGData"


def create_output_folder():
    """Create RAGData folder"""
    Path(OUTPUT_FOLDER).mkdir(exist_ok=True)
    logger.info(f"RAG data folder ready: {OUTPUT_FOLDER}")


def load_scraped_data(filename):
    """Load JSON file from ScrappedData folder"""
    filepath = os.path.join(SCRAPPED_DATA_FOLDER, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return None


def prepare_for_embedding(data):
    """
    Prepare data for embedding/RAG training
    Returns: list of documents ready for embedding
    """
    if not data or 'chunks' not in data:
        return []
    
    documents = []
    metadata = data.get('metadata', {})
    chunks = data.get('chunks', [])
    
    for idx, chunk in enumerate(chunks):
        doc = {
            "id": f"{metadata.get('title', 'page')}_chunk_{idx}",
            "text": chunk,
            "metadata": {
                "source_url": metadata.get('url'),
                "source_title": metadata.get('title'),
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "scraped_at": metadata.get('scraped_at')
            }
        }
        documents.append(doc)
    
    return documents


def export_for_embedding(output_format='jsonl'):
    """
    Export all scraped data in format ready for embedding
    Supports: jsonl (default), json, csv
    """
    create_output_folder()
    
    logger.info("=" * 70)
    logger.info("Preparing data for embedding...")
    logger.info("=" * 70)
    
    all_documents = []
    files_processed = 0
    total_chunks = 0
    
    # Process all JSON files in ScrappedData
    if not os.path.exists(SCRAPPED_DATA_FOLDER):
        logger.warning(f"No {SCRAPPED_DATA_FOLDER} folder found!")
        return
    
    for filename in os.listdir(SCRAPPED_DATA_FOLDER):
        if filename.endswith('.json'):
            logger.info(f"Processing: {filename}")
            data = load_scraped_data(filename)
            
            if data:
                documents = prepare_for_embedding(data)
                all_documents.extend(documents)
                chunks_count = len(documents)
                total_chunks += chunks_count
                files_processed += 1
                logger.info(f"  ✓ Extracted {chunks_count} chunks")
    
    # Export based on format
    if output_format == 'jsonl':
        output_file = os.path.join(OUTPUT_FOLDER, "embeddings.jsonl")
        with open(output_file, 'w', encoding='utf-8') as f:
            for doc in all_documents:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        logger.info(f"✓ Exported to: {output_file}")
    
    elif output_format == 'json':
        output_file = os.path.join(OUTPUT_FOLDER, "embeddings.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_documents, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ Exported to: {output_file}")
    
    # Summary
    logger.info("=" * 70)
    logger.info(f"Data Preparation Complete!")
    logger.info(f"Files processed: {files_processed}")
    logger.info(f"Total chunks: {total_chunks}")
    logger.info(f"Output folder: {os.path.abspath(OUTPUT_FOLDER)}")
    logger.info("=" * 70)
    
    return all_documents


def generate_config_file():
    """Generate a config file for RAG model training"""
    config = {
        "rag_config": {
            "data_source": "ScrappedData",
            "prepared_data": "RAGData/embeddings.jsonl",
            "embedding_config": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "embedding_dimension": 384,
                "chunk_size": 500,
                "chunk_overlap": 50
            },
            "retrieval_config": {
                "top_k": 5,
                "similarity_threshold": 0.7,
                "reranking": True
            },
            "vector_store": {
                "type": "faiss",
                "index_path": "indexes/faiss.index"
            }
        },
        "prepared_at": datetime.now().isoformat(),
        "instructions": [
            "1. Use the embeddings.jsonl file for creating vector embeddings",
            "2. Each line is a JSON document with 'id', 'text', and 'metadata'",
            "3. Recommended embedding model: sentence-transformers/all-MiniLM-L6-v2",
            "4. Store embeddings in a vector database (FAISS, Pinecone, etc.)",
            "5. Use the 'id' field as the unique identifier for each chunk",
            "6. The 'metadata' contains source and context information"
        ]
    }
    
    config_file = os.path.join(OUTPUT_FOLDER, "rag_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✓ Config file created: {config_file}")


if __name__ == "__main__":
    logger.info("RAG Data Processor Started")
    
    # Process and export data
    documents = export_for_embedding('jsonl')
    
    # Generate configuration
    generate_config_file()
    
    logger.info("Ready for embedding and RAG training!")
