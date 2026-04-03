# CRAG System Evaluation Guide

## Overview

The CRAG (Corrective RAG) system evaluation suite provides comprehensive metrics and analysis for your chatbot's performance. It includes:

1. **evaluate_crag.py** - Main evaluation script that tests the system
2. **analyze_metrics.py** - Advanced visualization and analysis tool

---

## Quick Start

### 1. Run Evaluation

```bash
cd backend
source venv/bin/activate
python evaluate_crag.py
```

**Output:**
```
======================================================================
MEEZAN BANK CRAG SYSTEM EVALUATION
======================================================================

[Query 1/5] What savings accounts does Meezan Bank offer?...
  🔍 Evaluating retrieval... ✓ (245.3ms)
  🤖 Evaluating generation... ✓ (1523.2ms)
  🔄 Evaluating full pipeline... ✓ (1768.5ms)

[Query 2/5] What is car financing in Islamic banking?...
  ...

======================================================================
📊 CRAG SYSTEM EVALUATION REPORT
======================================================================

📈 OVERALL PERFORMANCE
  Success Rate:          100.0%
  Failed Queries:        0

🔍 RETRIEVAL METRICS
  Avg Documents Retrieved: 3.0
  Avg Top Score:           0.856

🤖 GENERATION METRICS
  Avg Answer Relevance:    0.742
  Avg Context Relevance:   0.698

⚡ PERFORMANCE METRICS
  Avg Latency:             1654.2ms
  Min Latency:             1234.5ms
  Max Latency:             2105.3ms
```

### 2. Analyze Results

```bash
python analyze_metrics.py
```

**Output:**
```
✅ Latency chart saved: latency_analysis.png
✅ Relevance chart saved: relevance_analysis.png
✅ Retrieval scores chart saved: retrieval_scores.png
✅ Dashboard saved: crag_dashboard.png
✅ Detailed report saved: crag_detailed_analysis.txt
```

---

## Metrics Explained

### 📊 Overall Performance

**Success Rate** (%)
- Percentage of queries that completed successfully
- Target: 100%
- What it means: Reliability of the CRAG system

**Failed Queries**
- Number of queries that errored out
- Target: 0
- What it means: System stability

### 🔍 Retrieval Metrics

**Avg Documents Retrieved**
- Average number of documents returned per query
- Default: 3 (top-k=3)
- What it means: Coverage of knowledge base

**Avg Top Score** (0-1)
- Average cosine similarity of the best match
- Target: > 0.7
- Scores:
  - 0.9+: Excellent match
  - 0.7-0.9: Good match
  - 0.5-0.7: Acceptable match
  - <0.5: Poor match
- What it means: Quality of document retrieval

### 🤖 Generation Metrics

**Answer Relevance** (0-1)
- Semantic similarity between query and answer
- Calculated using embedding models
- Target: > 0.6
- Scores:
  - 0.8+: Highly relevant answer
  - 0.6-0.8: Relevant answer
  - 0.4-0.6: Somewhat relevant
  - <0.4: Irrelevant answer
- What it means: How well the LLM answered the question

**Context Relevance** (0-1)
- Semantic similarity between query and retrieved documents
- Target: > 0.6
- What it means: Quality of context provided to the LLM

### ⚡ Performance Metrics

**Latency (ms)** - Total response time
- Mean: Average latency across all queries
  - <1000ms: Excellent (0-1 second)
  - 1000-2000ms: Good (1-2 seconds)
  - 2000-5000ms: Acceptable (2-5 seconds)
  - >5000ms: Slow (needs optimization)
- Min: Fastest response
- Max: Slowest response
- What it means: User experience - how fast responses arrive

**Latency Breakdown:**
1. **Retrieval**: Document search (typically 200-500ms)
2. **Generation**: LLM response (typically 1000-3000ms)
3. **Correction**: Validation (typically 100-300ms)

### 📋 Document Scores

**Retrieval Score Distribution**
- Shows range of document match scores
- Helps understand coverage:
  - High concentration (>0.8): Good matches available
  - Wide distribution: Diverse results
  - Low concentration (<0.5): Poor matches

---

## Reading the Charts

### 1. Latency Analysis
**What it shows:**
- Distribution of response times
- Identifies slow queries
- Helps identify bottlenecks

**How to interpret:**
- Bimodal (two peaks): Some queries faster than others
- Single peak: Consistent performance
- Long tail: Some very slow queries exist

### 2. Relevance Analysis
**What it shows:**
- Answer quality vs query number
- Trend in performance across queries
- High vs low confidence answers

**How to interpret:**
- High values (>0.7): Good answers to queries
- Low values (<0.5): Poor answers or hard queries
- Correlation: Should match high retrieval scores

### 3. Retrieval Scores Distribution
**What it shows:**
- Range of document match scores
- Coverage of knowledge base

**How to interpret:**
- Right-skewed (high scores): Good documents available
- Left-skewed (low scores): Limited relevant documents
- Wide range (0.2-0.9): Diverse knowledge base

### 4. Dashboard Summary
**What it shows:**
- Success rate (pie chart)
- Latency distribution
- Per-query relevance
- Key metrics summary

**How to interpret:**
- Success rate >95%: System is reliable
- Latency <2000ms: Good user experience
- Relevance >0.6: Quality answers

---

## Optimization Guide

### If Latency is High (>3000ms)

**Possible causes:**
1. LLM API latency (Groq/OpenAI slow)
2. Network latency
3. Too many documents (high top-k)
4. First query (model loading)

**Solutions:**
```python
# Reduce top-k
{"query": "...", "top_k": 2}  # Instead of 3-5

# Use faster LLM
# .env: LLM_PROVIDER=groq_fast

# Check API status
# https://console.groq.com/status
```

### If Relevance is Low (<0.5)

**Possible causes:**
1. Query outside knowledge base
2. Embeddings not aligned with documents
3. LLM generating off-topic answers
4. Poor document matches

**Solutions:**
```python
# Increase top-k to get more context
{"query": "...", "top_k": 5}

# Enable correction
{"query": "...", "use_correction": true}

# Check metadata quality
python rebuild_metadata.py

# Verify embeddings match
python validate_embeddings_consistency.py
```

### If Success Rate <95%

**Possible causes:**
1. FAISS index corruption
2. Missing API keys
3. Network issues
4. Malformed queries

**Solutions:**
```bash
# Rebuild FAISS index
python setup_faiss.py

# Check environment variables
cat .env

# Verify API connectivity
python -c "from groq import Groq; print('OK')"

# Test with curl
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

---

## Detailed Report Format

The `crag_evaluation_report.json` contains:

```json
{
  "metadata": {
    "timestamp": "2026-04-03T14:35:22.123456",
    "total_queries": 5,
    "backend_path": "/path/to/backend"
  },
  "aggregate_metrics": {
    "success_rate": 100.0,
    "failure_count": 0,
    "retrieval": {...},
    "generation": {...},
    "performance": {...}
  },
  "individual_results": [
    {
      "query_idx": 1,
      "query": "What savings accounts does Meezan Bank offer?",
      "category": "savings_accounts",
      "retrieval": {
        "success": true,
        "num_docs_retrieved": 3,
        "top_score": 0.856,
        "avg_score": 0.742,
        "documents": [...]
      },
      "generation": {
        "success": true,
        "answer": "Meezan Bank offers...",
        "answer_length_words": 145,
        "relevance_score": 0.782,
        "latency_ms": 1523.4
      },
      "pipeline": {
        "success": true,
        "total_latency_ms": 1768.5,
        "answer_relevance": 0.782,
        "avg_context_relevance": 0.698
      }
    }
  ]
}
```

---

## Test Queries

The evaluation uses 5 default test queries covering different categories:

1. **Savings Accounts**
   - Query: "What savings accounts does Meezan Bank offer?"
   - Tests: General product knowledge

2. **Auto Financing**
   - Query: "What is car financing in Islamic banking?"
   - Tests: Specialized knowledge

3. **Business Banking**
   - Query: "How to apply for business account at Meezan Bank?"
   - Tests: Process-oriented queries

4. **Branch Locator**
   - Query: "What are the ATM locations of Meezan Bank?"
   - Tests: Location data retrieval

5. **Awards & Recognition**
   - Query: "Tell me about Meezan Bank awards and certifications"
   - Tests: Historical/factual information

### Adding Custom Test Queries

Edit `evaluate_crag.py` and modify the `test_queries` list:

```python
self.test_queries = [
    {
        "query": "Your custom question?",
        "keywords": ["keyword1", "keyword2"],
        "category": "custom_category"
    },
    # ... more queries
]
```

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Good | Acceptable |
|--------|--------|------|-----------|
| Success Rate | 100% | 95%+ | 80%+ |
| Latency (ms) | <2000 | <3000 | <5000 |
| Answer Relevance | >0.7 | >0.6 | >0.5 |
| Top Doc Score | >0.8 | >0.7 | >0.6 |

### Baseline Performance (your system)

Update this after running evaluation:

```
Success Rate:        ____%
Avg Latency:        ____ms
Answer Relevance:    ____
Top Doc Score:       ____
```

---

## Troubleshooting Evaluation

### Error: "FAISS index not found"
```bash
cd backend
python setup_faiss.py
```

### Error: "Groq API error"
```bash
# Check API key
echo $GROQ_API_KEY

# Check connectivity
curl https://api.groq.com
```

### Error: "Module not found"
```bash
pip install -r requirements.txt
pip install matplotlib numpy
```

### Evaluation runs but shows all 0 scores
```bash
# Rebuild metadata with text content
python rebuild_metadata.py

# Verify embeddings exist
ls -lh Embeddings_data/bge_base_en_v1_5_embeddings.npy
```

---

## Next Steps

1. ✅ Run `evaluate_crag.py` to get baseline metrics
2. ✅ Run `analyze_metrics.py` to generate charts
3. ✅ Review `crag_evaluation_report.json` for detailed results
4. ✅ Compare metrics against targets
5. ✅ Optimize based on weak areas
6. ✅ Re-run evaluation after optimizations
7. ✅ Track improvements over time

---

## Continuous Monitoring

To track performance over time:

```bash
# Create timestamped reports
python evaluate_crag.py
mv crag_evaluation_report.json "reports/report_$(date +%Y%m%d_%H%M%S).json"

# Compare reports
diff report1.json report2.json
```

---

## Support

For issues or questions about evaluation:

1. Check `crag_detailed_analysis.txt` for detailed breakdown
2. Review charts to visualize issues
3. Test individual components with curl
4. Check backend logs: `tail -f /var/log/crag.log`

Happy evaluating! 🚀
