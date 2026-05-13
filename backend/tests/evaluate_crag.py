#!/usr/bin/env python3
"""
CRAG System Evaluation Script

Evaluates the Corrective RAG system performance across:
- Retrieval quality (relevant documents retrieved)
- Generation quality (answer coherence and relevance)
- System performance (latency, throughput)
- Overall accuracy and effectiveness
"""

import json
import time
import statistics
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from sentence_transformers import util
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from crag_system import CRAGSystem
from faiss_retriever import FAISSRetriever
from sentence_transformers import SentenceTransformer


class CRAGEvaluator:
    """Comprehensive CRAG system evaluator"""
    
    def __init__(self, backend_path=None):
        """Initialize evaluator with CRAG system"""
        if backend_path is None:
            backend_path = Path(__file__).parent
        
        self.backend_path = Path(backend_path)
        self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        self.crag_system = CRAGSystem()
        
        # Test queries with ground truth relevance
        self.test_queries = [
            {
                "query": "What savings accounts does Meezan Bank offer?",
                "keywords": ["savings", "account", "bachat", "asaan"],
                "category": "savings_accounts"
            },
            {
                "query": "What is car financing in Islamic banking?",
                "keywords": ["car", "ijarah", "apni", "financing"],
                "category": "auto_financing"
            },
            {
                "query": "How to apply for business account at Meezan Bank?",
                "keywords": ["business", "account", "application", "corporate"],
                "category": "business_banking"
            },
            {
                "query": "What are the ATM locations of Meezan Bank?",
                "keywords": ["atm", "branch", "locator", "location"],
                "category": "branches"
            },
            {
                "query": "Tell me about Meezan Bank awards and certifications",
                "keywords": ["award", "recognition", "certification", "best"],
                "category": "awards"
            },
        ]
        
        self.results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_queries": len(self.test_queries),
                "backend_path": str(self.backend_path)
            },
            "retrieval_metrics": {},
            "generation_metrics": {},
            "system_metrics": {},
            "individual_results": []
        }
    
    def evaluate_retrieval(self, query: str, top_k: int = 3) -> Dict:
        """Evaluate retrieval performance"""
        start = time.time()
        
        try:
            results = self.crag_system.retriever.retrieve(query, top_k=top_k)
            latency = time.time() - start
            
            retrieved_docs = results if isinstance(results, list) else []
            
            return {
                "success": True,
                "num_docs_retrieved": len(retrieved_docs),
                "top_score": retrieved_docs[0][1] if retrieved_docs else 0,
                "avg_score": np.mean([doc[1] for doc in retrieved_docs]) if retrieved_docs else 0,
                "min_score": retrieved_docs[-1][1] if retrieved_docs else 0,
                "latency_ms": latency * 1000,
                "documents": [
                    {
                        "title": doc[0].get("metadata", {}).get("source_title", "Unknown"),
                        "score": float(doc[1]),
                        "chars": doc[0].get("chars", 0)
                    }
                    for doc in retrieved_docs
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency_ms": (time.time() - start) * 1000
            }
    
    def evaluate_generation(self, query: str, context: List, use_correction: bool = False) -> Dict:
        """Evaluate generation performance"""
        start = time.time()
        
        try:
            answer = self.crag_system.generator.generate(query, context)
            latency = time.time() - start
            
            # Calculate answer metrics
            answer_length = len(answer.split())
            answer_embedding = self.embedding_model.encode(answer)
            query_embedding = self.embedding_model.encode(query)
            relevance_score = float(util.pytorch_cos_sim(query_embedding, answer_embedding)[0][0])
            
            return {
                "success": True,
                "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                "answer_length_words": answer_length,
                "relevance_score": relevance_score,
                "latency_ms": latency * 1000,
                "has_numbers": any(char.isdigit() for char in answer),
                "has_action_words": any(word in answer.lower() for word in 
                                       ["can", "offer", "provide", "include", "available"])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency_ms": (time.time() - start) * 1000
            }
    
    def evaluate_full_pipeline(self, query: str, top_k: int = 3, use_correction: bool = False) -> Dict:
        """Evaluate full CRAG pipeline"""
        start = time.time()
        
        try:
            # Call CRAG system
            result = self.crag_system.query(query, top_k=top_k, use_correction=use_correction)
            total_latency = time.time() - start
            
            # Extract metrics
            answer_embedding = self.embedding_model.encode(result["answer"])
            query_embedding = self.embedding_model.encode(query)
            answer_relevance = float(util.pytorch_cos_sim(query_embedding, answer_embedding)[0][0])
            
            # Calculate context relevance
            context_relevance_scores = []
            if result.get("context"):
                for ctx in result["context"]:
                    ctx_embedding = self.embedding_model.encode(ctx.get("content", "")[:500])
                    relevance = float(util.pytorch_cos_sim(query_embedding, ctx_embedding)[0][0])
                    context_relevance_scores.append(relevance)
            
            return {
                "success": True,
                "query": query,
                "answer": result["answer"][:150] + "..." if len(result["answer"]) > 150 else result["answer"],
                "answer_length_words": len(result["answer"].split()),
                "num_sources": len(result.get("context", [])),
                "total_latency_ms": total_latency * 1000,
                "answer_relevance": answer_relevance,
                "avg_context_relevance": np.mean(context_relevance_scores) if context_relevance_scores else 0,
                "retrieval_scores": [ctx.get("score", 0) for ctx in result.get("context", [])],
                "answer_quality_indicators": {
                    "has_context": answer_relevance > 0.5,
                    "has_specific_info": len(result["answer"]) > 100,
                    "is_coherent": answer_relevance > 0.4
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_latency_ms": (time.time() - start) * 1000
            }
    
    def calculate_aggregate_metrics(self) -> Dict:
        """Calculate aggregate performance metrics"""
        individual = self.results["individual_results"]
        
        # Filter successful queries
        successful = [r for r in individual if r.get("pipeline", {}).get("success")]
        failed = len(individual) - len(successful)
        
        if not successful:
            return {}
        
        # Retrieval metrics
        all_retrieval_scores = []
        all_latencies = []
        all_num_docs = []
        all_answer_relevance = []
        all_context_relevance = []
        
        for result in successful:
            retr = result.get("retrieval", {})
            pipe = result.get("pipeline", {})
            
            if retr.get("success"):
                all_retrieval_scores.extend(retr.get("documents", []))
                all_latencies.append(retr.get("latency_ms", 0))
                all_num_docs.append(retr.get("num_docs_retrieved", 0))
            
            if pipe.get("success"):
                all_answer_relevance.append(pipe.get("answer_relevance", 0))
                all_context_relevance.append(pipe.get("avg_context_relevance", 0))
                all_latencies.append(pipe.get("total_latency_ms", 0))
        
        metrics = {
            "success_rate": (len(successful) / len(individual)) * 100,
            "failure_count": failed,
            "retrieval": {
                "avg_documents_retrieved": statistics.mean(all_num_docs) if all_num_docs else 0,
                "avg_top_score": statistics.mean([d["score"] for d in all_retrieval_scores if isinstance(d, dict)]) 
                                 if all_retrieval_scores else 0,
            },
            "generation": {
                "avg_answer_relevance": statistics.mean(all_answer_relevance) if all_answer_relevance else 0,
                "avg_context_relevance": statistics.mean(all_context_relevance) if all_context_relevance else 0,
            },
            "performance": {
                "avg_latency_ms": statistics.mean(all_latencies) if all_latencies else 0,
                "min_latency_ms": min(all_latencies) if all_latencies else 0,
                "max_latency_ms": max(all_latencies) if all_latencies else 0,
            }
        }
        
        return metrics
    
    def run_evaluation(self, top_k: int = 3, use_correction: bool = False):
        """Run complete evaluation"""
        print("\n" + "="*70)
        print("MEEZAN BANK CRAG SYSTEM EVALUATION")
        print("="*70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Backend Path: {self.backend_path}")
        print(f"Test Queries: {len(self.test_queries)}")
        print(f"Top-K: {top_k}")
        print(f"Use Correction: {use_correction}")
        print("="*70 + "\n")
        
        for idx, test_case in enumerate(self.test_queries, 1):
            query = test_case["query"]
            print(f"\n[Query {idx}/{len(self.test_queries)}] {query[:60]}...")
            
            # Retrieval evaluation
            print("  🔍 Evaluating retrieval...", end=" ", flush=True)
            retrieval_result = self.evaluate_retrieval(query, top_k)
            print(f"✓ ({retrieval_result.get('latency_ms', 0):.1f}ms)")
            
            # Generation evaluation
            if retrieval_result.get("success"):
                context = retrieval_result.get("documents", [])
                print("  🤖 Evaluating generation...", end=" ", flush=True)
                generation_result = self.evaluate_generation(query, context, use_correction)
                print(f"✓ ({generation_result.get('latency_ms', 0):.1f}ms)")
            else:
                generation_result = {"success": False, "error": "Retrieval failed"}
            
            # Full pipeline evaluation
            print("  🔄 Evaluating full pipeline...", end=" ", flush=True)
            pipeline_result = self.evaluate_full_pipeline(query, top_k, use_correction)
            print(f"✓ ({pipeline_result.get('total_latency_ms', 0):.1f}ms)")
            
            # Store results
            self.results["individual_results"].append({
                "query_idx": idx,
                "query": query,
                "category": test_case["category"],
                "retrieval": retrieval_result,
                "generation": generation_result,
                "pipeline": pipeline_result
            })
        
        # Calculate aggregate metrics
        print("\n" + "="*70)
        print("CALCULATING AGGREGATE METRICS...")
        print("="*70 + "\n")
        
        aggregate = self.calculate_aggregate_metrics()
        self.results["aggregate_metrics"] = aggregate
        
        return self.results
    
    def print_report(self):
        """Print evaluation report"""
        agg = self.results.get("aggregate_metrics", {})
        ind = self.results.get("individual_results", [])
        
        print("\n" + "="*70)
        print("📊 CRAG SYSTEM EVALUATION REPORT")
        print("="*70)
        
        # Overall metrics
        print("\n📈 OVERALL PERFORMANCE")
        print("-" * 70)
        print(f"  Success Rate:          {agg.get('success_rate', 0):.1f}%")
        print(f"  Failed Queries:        {agg.get('failure_count', 0)}")
        
        # Retrieval metrics
        retr = agg.get("retrieval", {})
        print("\n🔍 RETRIEVAL METRICS")
        print("-" * 70)
        print(f"  Avg Documents Retrieved: {retr.get('avg_documents_retrieved', 0):.1f}")
        print(f"  Avg Top Score:           {retr.get('avg_top_score', 0):.3f}")
        
        # Generation metrics
        gen = agg.get("generation", {})
        print("\n🤖 GENERATION METRICS")
        print("-" * 70)
        print(f"  Avg Answer Relevance:    {gen.get('avg_answer_relevance', 0):.3f}")
        print(f"  Avg Context Relevance:   {gen.get('avg_context_relevance', 0):.3f}")
        
        # Performance metrics
        perf = agg.get("performance", {})
        print("\n⚡ PERFORMANCE METRICS")
        print("-" * 70)
        print(f"  Avg Latency:             {perf.get('avg_latency_ms', 0):.1f}ms")
        print(f"  Min Latency:             {perf.get('min_latency_ms', 0):.1f}ms")
        print(f"  Max Latency:             {perf.get('max_latency_ms', 0):.1f}ms")
        
        # Individual results
        print("\n📋 INDIVIDUAL QUERY RESULTS")
        print("-" * 70)
        for result in ind:
            status = "✓" if result.get("pipeline", {}).get("success") else "✗"
            query = result.get("query", "")[:50]
            relevance = result.get("pipeline", {}).get("answer_relevance", 0)
            latency = result.get("pipeline", {}).get("total_latency_ms", 0)
            
            print(f"  {status} [{result.get('category')}] {query}")
            print(f"     Relevance: {relevance:.3f} | Latency: {latency:.1f}ms")
        
        print("\n" + "="*70)
    
    def save_report(self, filename: str = "crag_evaluation_report.json"):
        """Save detailed report to JSON"""
        output_path = self.backend_path / filename
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Report saved to: {output_path}")
        return output_path


def main():
    """Run evaluation"""
    evaluator = CRAGEvaluator()
    
    print("\n🚀 Starting CRAG System Evaluation...")
    print("This will test retrieval, generation, and overall performance.\n")
    
    # Run evaluation
    try:
        evaluator.run_evaluation(top_k=3, use_correction=False)
        evaluator.print_report()
        evaluator.save_report()
        
        print("\n✅ Evaluation completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
