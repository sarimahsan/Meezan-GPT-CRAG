# Meezan Bank ChatBot - Frontend Setup

## Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

### 3. Ensure Backend is Running
Make sure the FastAPI backend is running on `http://localhost:8000`:

```bash
cd backend
python main.py
```

## Features

✅ **Real-time Chat Interface** - Clean, responsive chat UI  
✅ **Message History** - Conversation stored in component state  
✅ **Source Attribution** - Clickable sources with match scores (%)  
✅ **Configurable Top-K** - Adjust the number of retrieved documents (1-10)  
✅ **Loading States** - Visual feedback while waiting for responses  
✅ **Mobile Responsive** - Works on desktop and tablets  
✅ **API Integration** - Calls CRAG backend at `http://localhost:8000/query`

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│                   http://localhost:5173              │
├─────────────────────────────────────────────────────┤
│  - Chat interface (App.jsx)                          │
│  - Message display with sources                      │
│  - API client for POST /query                        │
└──────────────────────┬──────────────────────────────┘
                       │
                       │ POST /query
                       │ {query, use_correction, top_k}
                       │
┌──────────────────────▼──────────────────────────────┐
│                   Backend (FastAPI)                  │
│              http://localhost:8000/query             │
├─────────────────────────────────────────────────────┤
│  - CRAG System (retrieval + generation + correction) │
│  - FAISS vector database (304 documents)            │
│  - Groq LLM (llama-3.1-8b-instant)                  │
│  - Returns: {query, answer, context[], metadata}    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
                  Knowledge Base
              (Meezan Bank Documents)
```

## Component Structure

### App.jsx
- **State Management:**
  - `messages[]` - Array of chat messages
  - `loading` - Boolean for API call state
  - `topK` - Number of documents to retrieve (1-10)
  - `inputValue` - Current input text

- **Key Functions:**
  - `handleSendMessage()` - Sends query to API and adds bot response
  - `handleKeyPress()` - Handles Enter to send (Shift+Enter for newline)
  - `scrollToBottom()` - Auto-scrolls to latest message

### API Response Format
```json
{
  "query": "What savings accounts does Meezan Bank offer?",
  "answer": "Meezan Bank offers several savings account types...",
  "context": [
    {
      "id": "doc-123",
      "content": "[full document text]",
      "source": "[document title]",
      "score": 0.85,
      "metadata": {
        "metadata": {
          "source_title": "Meezan Plus Account",
          "source_url": "https://example.com"
        }
      }
    }
  ]
}
```

## Build for Production
```bash
npm run build
```

Output will be in the `dist/` folder.

## Troubleshooting

### "API error: 404"
- Make sure backend is running: `python backend/main.py`
- Check port 8000 is accessible

### Empty responses
- Verify Groq API key is set in backend `.env`
- Check FAISS index exists at `backend/Embeddings_data/faiss_index.bin`
- Verify metadata is loaded: `backend/Embeddings_data/metadata.json`

### Chat not scrolling to bottom
- Check browser console for JS errors
- Ensure `messagesEndRef` is being called

## UI Colors & Theme
- **Primary Gradient:** `#667eea` → `#764ba2` (Purple)
- **Background:** Light gradient (`#f5f7fa` → `#c3cfe2`)
- **User Messages:** Purple gradient
- **Bot Messages:** White with border
- **Source Links:** Purple with hover effects
- **Match Scores:** Blue background with percentage

## Performance Tips
1. **Increase Top-K gradually** - Start with 3, increase if needed
2. **Monitor API response time** - Should be <5 seconds
3. **Browser DevTools** - Check network tab for API calls
4. **Build Optimization** - Use `npm run build` for production

## Next Steps
- [ ] Add message persistence (localStorage)
- [ ] Add voice input support
- [ ] Implement message search/filter
- [ ] Add dark mode toggle
- [ ] Add share conversation feature
- [ ] Real-time streaming responses
