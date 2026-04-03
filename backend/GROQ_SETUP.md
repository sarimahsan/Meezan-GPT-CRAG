# 🚀 Switching to Groq (Free LLM)

## Why Groq?
- ✅ **FREE** - No credit card needed
- ⚡ **FAST** - Faster than OpenAI
- 🎯 **Easy** - Works out of the box
- 💰 **Generous** - High rate limits on free tier

## Get Your Free Groq API Key

### Step 1: Go to Groq Console
```
https://console.groq.com
```

### Step 2: Sign Up (if needed)
- Click "Sign Up"
- Use Google, GitHub, or email
- Free account created instantly

### Step 3: Get Your API Key
1. Go to https://console.groq.com/keys
2. Click "Create API Key"
3. Copy the key (it starts with `gsk_`)
4. Keep it safe!

### Step 4: Add to .env
Open `backend/.env` and update:
```env
GROQ_API_KEY=gsk_your_api_key_here
LLM_PROVIDER=groq
```

## Available Groq Models
- **mixtral-8x7b-32768** ⭐ (Free) - Recommended for CRAG
- **llama2-70b-4096** - Also free
- **gemma-7b-it** - Lightweight option

## Testing
Once you add your Groq key, restart the server:

```bash
# Kill old server (Ctrl+C)
# Then restart:
export PYTHONPATH=/media/syed-sarim-ahsan/Storage1/Meezan-GPT-CRAG/backend:$PYTHONPATH && \
cd /media/syed-sarim-ahsan/Storage1/Meezan-GPT-CRAG/backend && \
./venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Test the API:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Meezan Bank?","use_correction":false,"top_k":3}'
```

## Rate Limits
- Groq Free: ~30 requests/minute
- Perfect for development & testing
- Upgrade to higher limits if needed

## Switching Back to OpenAI
If you want to use OpenAI again:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk_xxx...
```

---

**Get your Groq key now**: https://console.groq.com/keys
