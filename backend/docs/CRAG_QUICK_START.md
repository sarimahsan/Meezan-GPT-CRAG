# CRAG System - Quick Start Guide

You've successfully set up the **Corrective RAG (CRAG) System** for Meezan Bank. Here's how to use it.

## 📁 What You Now Have

```
backend/
├── crag_system.py      ← CRAG core (Retrieval + Generation + Correction)
├── main.py             ← FastAPI backend
├── Embeddings/
│   └── faiss_retriever.py  ← FAISS vector search
└── Embeddings_data/    ← Pre-built embeddings & index
```

## 🚀 Getting Started

### Step 1: Install Dependencies

```bash
cd /media/syed-sarim-ahsan/Storage1/Meezan-GPT-CRAG/backend
source venv/bin/activate

# Install required packages
pip install fastapi uvicorn python-dotenv openai sentence-transformers
```

### Step 2: Set Up Environment Variables

Create/update `.env` file in `backend/` directory:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

Get your API key from: https://platform.openai.com/account/api-keys

### Step 3: Test the CRAG System (Standalone)

```bash
# Test without API
python crag_system.py
```

Expected output:
```
==========================================
CRAG System Test
==========================================
Query: What is Meezan Bank?

Answer: [LLM generated answer based on your data]

Context Retrieved: 5 documents
Verification - Grounded: True
Confidence: 0.95
==========================================
```

---

## 🌐 Use CRAG as REST API

### Start the API Server

```bash
# From backend/ directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation will be available at:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

#### 1. **Health Check**
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "message": "CRAG System is ready"
}
```

#### 2. **Full CRAG Query (with Correction)**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Meezan Bank's vision?",
    "use_correction": true,
    "top_k": 5
  }'
```

Response:
```json
{
  "query": "What is Meezan Bank's vision?",
  "answer": "Based on the context provided, Meezan Bank's vision is...",
  "context": [
    {
      "id": 0,
      "content": "Meezan Bank is...",
      "source": "Company Overview",
      "score": 0.95,
      "metadata": {...}
    }
  ],
  "verification": {
    "is_grounded": true,
    "confidence": 0.92,
    "issues": [],
    "suggestions": "Response is well-grounded in the context"
  },
  "status": "success"
}
```

#### 3. **Fast Query (without Correction)**
Faster response, skips verification:
```bash
curl -X POST http://localhost:8000/query-fast \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about savings accounts",
    "top_k": 3
  }'
```

---

## 🔄 CRAG Pipeline Explained

```
┌─────────────────────────────────────────────────────────┐
│                    USER QUERY                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   RETRIEVAL (FAISS)        │
        │ Search embeddings index    │
        │ Get top-k relevant chunks  │
        └────────┬───────────────────┘
                 │ (Retrieved Documents)
                 ▼
        ┌────────────────────────────┐
        │   GENERATION (LLM)         │
        │ Build context prompt       │
        │ Call OpenAI API            │
        │ Generate response          │
        └────────┬───────────────────┘
                 │ (Generated Response)
                 ▼
        ┌────────────────────────────┐
        │   CORRECTION (Validator)   │
        │ Verify response grounded   │
        │ Check for hallucinations   │
        │ Provide confidence score   │
        └────────┬───────────────────┘
                 │ (Verified + Safe)
                 ▼
        ┌────────────────────────────┐
        │   FINAL RESPONSE           │
        │ Answer + Context + Score   │
        └────────────────────────────┘
```

---

## 📊 Key Features

| Feature | Whether You Have It |
|---------|-------------------|
| **Retrieval**: FAISS vector search | ✅ Yes |
| **Generation**: LLM (OpenAI) | ✅ Yes |
| **Correction**: Response validation | ✅ Yes |
| **API**: FastAPI endpoint | ✅ Yes |
| **CORS**: Allow browser requests | ✅ Yes |
| **Logging**: Request tracking | ✅ Yes |

---

## 🐛 Troubleshooting

### 1. **"FAISS index not found"**
```
Solution: Ensure you've run setup_faiss.py and embeddings are created
Run: python Embeddings/setup_faiss.py
```

### 2. **"No OpenAI API key found"**
```
Solution: Set OPENAI_API_KEY in .env file
Get key: https://platform.openai.com/account/api-keys
```

### 3. **"CRAG System not initialized"**
```
Solution: Wait for startup to complete, check logs for errors
```

### 4. **Slow responses**
```
Solution: Use /query-fast endpoint (no correction)
Or increase timeout in client
```

---

## 🔧 Configuration Options

Edit in `crag_system.py`:

```python
# LLM Model
LLM_MODEL = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo"

# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/bge-base-en-v1.5"

# Retriever k value
CRAG.retriever.top_k = 5  # More = slower but more context
```

---

## 📱 Next Steps

### **Phase 1: Test API** (Current)
- [x] Build CRAG system
- [x] Create FastAPI backend
- [ ] Test all endpoints
- [ ] Verify responses quality

### **Phase 2: Frontend Integration**
- [ ] Update React frontend to call `/query` endpoint
- [ ] Build chat interface
- [ ] Add streaming responses

### **Phase 3: Optimization**
- [ ] Fine-tune retrieval (adjust top_k)
- [ ] Improve prompts
- [ ] Cache embeddings
- [ ] Add conversation history

---

## 💡 Example: Using CRAG in Python

```python
from crag_system import CRAGSystem
from Embeddings.faiss_retriever import FAISSRetriever

# Initialize
faiss = FAISSRetriever()
crag = CRAGSystem(faiss, top_k=5)

# Ask a question
result = crag.query("What services does Meezan Bank offer?")

# Access results
print(f"Answer: {result['answer']}")
print(f"Sources: {[doc['source'] for doc in result['context']]}")
print(f"Grounded: {result['verification']['is_grounded']}")
```

---

## 🎯 What's Working Now

✅ **Retrieval**: FAISS finds relevant documents
✅ **Generation**: LLM creates intelligent responses
✅ **Correction**: System validates answers
✅ **API**: REST endpoints ready
✅ **Logging**: Full request tracking

---

Start with testing the API, then integrate with your React frontend! 🚀
