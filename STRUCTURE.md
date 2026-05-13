# Project Structure

## Root Level
```
backend/                    # Backend application
frontend/                   # Frontend application
requirement.txt             # Single dependency file (consolidated)
README.md                   # Project documentation
```

## Backend Organization

### Core Application
```
backend/
├── main.py               # FastAPI app entry point
├── crag_system.py        # CRAG implementation (Retriever, Generator, Corrector)
└── requirements.txt      # Backend dependencies
```

### Embeddings & Retrieval
```
backend/Embeddings/
├── __init__.py
├── faiss_retriever.py              # Core FAISS vector search
├── Embeddings_data/                # Pre-built FAISS indexes
│   ├── bge_base_en_v1_5_embeddings.npy
│   ├── bge_base_en_v1_5_manifest.jsonl
│   └── metadata.json
└── utils/                          # Demo and validation scripts
    ├── __init__.py
    ├── demo_retrieval.py           # Demo retrieval examples
    ├── create_embeddings.py        # Embedding generation
    ├── validate_data.py            # Data validation
    └── validate_embeddings_consistency.py  # Embedding validation
```

### Data Management
```
backend/
├── RAGData/                # RAG-processed data ready for embeddings
│   ├── embeddings.jsonl
│   └── rag_config.json
├── ScrappedData/           # Raw scraped web data (JSON)
└── WebScrapping/           # Web scraping scripts
```

### Configuration & Setup
```
backend/config/
├── __init__.py
└── setup_embeddings.py     # FAISS index setup script
```

### Utilities
```
backend/utils/
├── __init__.py
├── analyze_metrics.py      # Performance metrics analysis
├── monitor_health.py       # System health monitoring
└── rebuild_metadata.py     # Metadata rebuilding
```

### Tests
```
backend/tests/
├── __init__.py
├── test.py                 # General tests
├── test_crag.py           # CRAG-specific tests
└── evaluate_crag.py       # CRAG evaluation suite
```

### Documentation
```
backend/docs/
├── __init__.py
├── CRAG_QUICK_START.md    # Quick start guide
└── RAG_GUIDE.md           # RAG data pipeline guide
```

## Frontend
```
frontend/
├── src/                    # React/Vue source code
├── package.json           # Frontend dependencies
├── vite.config.js         # Vite configuration
└── index.html             # Entry HTML
```

## Usage Examples

### Import CRAG System
```python
from backend.crag_system import CRAGSystem
from backend.Embeddings.faiss_retriever import FAISSRetriever
```

### Import Test Files
```python
from backend.tests.test_crag import TestCRAG
from backend.tests.evaluate_crag import CRAGEvaluator
```

### Import Utilities
```python
from backend.utils.analyze_metrics import MetricsAnalyzer
from backend.utils.monitor_health import HealthMonitor
```

### Import Embeddings Utils
```python
from backend.Embeddings.utils.demo_retrieval import demo_retrieval
from backend.Embeddings.utils.validate_embeddings_consistency import validate_embeddings
```
