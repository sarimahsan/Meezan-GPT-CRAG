# RAG Data Pipeline

Your scraped data is now cleaned and prepared for RAG (Retrieval-Augmented Generation) training and embedding generation.

## Data Flow

```
1. scrapping.py     → Scrapes websites and cleans text
                     Removes navigation, menus, forms
                     Chunks content into 500-word segments
                     ↓
2. ScrappedData/    → Raw JSON files with cleaned content
                     Includes full_text + chunks
                     ↓
3. rag_processor.py → Processes chunks for embedding
                     Creates JSONL format
                     Adds metadata to each chunk
                     ↓
4. RAGData/         → Ready for embedding & vector DB
                     embeddings.jsonl (JSONL format)
                     rag_config.json (Configuration)
```

## Usage

### Step 1: Scrape Websites
```bash
source venv/bin/activate
python3 scrapping.py
```

**What it does:**
- Loads JavaScript-rendered content using Selenium
- Removes navigation, forms, and boilerplate
- Cleans text aggressively for RAG
- Chunks content into 500-word overlapping segments

**Output:** `ScrappedData/*.json` files with:
```json
{
  "metadata": {
    "url": "...",
    "title": "...",
    "chunk_count": 5,
    "suitable_for_rag": true
  },
  "content": "Full cleaned text",
  "chunks": ["chunk1", "chunk2", ...]
}
```

### Step 2: Prepare for Embedding
```bash
python3 rag_processor.py
```

**What it does:**
- Reads all JSON files from ScrappedData/
- Extracts chunks with metadata
- Creates JSONL format for embedding
- Generates configuration file

**Output:** `RAGData/` folder with:
- `embeddings.jsonl` - One chunk per line, ready for embedding
- `rag_config.json` - Configuration for your RAG system

### Step 3: Create Embeddings
Use `RAGData/embeddings.jsonl` with any embedding service:

```python
# Example: Using sentence-transformers
from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer('all-MiniLM-L6-v2')

embeddings = []
with open('RAGData/embeddings.jsonl', 'r') as f:
    for line in f:
        doc = json.loads(line)
        embedding = model.encode(doc['text'])
        embeddings.append({
            'id': doc['id'],
            'embedding': embedding.tolist(),
            'metadata': doc['metadata']
        })

# Store embeddings in vector DB (FAISS, Pinecone, etc.)
```

### Step 4: Use in RAG System

```python
# Pseudocode for RAG retrieval
def retrieve_context(query, top_k=5):
    # 1. Embed the query
    query_embedding = model.encode(query)
    
    # 2. Search vector DB for similar chunks
    results = vector_db.search(query_embedding, top_k=top_k)
    
    # 3. Get source information
    context = [result['text'] for result in results]
    sources = [result['metadata']['source_url'] for result in results]
    
    return context, sources
```

## Data Cleaning Features

✅ **Removes:**
- Navigation menus and duplicates
- Form elements and inputs
- Footer content
- Script and style tags
- Boilerplate text
- Extra whitespace

✅ **Preserves:**
- Main content structure
- Section headings
- Key information
- Metadata (source, date)

## Embedding Recommendations

**Recommended Models:**
- `all-MiniLM-L6-v2` (Default) - 384 dimensions, fast
- `all-mpnet-base-v2` - 768 dimensions, more accurate
- `multilingual-e5-base` - Supports 100+ languages

**Vector Databases:**
- FAISS (local, open-source)
- Pinecone (cloud, managed)
- Weaviate (open-source, vector-native DB)
- Milvus (open-source, scalable)

## Configuration

Edit `rag_config.json` to customize:

```json
{
  "embedding_config": {
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "chunk_size": 500,      // Words per chunk
    "chunk_overlap": 50     // Overlap words
  },
  "retrieval_config": {
    "top_k": 5,             // Results to return
    "similarity_threshold": 0.7
  }
}
```

## File Structure

```
backend/
├── scrapping.py           # Web scraper
├── rag_processor.py       # Data processor
├── ScrappedData/          # Raw scraped JSON
│   └── *.json
├── RAGData/               # Processed for embedding
│   ├── embeddings.jsonl   # JSONL format
│   └── rag_config.json    # Configuration
└── venv/                  # Virtual environment
```

## Tips for Better RAG

1. **More Data = Better Results**
   - Add more URLs to `WEBSITES_TO_SCRAPE` in scrapping.py
   - Run scraper multiple times for different sites

2. **Quality Matters**
   - Each chunk should be coherent
   - Adjust chunk_size if results are fragmented
   - Review chunks in RAGData/embeddings.jsonl

3. **Metadata is Useful**
   - Stores source URL and title
   - Use in retrieval ranking
   - Help with result attribution

4. **Test Your RAG**
   - Query common questions about your data
   - Evaluate relevance of retrieved chunks
   - Adjust similarity threshold as needed

## Troubleshooting

**Chunks not making sense?**
- Increase `chunk_size` in rag_processor.py
- Decrease `chunk_overlap` for more separation

**Missing important content?**
- Check ScrappedData JSON `content` field
- May need to adjust cleaning rules in scrapping.py

**Too many irrelevant results?**
- Increase `similarity_threshold` in rag_config.json
- Use a more sophisticated embedding model
- Add reranking layer

---

**Ready to train your RAG!** 🚀
