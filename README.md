# Meezan CRAG: Corrective RAG System

A Corrective RAG system for Meezan Bank that provides accurate, context-aware responses using retrieval, generation, and verification layers.

## Architecture

**3-Layer Pipeline:**
1. **Retrieval** - FAISS vector search finds relevant documents
2. **Generation** - LLM generates responses with retrieved context
3. **Correction** - Verifies responses are grounded in retrieved content

## Tech Stack
- **Vector DB:** FAISS (pre-built indexes)
- **Embeddings:** sentence-transformers (`all-mpnet-base-v2`)
- **LLMs:** Groq (free) or OpenAI
- **Backend:** FastAPI
- **Frontend:** React + Vite

## Project Structure
```
backend/
├── main.py              # FastAPI server
├── crag_system.py       # CRAG implementation
├── Embeddings/          # FAISS retrieval
├── RAGData/             # Processed data
├── ScrappedData/        # Pre-scraped web data
├── tests/               # Test files
├── utils/               # Utilities
├── docs/                # Documentation
└── config/              # Setup scripts
```

## Quick Start

```bash
cd backend
python main.py
```

API runs at `http://localhost:8000`
