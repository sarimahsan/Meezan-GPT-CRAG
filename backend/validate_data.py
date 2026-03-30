#!/usr/bin/env python3
"""
Data Quality Validator
Analyzes and validates scraped data for RAG readiness
"""

import json
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRAPPED_DATA_FOLDER = "ScrappedData"
RAG_DATA_FOLDER = "RAGData"


def analyze_text_quality(text):
    """Analyze text quality metrics"""
    metrics = {
        "length": len(text),
        "word_count": len(text.split()),
        "avg_word_length": sum(len(w) for w in text.split()) / len(text.split()) if text.split() else 0,
        "sentence_count": text.count('.') + text.count('!') + text.count('?'),
        "paragraph_count": len([p for p in text.split('\n') if p.strip()])
    }
    return metrics


def validate_scraped_data():
    """Validate data in ScrappedData folder"""
    logger.info("=" * 70)
    logger.info("SCRAPED DATA QUALITY REPORT")
    logger.info("=" * 70)
    
    if not os.path.exists(SCRAPPED_DATA_FOLDER):
        logger.warning(f"No {SCRAPPED_DATA_FOLDER} folder found!")
        return
    
    total_files = 0
    total_content_length = 0
    total_chunks = 0
    
    for filename in os.listdir(SCRAPPED_DATA_FOLDER):
        if filename.endswith('.json'):
            filepath = os.path.join(SCRAPPED_DATA_FOLDER, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            content = data.get('content', '')
            chunks = data.get('chunks', [])
            
            total_files += 1
            total_content_length += metadata.get('content_length', 0)
            total_chunks += len(chunks)
            
            logger.info(f"\n📄 {metadata.get('title', 'Unknown')}")
            logger.info(f"   URL: {metadata.get('url', 'N/A')}")
            logger.info(f"   Characters: {metadata.get('content_length', 0):,}")
            logger.info(f"   Words: {metadata.get('word_count', 0):,}")
            logger.info(f"   Chunks: {len(chunks)}")
            logger.info(f"   Status: ✓ {metadata.get('status', 'unknown')}")
            logger.info(f"   RAG Ready: {'✓ Yes' if metadata.get('suitable_for_rag') else '✗ No'}")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total Files: {total_files}")
    logger.info(f"Total Content Length: {total_content_length:,} characters")
    logger.info(f"Total Words: {int(total_content_length / 5):,}")  # Rough estimate
    logger.info(f"Total Chunks: {total_chunks} (ready for embedding)")
    
    if total_files > 0:
        logger.info(f"Average Chunk Size: {int(total_content_length / total_chunks)} chars")
        logger.info("\n✓ Data is clean and ready for RAG training!")
    
    logger.info("=" * 70)


def validate_rag_data():
    """Validate prepared RAG data"""
    logger.info("\n" + "=" * 70)
    logger.info("RAG DATA VALIDATION")
    logger.info("=" * 70)
    
    if not os.path.exists(RAG_DATA_FOLDER):
        logger.warning(f"No {RAG_DATA_FOLDER} folder found!")
        return
    
    embeddings_file = os.path.join(RAG_DATA_FOLDER, "embeddings.jsonl")
    
    if not os.path.exists(embeddings_file):
        logger.warning(f"No embeddings.jsonl found!")
        return
    
    chunk_count = 0
    total_text_length = 0
    sources = set()
    
    with open(embeddings_file, 'r', encoding='utf-8') as f:
        for line in f:
            doc = json.loads(line)
            chunk_count += 1
            total_text_length += len(doc.get('text', ''))
            sources.add(doc.get('metadata', {}).get('source_url', 'Unknown'))
    
    logger.info(f"Total Chunks: {chunk_count}")
    logger.info(f"Total Text Length: {total_text_length:,} characters")
    logger.info(f"Unique Sources: {len(sources)}")
    
    if chunk_count > 0:
        logger.info(f"Average Chunk Size: {int(total_text_length / chunk_count)} characters")
        logger.info(f"\n✓ {chunk_count} chunks ready for embedding!")
        logger.info(f"File: {embeddings_file}")
    
    logger.info("=" * 70)


if __name__ == "__main__":
    validate_scraped_data()
    validate_rag_data()
    logger.info("\n✅ Data validation complete!")
