# 🏦 Meezan Bank CRAG ChatBot - Complete Setup Guide

## System Overview

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              MEEZAN BANK CRAG CHATBOT                   ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                          ┃
┃  FRONTEND (React + Vite)           BACKEND (FastAPI)   ┃
┃  Port: 5173                        Port: 8000           ┃
┃  ├─ Chat UI                        ├─ CRAG Pipeline    ┃
┃  ├─ Message History                ├─ FAISS Index      ┃
┃  ├─ Source Display                 ├─ Groq LLM         ┃
┃  └─ Match Scores                   └─ API Endpoints    ┃
┃                                                          ┃
┃                    Knowledge Base                       ┃
┃              (304 Meezan Bank Docs)                     ┃
┃              Embeddings + Metadata                      ┃
┃              FAISS Index                                ┃
┃                                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Prerequisites

- Python 3.9+
- Node.js 16+
- npm or yarn
- Groq API Key ([Get free API key](https://console.groq.com))

## Step 1: Backend Setup (FastAPI + CRAG)

### 1.1 Create Python Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1.2 Install Dependencies
```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `fastapi` - REST API framework
- `sentence-transformers` - Embeddings (768-dim)
- `faiss-cpu` - Vector database
- `groq` - Free LLM provider
- `python-dotenv` - Environment variables
- `uvicorn` - ASGI server

### 1.3 Configure Environment
Create `.env` file in `backend/` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
```

**Get Groq API Key:**
1. Visit https://console.groq.com
2. Sign up (free)
3. Create API key
4. Paste in `.env`

### 1.4 Verify FAISS and Metadata
Check these files exist:
```
backend/Embeddings_data/
├── faiss_index.bin          # 304 docs indexed
├── metadata.json            # Text + metadata
├── bge_base_en_v1_5_embeddings.npy
└── bge_base_en_v1_5_manifest.jsonl
```

If missing, rebuild:
```bash
cd backend
python rebuild_metadata.py
```

### 1.5 Start Backend Server
```bash
cd backend
python main.py
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 [CTRL+C to quit]
```

**Health Check:**
```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy", "message": "CRAG System is ready"}
```

---

## Step 2: Frontend Setup (React + Vite)

### 2.1 Install Dependencies
```bash
cd frontend
npm install
```

### 2.2 Start Development Server
```bash
npm run dev
```

**Output:**
```
  ➜  Local:   http://localhost:5173/
```

### 2.3 Open in Browser
Navigate to: **http://localhost:5173**

You should see:
- 🏦 **Meezan Bank ChatBot** header
- Purple gradient theme
- Welcome message
- Input field with "Top-K" control

---

## Step 3: Test the System

### 3.1 Using the Chat UI
1. Type a question: "What savings accounts does Meezan Bank offer?"
2. Click send (or press Enter)
3. Wait for response (usually <5 seconds)
4. View answer with sources

### 3.2 Using API Directly
```bash
# Test with curl
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Apni Car?",
    "use_correction": false,
    "top_k": 3
  }'
```

### 3.3 API Response Example
```json
{
  "query": "What is Apni Car?",
  "answer": "Apni Car is an Islamic financing option offered by Meezan Bank for purchasing vehicles...",
  "context": [
    {
      "id": "doc_001",
      "content": "Apni Car is a car financing solution...",
      "source": "Apni Car | Roshan Car | Meezan Bank",
      "score": 0.87,
      "metadata": {...}
    }
  ]
}
```

---

## Architecture Deep Dive

### CRAG Pipeline (Corrective RAG)

```
       USER QUERY
            │
            ▼
    ┌─────────────────┐
    │  RETRIEVER      │
    │  ───────────    │
    │  - FAISS Index  │
    │  - Top-K docs   │
    │  - Score: 0.35+ │
    └────────┬────────┘
             │
            ▼
    ┌─────────────────┐
    │  GENERATOR      │
    │  ───────────    │
    │  - Groq LLM     │
    │  - llama-3.1-8b │
    │  - Format text  │
    └────────┬────────┘
             │
            ▼
    ┌─────────────────┐
    │  CORRECTOR      │
    │  ───────────    │
    │  - Validate     │
    │  - Extract      │
    │  - Format JSON  │
    └────────┬────────┘
             │
            ▼
         RESPONSE
```

### Components

**CRAGRetriever**
- Uses FAISS index to find similar documents
- Returns (metadata, score) tuples sorted by relevance
- Threshold: 0.35 cosine similarity

**CRAGGenerator**
- Takes retrieved documents + query
- Generates answer using Groq LLM
- Supports both Groq and OpenAI APIs

**CRAGCorrector**
- Validates LLM output format
- Extracts sources from metadata
- Returns clean JSON response

**CRAGSystem**
- Orchestrates all three stages
- Handles errors gracefully
- Caches metadata on first load

---

## File Structure

```
Meezan-GPT-CRAG/
├── backend/
│   ├── main.py                          # FastAPI server (267 lines)
│   ├── crag_system.py                   # CRAG implementation (400+ lines)
│   ├── rebuild_metadata.py              # Metadata rebuilding script
│   ├── requirements.txt                 # Python dependencies
│   ├── Embeddings_data/
│   │   ├── faiss_index.bin              # Vector index (304 docs)
│   │   └── metadata.json                # Document metadata + text
│   └── .env                             # GROQ_API_KEY, LLM_PROVIDER
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                      # Chat component (React)
│   │   ├── App.css                      # Chat styling (400+ lines)
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json                     # npm dependencies
│   ├── vite.config.js
│   └── index.html
│
├── README.md                            # Project overview
├── FRONTEND_SETUP.md                    # Frontend guide
└── STARTUP_GUIDE.md                     # This file
```

---

## API Endpoints

### 1. Health Check
```bash
GET /health
```
Response:
```json
{
  "status": "healthy",
  "message": "CRAG System is ready"
}
```

### 2. Full CRAG Query
```bash
POST /query
Content-Type: application/json

{
  "query": "What savings accounts does Meezan Bank offer?",
  "use_correction": false,
  "top_k": 3
}
```

Parameters:
- `query` (string, required) - User question
- `use_correction` (boolean, optional) - Enable response validation (default: false)
- `top_k` (integer, optional) - Number of documents to retrieve (default: 3, max: 10)

### 3. Fast Retrieval Only
```bash
POST /query-fast
Content-Type: application/json

{
  "query": "...",
  "top_k": 3
}
```

Returns only retrieved documents without LLM generation.

---

## Common Issues & Solutions

### Issue 1: "Connection refused" on port 8000
**Problem:** Backend not running  
**Solution:**
```bash
cd backend
python main.py
```

### Issue 2: "GROQ_API_KEY not found"
**Problem:** Missing .env file  
**Solution:**
```bash
cd backend
echo "GROQ_API_KEY=your_key_here" > .env
echo "LLM_PROVIDER=groq" >> .env
```

### Issue 3: Empty API responses
**Problem:** Metadata file is empty  
**Solution:**
```bash
cd backend
python rebuild_metadata.py
```

### Issue 4: "Module not found" errors
**Problem:** Dependencies not installed  
**Solution:**
```bash
cd backend
pip install -r requirements.txt
cd ../frontend
npm install
```

### Issue 5: Slow responses (>10 seconds)
**Problem:** Network/API latency  
**Solution:**
- Reduce `top_k` (smaller number = faster)
- Check Groq API status (console.groq.com)
- Monitor network in browser (F12 → Network tab)

### Issue 6: Frontend won't connect to backend
**Problem:** CORS issue or backend not accessible  
**Solution:**
1. Ensure backend running on http://localhost:8000
2. Check browser console (F12) for errors
3. Verify firewall isn't blocking port 8000

---

## Performance Tuning

### Optimize Response Time
| Parameter | Impact | Recommendation |
|-----------|--------|-----------------|
| `top_k` | Higher = slower | Start at 3, increase if needed |
| `use_correction` | Adds validation step | Disable for speed |
| Groq vs OpenAI | Free vs Paid | Use Groq for free tier |

### Monitor Requests
1. Open browser DevTools (F12)
2. Go to Network tab
3. Send a query
4. Check request timing:
   - Retrieval: <1 second
   - Generation: 2-4 seconds
   - Total: <5 seconds

---

## Deployment

### Local Network Access
```bash
# Run backend on 0.0.0.0 instead of 127.0.0.1
# Edit main.py:
uvicorn.run(app, host="0.0.0.0", port=8000)

# Update frontend API endpoint to your machine IP
# Edit App.jsx:
const response = await fetch('http://YOUR_IP:8000/query', ...)
```

### Production Deployment
1. **Backend:** Deploy FastAPI to cloud (AWS, Azure, Google Cloud)
2. **Frontend:** Build and deploy to CDN (Vercel, Netlify)
3. **Database:** Keep FAISS index as file or use vector DB service
4. **Scaling:** Implement caching and rate limiting

---

## Support & Debugging

### Enable Debug Logging
```bash
# Backend
export LOGLEVEL=DEBUG
python backend/main.py

# Frontend (browser console)
# F12 → Console tab → Check for errors
```

### Check Resource Health
```bash
# FAISS index size
ls -lh backend/Embeddings_data/faiss_index.bin

# Metadata file
cat backend/Embeddings_data/metadata.json | head -20

# Backend logs
# Check terminal where main.py is running
```

### Test Components Individually
```bash
# Test retrieval only
curl -X POST http://localhost:8000/query-fast \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 1}'

# Check Groq API status
python -c "from groq import Groq; print('Groq SDK loaded')"
```

---

## Next Steps

✅ **Completed:**
- [x] Backend CRAG system
- [x] FastAPI REST API
- [x] Groq LLM integration
- [x] FAISS vector index (304 docs)
- [x] React frontend
- [x] Chat UI with sources

🚀 **Future Enhancements:**
- [ ] Message persistence (localStorage)
- [ ] Dark mode toggle
- [ ] Voice input/output
- [ ] Message search
- [ ] Conversation export (PDF/JSON)
- [ ] Real-time response streaming
- [ ] Multi-language support
- [ ] Analytics dashboard

---

## Quick Checklist

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python main.py
# ✅ Running on http://localhost:8000

# Terminal 2: Frontend
cd frontend
npm install  # first time only
npm run dev
# ✅ Running on http://localhost:5173

# Terminal 3: Test
curl http://localhost:8000/health
# ✅ {"status": "healthy", "message": "CRAG System is ready"}

# Browser
# ✅ Open http://localhost:5173
# ✅ Type a question
# ✅ See answer with sources
```

---

## Contact & Support

- **Project:** Meezan Bank CRAG ChatBot
- **Architecture:** Corrective RAG (Retrieval + Generation + Correction)
- **LLM:** Groq (Free) / OpenAI (Paid)
- **Vector DB:** FAISS (304 documents)
- **Frontend:** React + Vite
- **Backend:** FastAPI + UVicorn

Happy chatting! 🚀
