#!/usr/bin/env python3
"""
CRAG System Health Monitor

Real-time monitoring of CRAG system performance.
Tracks key metrics and alerts on anomalies.
"""

import requests
import time
import json
from datetime import datetime
from statistics import mean
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from crag_system import CRAGSystem


class HealthMonitor:
    """Monitor CRAG system health in real-time"""
    
    def __init__(self, check_interval: int = 60):
        """Initialize monitor"""
        self.check_interval = check_interval
        self.crag = CRAGSystem()
        self.latency_history = []
        self.error_count = 0
        self.success_count = 0
    
    def check_api(self, timeout: int = 5) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get('http://localhost:8000/health', timeout=timeout)
            return response.status_code == 200
        except:
            return False
    
    def test_query(self, query: str = "What is Meezan Bank?") -> dict:
        """Test a single query"""
        start = time.time()
        try:
            result = self.crag.query(query, top_k=1, use_correction=False)
            latency = (time.time() - start) * 1000
            
            self.latency_history.append(latency)
            if len(self.latency_history) > 100:
                self.latency_history.pop(0)
            
            self.success_count += 1
            
            return {
                "status": "success",
                "latency_ms": latency,
                "answer_length": len(result.get("answer", "")),
                "num_sources": len(result.get("context", []))
            }
        except Exception as e:
            self.error_count += 1
            return {
                "status": "error",
                "error": str(e),
                "latency_ms": (time.time() - start) * 1000
            }
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        total = self.success_count + self.error_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0
        
        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": total,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "api_healthy": self.check_api(),
            "avg_latency_ms": mean(self.latency_history) if self.latency_history else 0,
            "min_latency_ms": min(self.latency_history) if self.latency_history else 0,
            "max_latency_ms": max(self.latency_history) if self.latency_history else 0,
        }
        
        return stats
    
    def print_status(self):
        """Print current status"""
        stats = self.get_stats()
        
        print("\n" + "="*70)
        print("🏥 CRAG SYSTEM HEALTH CHECK")
        print("="*70)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*70)
        
        # API Status
        api_status = "✅ Online" if stats["api_healthy"] else "❌ Offline"
        print(f"API Status:          {api_status}")
        
        # Request Stats
        print(f"Total Requests:      {stats['total_requests']}")
        print(f"Successful:          {stats['success_count']}")
        print(f"Failed:              {stats['error_count']}")
        print(f"Success Rate:        {stats['success_rate']:.1f}%")
        
        # Latency
        print(f"Avg Latency:         {stats['avg_latency_ms']:.1f}ms")
        print(f"Min Latency:         {stats['min_latency_ms']:.1f}ms")
        print(f"Max Latency:         {stats['max_latency_ms']:.1f}ms")
        
        # Alert Section
        print("-"*70)
        print("⚠️  ALERTS:")
        
        alerts = []
        if not stats["api_healthy"]:
            alerts.append("  ❌ API is not responding")
        
        if stats["success_rate"] < 95:
            alerts.append(f"  ⚠️  Success rate below 95% ({stats['success_rate']:.1f}%)")
        
        if stats["avg_latency_ms"] > 3000:
            alerts.append(f"  🐢 High latency detected ({stats['avg_latency_ms']:.1f}ms)")
        
        if stats["error_count"] > 5:
            alerts.append(f"  🔴 Multiple errors detected ({stats['error_count']} errors)")
        
        if not alerts:
            alerts.append("  ✅ No issues detected")
        
        for alert in alerts:
            print(alert)
        
        print("="*70)
        
        return stats
    
    def run_continuous(self, test_interval: int = 5, max_iterations: int = None):
        """Run continuous monitoring"""
        print(f"\n🚀 Starting continuous health monitor")
        print(f"Check interval: {test_interval}s")
        print(f"Press Ctrl+C to stop\n")
        
        iteration = 0
        try:
            while max_iterations is None or iteration < max_iterations:
                iteration += 1
                
                # Test system
                self.test_query()
                
                # Print status every 10 iterations or first run
                if iteration == 1 or iteration % 10 == 0:
                    self.print_status()
                
                # Wait before next check
                time.sleep(test_interval)
        
        except KeyboardInterrupt:
            print("\n\n⛔ Monitor stopped by user")
            self.print_status()
            print(f"\nMonitored for {iteration} iterations")
    
    def generate_report(self, output_file: str = "health_report.json"):
        """Generate health report"""
        stats = self.get_stats()
        
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n📄 Health report saved: {output_file}")


def main():
    """Run monitor"""
    # Quick check (1 minute)
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        monitor = HealthMonitor()
        monitor.run_continuous(test_interval=5, max_iterations=12)  # 60 seconds
    
    # Continuous monitoring
    elif len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        monitor = HealthMonitor()
        monitor.run_continuous(test_interval=60)  # 1 minute intervals
    
    # Single check
    else:
        monitor = HealthMonitor()
        monitor.test_query()
        monitor.print_status()
        monitor.generate_report()


if __name__ == "__main__":
    main()
