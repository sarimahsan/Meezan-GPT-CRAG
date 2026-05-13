#!/usr/bin/env python3
"""
Rebuild metadata.json with text content included
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMBEDDINGS_JSONL = Path(__file__).parent / "RAGData" / "embeddings.jsonl"
METADATA_OUTPUT = Path(__file__).parent / "Embeddings_data" / "metadata.json"

def rebuild_metadata():
    """Rebuild metadata.json with text content from embeddings"""
    logger.info(f"Loading embeddings from {EMBEDDINGS_JSONL}")
    
    metadata_list = []
    with open(EMBEDDINGS_JSONL, 'r') as f:
        for i, line in enumerate(f):
            try:
                doc = json.loads(line)
                
                # Extract relevant fields
                metadata = {
                    'id': doc.get('id'),
                    'text': doc.get('text', ''),  # Include actual text content
                    'chars': len(doc.get('text', '')),
                    'metadata': doc.get('metadata', {})
                }
                
                metadata_list.append(metadata)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1} documents")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing line {i}: {e}")
                continue
    
    # Save metadata
    logger.info(f"Saving {len(metadata_list)} metadata records to {METADATA_OUTPUT}")
    with open(METADATA_OUTPUT, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    logger.info("✅ Metadata rebuild complete!")

if __name__ == "__main__":
    rebuild_metadata()
