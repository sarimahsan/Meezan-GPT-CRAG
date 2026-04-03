# CRAG System Evaluation Tools

Complete toolkit for evaluating and monitoring your CRAG (Corrective RAG) chatbot performance.

## 📦 What's Included

| Script | Purpose | Output |
|--------|---------|--------|
| `evaluate_crag.py` | Run comprehensive system evaluation | `crag_evaluation_report.json` |
| `analyze_metrics.py` | Generate visualizations & charts | PNG charts + text report |
| `monitor_health.py` | Real-time system health monitoring | Console output + JSON |
| `EVALUATION_GUIDE.md` | Complete guide to metrics & optimization | Documentation |

---

## 🚀 Quick Start (2 minutes)

### 1. Make scripts executable
```bash
cd backend
chmod +x evaluate_crag.py analyze_metrics.py monitor_health.py
```

### 2. Run evaluation
```bash
python evaluate_crag.py
```

### 3. Generate visualizations
```bash
python analyze_metrics.py
```

### 4. View results
- Charts: `latency_analysis.png`, `relevance_analysis.png`, `crag_dashboard.png`
- Report: `crag_detailed_analysis.txt`
- JSON: `crag_evaluation_report.json`

---

## 📚 Tools Overview

### 1. evaluate_crag.py

**Purpose:** Comprehensive system evaluation

**What it does:**
- Tests 5 pre-defined queries across different categories
- Measures retrieval quality (document relevance)
- Measures generation quality (answer relevance)
- Measures system performance (latency)
- Evaluates full CRAG pipeline end-to-end

**Runtime:** ~15-30 seconds (5 queries)

**Usage:**
```bash
python evaluate_crag.py
```

**Output:**
```
[Query 1/5] What savings accounts does Meezan Bank offer?...
  🔍 Evaluating retrieval... ✓ (245.3ms)
  🤖 Evaluating generation... ✓ (1523.2ms)
  🔄 Evaluating full pipeline... ✓ (1768.5ms)

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
```

**Key Metrics:**
- ✅ Success Rate (~95-100%)
- ✅ Top Document Score (~0.7-0.9)
- ✅ Answer Relevance (~0.6-0.8)
- ✅ Total Latency (~1500-3000ms)

---

### 2. analyze_metrics.py

**Purpose:** Advanced visualization and analysis

**What it does:**
- Reads the JSON report from `evaluate_crag.py`
- Generates 5 visualization charts
- Creates detailed text analysis report
- Produces comprehensive dashboard

**Runtime:** ~5 seconds

**Usage:**
```bash
python analyze_metrics.py
```

**Generates:**

1. **latency_analysis.png**
   - Histogram of response times
   - Box plot showing distribution
   - Statistics: mean, median, min, max

2. **relevance_analysis.png**
   - Answer relevance per query
   - Context relevance per query
   - Side-by-side comparison

3. **retrieval_scores.png**
   - Distribution of document match scores
   - Shows coverage of knowledge base
   - Statistics overlay

4. **crag_dashboard.png**
   - Success rate pie chart
   - Latency histogram
   - Per-query relevance bars
   - Key metrics summary

5. **crag_detailed_analysis.txt**
   - Detailed statistics for all metrics
   - Per-query breakdown
   - Performance analysis

**Sample Output:**
```
✅ Latency chart saved: latency_analysis.png
✅ Relevance chart saved: relevance_analysis.png
✅ Retrieval scores chart saved: retrieval_scores.png
✅ Dashboard saved: crag_dashboard.png
✅ Detailed report saved: crag_detailed_analysis.txt
```

---

### 3. monitor_health.py

**Purpose:** Real-time system health monitoring

**What it does:**
- Continuously tests the CRAG system
- Tracks latency and success rate
- Detects anomalies and alerts
- Maintains rolling statistics

**Modes:**

**Quick Check (1 minute)**
```bash
python monitor_health.py --quick
```
- Tests for 60 seconds
- 5-second intervals
- Good for quick diagnostics

**Continuous Monitoring**
```bash
python monitor_health.py --continuous
```
- Runs indefinitely
- 60-second intervals
- Press Ctrl+C to stop

**Single Check**
```bash
python monitor_health.py
```
- One test and report
- Saves to `health_report.json`

**Sample Output:**
```
🏥 CRAG SYSTEM HEALTH CHECK
======================================================================
Time: 2026-04-03 14:35:22
----------------------------------------------------------------------
API Status:          ✅ Online
Total Requests:      10
Successful:          10
Failed:              0
Success Rate:        100.0%
Avg Latency:         1,623.4ms
Min Latency:         1,234.5ms
Max Latency:         2,105.3ms
----------------------------------------------------------------------
⚠️  ALERTS:
  ✅ No issues detected
======================================================================
```

**Alert Conditions:**
- ❌ API not responding → Check if backend is running
- ⚠️ Success rate <95% → Check logs for errors
- 🐢 High latency (>3000ms) → Check Groq API or reduce top-k
- 🔴 Multiple errors → Check network and dependencies

---

## 📊 Understanding the Metrics

### Success Rate
```
100% = All queries completed successfully
95%+ = Excellent (target)
80%+ = Acceptable
<80% = Needs investigation
```

### Latency Breakdown
```
Total = Retrieval + Generation + Correction
  ├─ Retrieval: 200-500ms (FAISS search)
  ├─ Generation: 1000-3000ms (Groq LLM)
  └─ Correction: 100-300ms (validation)
= Total: 1500-3800ms typical
```

### Relevance Scores
```
Answer Relevance: How well the answer matches the query
  - >0.7 = Excellent answer
  - 0.6-0.7 = Good answer
  - 0.5-0.6 = Acceptable answer
  - <0.5 = Poor answer

Context Relevance: How well documents match the query
  - >0.7 = Excellent context
  - 0.6-0.7 = Good context
  - 0.5-0.6 = Acceptable context
  - <0.5 = Poor context
```

### Document Scores
```
Top Score: Cosine similarity of best match
  - >0.9 = Perfect match
  - 0.7-0.9 = Strong match
  - 0.5-0.7 = Moderate match
  - <0.5 = Weak match
```

---

## 🔄 Typical Workflow

### Day 1: Baseline Evaluation
```bash
# Establish baseline performance
python evaluate_crag.py
python analyze_metrics.py

# Review charts and report
# Note target metrics for comparison
```

### Day 2-7: Optimization
Based on evaluation results:
- Increase top-k if relevance is low
- Reduce top-k if latency is high
- Fix metadata if scores are 0
- Check API keys if errors occur

### Day 7+: Monitor Performance
```bash
# Quick health check periodically
python monitor_health.py --quick

# Full evaluation weekly
python evaluate_crag.py
python analyze_metrics.py
```

---

## 🧪 Test Queries Included

The `evaluate_crag.py` script tests 5 categories:

1. **Savings Accounts** (Product Knowledge)
   - "What savings accounts does Meezan Bank offer?"

2. **Auto Financing** (Specialized Knowledge)
   - "What is car financing in Islamic banking?"

3. **Business Banking** (Process Knowledge)
   - "How to apply for business account at Meezan Bank?"

4. **Branch Locator** (Location Data)
   - "What are the ATM locations of Meezan Bank?"

5. **Awards & Recognition** (Factual Knowledge)
   - "Tell me about Meezan Bank awards and certifications"

**Adding Your Own Tests:**

Edit `evaluate_crag.py` and add to `test_queries`:
```python
self.test_queries = [
    # ... existing queries ...
    {
        "query": "Your custom question?",
        "keywords": ["keyword1", "keyword2"],
        "category": "your_category"
    }
]
```

---

## 📈 Performance Targets

### Recommended Metrics

| Metric | Excellent | Good | Acceptable |
|--------|-----------|------|-----------|
| Success Rate | 100% | 95%+ | 80%+ |
| Answer Relevance | >0.75 | >0.65 | >0.50 |
| Avg Top Score | >0.85 | >0.75 | >0.65 |
| Latency | <1500ms | <2500ms | <5000ms |

### Your Current Baseline
(Fill after first evaluation)
```
Success Rate:     ____%
Answer Relevance: _____
Avg Top Score:    _____
Latency:          ____ms
Date:             _____
```

---

## 🛠️ Optimization Quick Guide

### Slow Responses? (Latency >3000ms)
```bash
# Reduce number of documents to process
# In evaluate_crag.py or API calls:
{"query": "...", "top_k": 2}  # Instead of 3-5

# Check API status
curl https://api.groq.com/status

# Monitor network
ping api.groq.com
```

### Poor Answers? (Relevance <0.5)
```bash
# Increase context size
{"query": "...", "top_k": 5}

# Enable correction
{"query": "...", "use_correction": true}

# Verify metadata
python rebuild_metadata.py

# Check embeddings
python Embeddings/validate_embeddings_consistency.py
```

### Frequent Errors? (Success <90%)
```bash
# Check API connectivity
python monitor_health.py --quick

# Verify Groq API key
echo $GROQ_API_KEY

# Rebuild FAISS index
python Embeddings/setup_faiss.py

# Check logs
python | tail -20
```

---

## 📁 Output Files

After running the tools, you'll have:

```
backend/
├── crag_evaluation_report.json     # Complete metrics (JSON)
├── latency_analysis.png             # Latency chart
├── relevance_analysis.png           # Relevance chart  
├── retrieval_scores.png             # Score distribution
├── crag_dashboard.png               # Summary dashboard
├── crag_detailed_analysis.txt       # Text report
├── health_report.json               # Latest health check
└── EVALUATION_GUIDE.md              # This guide
```

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'sentence_transformers'"
```bash
pip install sentence-transformers
pip install matplotlib numpy
```

### Issue: "FAISS index not found"
```bash
cd Embeddings
python setup_faiss.py
```

### Issue: "GROQ_API_KEY not found"
```bash
# Create .env file
echo "GROQ_API_KEY=your_key_here" > .env
echo "LLM_PROVIDER=groq" >> .env
```

### Issue: "All scores are 0"
```bash
# Rebuild metadata with text content
python rebuild_metadata.py

# Verify metadata
head -5 Embeddings_data/metadata.json
```

---

## 💡 Tips for Best Results

1. **Run evaluation multiple times** to get average metrics (not single run)
2. **Test during off-peak hours** for consistent results
3. **Keep Groq API key fresh** (regenerate monthly for security)
4. **Monitor trends** (latency increasing = API degrading)
5. **Document baseline** before making changes
6. **Compare before/after** for optimization impact
7. **Alert on regressions** (set up notifications)

---

## 📊 Exporting Results

### Share Metrics
```bash
# Copy all reports
cp *.png *.json *.txt ~/shared/reports/

# Or specific format
cp crag_evaluation_report.json ~/shared/metrics.json
cp crag_dashboard.png ~/shared/dashboard.png
```

### Track Over Time
```bash
# Create versioned reports
mkdir -p reports
cp crag_evaluation_report.json "reports/$(date +%Y%m%d_%H%M%S).json"

# Compare versions
diff reports/20260403_140000.json reports/20260403_150000.json
```

---

## 🎯 Next Steps

1. ✅ Run `evaluate_crag.py` once for baseline
2. ✅ Run `analyze_metrics.py` to generate charts
3. ✅ Review `crag_dashboard.png` for overview
4. ✅ Read `crag_detailed_analysis.txt` for details
5. ✅ Set up `monitor_health.py` for continuous monitoring
6. ✅ Schedule weekly evaluations
7. ✅ Track improvements over time

---

## 📞 Support

For issues:
1. Check `EVALUATION_GUIDE.md` for detailed explanations
2. Run `monitor_health.py` to diagnose system state
3. Review chart files for visual insights
4. Check `crag_detailed_analysis.txt` for breakdown

Happy evaluating! 🚀
