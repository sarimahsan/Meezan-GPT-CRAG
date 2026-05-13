#!/usr/bin/env python3
"""
Advanced CRAG Metrics Analysis and Visualization

Provides detailed analysis and visualization of CRAG system performance.
Creates charts for latency distribution, relevance scores, success rates, etc.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from datetime import datetime
import statistics
import numpy as np


class CRAGMetricsAnalyzer:
    """Analyze and visualize CRAG evaluation metrics"""
    
    def __init__(self, report_path: str = "crag_evaluation_report.json"):
        """Load evaluation report"""
        self.report_path = Path(report_path)
        
        if not self.report_path.exists():
            raise FileNotFoundError(f"Report not found at {self.report_path}")
        
        with open(self.report_path, 'r') as f:
            self.report = json.load(f)
        
        self.individual_results = self.report.get("individual_results", [])
        self.aggregate = self.report.get("aggregate_metrics", {})
    
    def extract_metrics(self) -> dict:
        """Extract all metrics from report"""
        metrics = {
            "queries": [],
            "latencies": [],
            "answer_relevance": [],
            "context_relevance": [],
            "retrieval_scores": [],
            "status": []
        }
        
        for result in self.individual_results:
            pipeline = result.get("pipeline", {})
            if pipeline.get("success"):
                metrics["queries"].append(result.get("query", ""))
                metrics["latencies"].append(pipeline.get("total_latency_ms", 0))
                metrics["answer_relevance"].append(pipeline.get("answer_relevance", 0))
                metrics["context_relevance"].append(pipeline.get("avg_context_relevance", 0))
                metrics["retrieval_scores"].extend(pipeline.get("retrieval_scores", []))
                metrics["status"].append("Success")
            else:
                metrics["status"].append("Failed")
        
        return metrics
    
    def generate_latency_chart(self, output_file: str = "latency_analysis.png"):
        """Generate latency distribution chart"""
        metrics = self.extract_metrics()
        latencies = metrics["latencies"]
        
        if not latencies:
            print("⚠️  No latency data to plot")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram
        ax1.hist(latencies, bins=10, color='#667eea', alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Latency (ms)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax1.set_title('Latency Distribution', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add statistics to histogram
        stats_text = (
            f"Mean: {statistics.mean(latencies):.1f}ms\n"
            f"Median: {statistics.median(latencies):.1f}ms\n"
            f"Min: {min(latencies):.1f}ms\n"
            f"Max: {max(latencies):.1f}ms"
        )
        ax1.text(0.98, 0.97, stats_text, transform=ax1.transAxes,
                fontsize=10, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Box plot
        ax2.boxplot(latencies, vert=True)
        ax2.set_ylabel('Latency (ms)', fontsize=11, fontweight='bold')
        ax2.set_title('Latency Box Plot', fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Latency chart saved: {output_file}")
        plt.close()
    
    def generate_relevance_chart(self, output_file: str = "relevance_analysis.png"):
        """Generate relevance scores chart"""
        metrics = self.extract_metrics()
        answer_rel = metrics["answer_relevance"]
        context_rel = metrics["context_relevance"]
        
        if not answer_rel:
            print("⚠️  No relevance data to plot")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(answer_rel))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, answer_rel, width, label='Answer Relevance', color='#667eea')
        bars2 = ax.bar(x + width/2, context_rel, width, label='Context Relevance', color='#764ba2')
        
        ax.set_xlabel('Query Index', fontsize=11, fontweight='bold')
        ax.set_ylabel('Relevance Score (0-1)', fontsize=11, fontweight='bold')
        ax.set_title('Relevance Scores Across Queries', fontsize=13, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f"Q{i+1}" for i in range(len(answer_rel))])
        ax.legend(fontsize=10)
        ax.set_ylim([0, 1.1])
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Relevance chart saved: {output_file}")
        plt.close()
    
    def generate_retrieval_scores_chart(self, output_file: str = "retrieval_scores.png"):
        """Generate retrieval scores distribution"""
        metrics = self.extract_metrics()
        scores = metrics["retrieval_scores"]
        
        if not scores:
            print("⚠️  No retrieval scores to plot")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.hist(scores, bins=20, color='#667eea', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Document Match Score (0-1)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax.set_title('Retrieved Document Score Distribution', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add statistics
        stats_text = (
            f"Mean: {np.mean(scores):.3f}\n"
            f"Median: {np.median(scores):.3f}\n"
            f"Std Dev: {np.std(scores):.3f}\n"
            f"Min: {min(scores):.3f}\n"
            f"Max: {max(scores):.3f}"
        )
        ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Retrieval scores chart saved: {output_file}")
        plt.close()
    
    def generate_summary_dashboard(self, output_file: str = "crag_dashboard.png"):
        """Generate comprehensive dashboard"""
        metrics = self.extract_metrics()
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Success Rate (pie chart)
        ax1 = fig.add_subplot(gs[0, 0])
        success_count = sum(1 for s in metrics["status"] if s == "Success")
        failed_count = len(metrics["status"]) - success_count
        colors = ['#667eea', '#ff6b6b']
        ax1.pie([success_count, failed_count], labels=['Success', 'Failed'], 
               autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title('Success Rate', fontweight='bold')
        
        # 2. Latency distribution
        ax2 = fig.add_subplot(gs[0, 1:])
        if metrics["latencies"]:
            ax2.hist(metrics["latencies"], bins=10, color='#667eea', alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Latency (ms)', fontweight='bold')
            ax2.set_ylabel('Count', fontweight='bold')
            ax2.set_title('Latency Distribution', fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. Answer Relevance (bar chart)
        ax3 = fig.add_subplot(gs[1, :])
        x = np.arange(len(metrics["answer_relevance"]))
        ax3.bar(x, metrics["answer_relevance"], color='#667eea', alpha=0.8)
        ax3.set_xlabel('Query Index', fontweight='bold')
        ax3.set_ylabel('Relevance', fontweight='bold')
        ax3.set_title('Answer Relevance per Query', fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels([f"Q{i+1}" for i in range(len(metrics["answer_relevance"]))])
        ax3.set_ylim([0, 1.1])
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Key Metrics (text)
        ax4 = fig.add_subplot(gs[2, :])
        ax4.axis('off')
        
        metrics_text = f"""
        📊 KEY METRICS SUMMARY
        
        Total Queries Evaluated: {len(metrics["status"])}
        Success Rate: {(success_count/len(metrics["status"])*100):.1f}%
        
        Latency:
            Average: {statistics.mean(metrics["latencies"]):.1f}ms
            Median: {statistics.median(metrics["latencies"]):.1f}ms
            Min: {min(metrics["latencies"]):.1f}ms
            Max: {max(metrics["latencies"]):.1f}ms
        
        Relevance Scores:
            Answer Avg: {statistics.mean(metrics["answer_relevance"]):.3f}
            Context Avg: {statistics.mean(metrics["context_relevance"]):.3f}
            Retrieval Score Avg: {statistics.mean(metrics["retrieval_scores"]):.3f}
        
        Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        ax4.text(0.05, 0.95, metrics_text, transform=ax4.transAxes,
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.3))
        
        plt.suptitle('CRAG System Evaluation Dashboard', fontsize=16, fontweight='bold', y=0.98)
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Dashboard saved: {output_file}")
        plt.close()
    
    def generate_detailed_report(self, output_file: str = "crag_detailed_analysis.txt"):
        """Generate detailed text report"""
        metrics = self.extract_metrics()
        
        report = []
        report.append("="*80)
        report.append("CRAG SYSTEM - DETAILED PERFORMANCE ANALYSIS")
        report.append("="*80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Overall Statistics
        success_count = sum(1 for s in metrics["status"] if s == "Success")
        report.append("📊 OVERALL STATISTICS")
        report.append("-"*80)
        report.append(f"Total Queries: {len(metrics['status'])}")
        report.append(f"Successful: {success_count}")
        report.append(f"Failed: {len(metrics['status']) - success_count}")
        report.append(f"Success Rate: {(success_count/len(metrics['status'])*100):.1f}%\n")
        
        # Latency Analysis
        if metrics["latencies"]:
            report.append("⚡ LATENCY ANALYSIS (ms)")
            report.append("-"*80)
            report.append(f"Mean: {statistics.mean(metrics['latencies']):.2f}")
            report.append(f"Median: {statistics.median(metrics['latencies']):.2f}")
            report.append(f"Std Dev: {statistics.stdev(metrics['latencies']) if len(metrics['latencies']) > 1 else 0:.2f}")
            report.append(f"Min: {min(metrics['latencies']):.2f}")
            report.append(f"Q1 (25%): {np.percentile(metrics['latencies'], 25):.2f}")
            report.append(f"Q3 (75%): {np.percentile(metrics['latencies'], 75):.2f}")
            report.append(f"Max: {max(metrics['latencies']):.2f}\n")
        
        # Relevance Analysis
        if metrics["answer_relevance"]:
            report.append("🎯 RELEVANCE ANALYSIS")
            report.append("-"*80)
            report.append(f"Answer Relevance Mean: {statistics.mean(metrics['answer_relevance']):.3f}")
            report.append(f"Answer Relevance Min: {min(metrics['answer_relevance']):.3f}")
            report.append(f"Answer Relevance Max: {max(metrics['answer_relevance']):.3f}")
            
            if metrics["context_relevance"]:
                report.append(f"Context Relevance Mean: {statistics.mean(metrics['context_relevance']):.3f}")
                report.append(f"Context Relevance Min: {min(metrics['context_relevance']):.3f}")
                report.append(f"Context Relevance Max: {max(metrics['context_relevance']):.3f}\n")
        
        # Retrieval Score Analysis
        if metrics["retrieval_scores"]:
            report.append("🔍 RETRIEVAL SCORE ANALYSIS")
            report.append("-"*80)
            report.append(f"Mean Document Score: {statistics.mean(metrics['retrieval_scores']):.3f}")
            report.append(f"Median Document Score: {statistics.median(metrics['retrieval_scores']):.3f}")
            report.append(f"Min Document Score: {min(metrics['retrieval_scores']):.3f}")
            report.append(f"Max Document Score: {max(metrics['retrieval_scores']):.3f}\n")
        
        # Individual Query Results
        report.append("📋 INDIVIDUAL QUERY RESULTS")
        report.append("-"*80)
        for i, result in enumerate(self.individual_results, 1):
            query = result.get("query", "Unknown")
            category = result.get("category", "unknown")
            pipeline = result.get("pipeline", {})
            
            status = "✓ PASS" if pipeline.get("success") else "✗ FAIL"
            relevance = pipeline.get("answer_relevance", 0)
            latency = pipeline.get("total_latency_ms", 0)
            num_sources = pipeline.get("num_sources", 0)
            
            report.append(f"\nQuery {i} [{category}] {status}")
            report.append(f"  Text: {query}")
            report.append(f"  Relevance: {relevance:.3f}")
            report.append(f"  Latency: {latency:.1f}ms")
            report.append(f"  Sources: {num_sources}")
        
        report.append("\n" + "="*80)
        
        # Save report
        with open(output_file, 'w') as f:
            f.write("\n".join(report))
        
        print(f"✅ Detailed report saved: {output_file}")


def main():
    """Run analysis"""
    print("\n🔍 CRAG Metrics Analysis Tool")
    print("="*60)
    
    try:
        analyzer = CRAGMetricsAnalyzer()
        
        print("📊 Generating visualizations...")
        analyzer.generate_latency_chart()
        analyzer.generate_relevance_chart()
        analyzer.generate_retrieval_scores_chart()
        analyzer.generate_summary_dashboard()
        analyzer.generate_detailed_report()
        
        print("\n✅ All analysis complete!")
        print("\nGenerated files:")
        print("  - latency_analysis.png")
        print("  - relevance_analysis.png")
        print("  - retrieval_scores.png")
        print("  - crag_dashboard.png")
        print("  - crag_detailed_analysis.txt")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
