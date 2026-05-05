"""
Analyzer for plot_gen_visual_agent benchmark results

Loads and analyzes benchmark results to provide insights and visualizations
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import numpy as np
from collections import defaultdict


class BenchmarkAnalyzer:
    """Analyze and visualize benchmark results"""
    
    def __init__(self, results_file: str = None):
        self.results = []
        self.stats = {}
        
        if results_file:
            self.load_results(results_file)
        else:
            self.load_latest_results()
    
    def load_latest_results(self):
        """Load the most recent benchmark results"""
        results_dir = "./benchmarks/plot_gen_results"
        
        if not os.path.exists(results_dir):
            print(f"Results directory not found: {results_dir}")
            return
        
        json_files = sorted(
            [f for f in os.listdir(results_dir) if f.startswith("benchmark_report_") and f.endswith(".json")],
            reverse=True
        )
        
        if not json_files:
            print("No benchmark results found")
            return
        
        latest_file = os.path.join(results_dir, json_files[0])
        self.load_results(latest_file)
    
    def load_results(self, filepath: str):
        """Load results from JSON file"""
        try:
            with open(filepath, 'r') as f:
                self.results = json.load(f)
            print(f"Loaded {len(self.results)} test results from {filepath}")
            self._analyze_results()
        except Exception as e:
            print(f"Error loading results: {e}")
    
    def _analyze_results(self):
        """Analyze loaded results"""
        
        self.stats = {
            "total": len(self.results),
            "successful": sum(1 for r in self.results if r.get("success")),
            "valid": sum(1 for r in self.results if r.get("is_valid")),
            "by_difficulty": defaultdict(dict),
            "by_test_name": {},
            "errors": []
        }
        
        # Group by difficulty
        for difficulty in ["EASY", "INTERMEDIATE", "ADVANCED"]:
            tests = [r for r in self.results if r.get("difficulty") == difficulty]
            if tests:
                self.stats["by_difficulty"][difficulty] = {
                    "total": len(tests),
                    "successful": sum(1 for t in tests if t.get("success")),
                    "valid": sum(1 for t in tests if t.get("is_valid")),
                    "success_rate": (sum(1 for t in tests if t.get("success")) / len(tests)) * 100,
                    "valid_rate": (sum(1 for t in tests if t.get("is_valid")) / len(tests)) * 100,
                    "avg_time": np.mean([t.get("execution_time", 0) for t in tests]),
                    "min_time": np.min([t.get("execution_time", 0) for t in tests]),
                    "max_time": np.max([t.get("execution_time", 0) for t in tests]),
                    "avg_attempts": np.mean([t.get("attempts", 0) for t in tests]),
                    "max_attempts": np.max([t.get("attempts", 0) for t in tests])
                }
        
        # Individual test analysis
        for result in self.results:
            test_name = result.get("test_name", "unknown")
            self.stats["by_test_name"][test_name] = {
                "success": result.get("success"),
                "valid": result.get("is_valid"),
                "time": result.get("execution_time"),
                "attempts": result.get("attempts"),
                "error": result.get("error")
            }
            
            if result.get("error"):
                self.stats["errors"].append({
                    "test": test_name,
                    "difficulty": result.get("difficulty"),
                    "error": result.get("error")
                })
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "=" * 80)
        print("BENCHMARK ANALYSIS SUMMARY")
        print("=" * 80)
        
        if not self.stats:
            print("No results to analyze")
            return
        
        total = self.stats["total"]
        successful = self.stats["successful"]
        valid = self.stats["valid"]
        
        print(f"\nOverall Statistics:")
        print(f"  Total Tests: {total}")
        print(f"  Successful: {successful}/{total} ({(successful/total)*100:.1f}%)")
        print(f"  Valid: {valid}/{total} ({(valid/total)*100:.1f}%)")
        
        print(f"\n{'Difficulty':<15} {'Total':<8} {'Success':<12} {'Valid':<12} {'Avg Time':<12} {'Avg Attempts'}")
        print("-" * 80)
        
        for difficulty in ["EASY", "INTERMEDIATE", "ADVANCED"]:
            if difficulty in self.stats["by_difficulty"]:
                stats = self.stats["by_difficulty"][difficulty]
                print(f"{difficulty:<15} {stats['total']:<8} "
                      f"{stats['success_rate']:.1f}%{'':<8} "
                      f"{stats['valid_rate']:.1f}%{'':<8} "
                      f"{stats['avg_time']:.2f}s{'':<6} "
                      f"{stats['avg_attempts']:.2f}")
        
        self._print_error_analysis()
        print()
    
    def _print_error_analysis(self):
        """Print error analysis"""
        if not self.stats["errors"]:
            return
        
        print(f"\nErrors ({len(self.stats['errors'])}):")
        
        # Group errors by type
        error_types = defaultdict(list)
        for error in self.stats["errors"]:
            error_msg = error.get("error", "Unknown")
            error_category = error_msg.split(":")[0] if ":" in error_msg else error_msg[:50]
            error_types[error_category].append(error)
        
        for category, errors in error_types.items():
            print(f"  {category}: {len(errors)} occurrences")
            for error in errors[:2]:  # Show first 2 of each type
                print(f"    - [{error['difficulty']}] {error['test'][:40]}...")
    
    def print_test_details(self, test_name: str = None):
        """Print detailed info for specific test(s)"""
        
        if test_name:
            tests = [r for r in self.results if r.get("test_name") == test_name]
        else:
            tests = self.results
        
        print(f"\nTest Details ({len(tests)} tests):")
        print("=" * 80)
        
        for result in tests:
            print(f"\n[{result.get('difficulty')}] {result.get('test_name')}")
            print(f"  Status: {'✓ PASS' if result.get('success') else '✗ FAIL'} "
                  f"(Valid: {'Yes' if result.get('is_valid') else 'No'})")
            print(f"  Time: {result.get('execution_time', 0):.2f}s | "
                  f"Attempts: {result.get('attempts', 0)}")
            
            if result.get("error"):
                print(f"  Error: {result.get('error')}")
            
            if result.get("image_path"):
                print(f"  Image: {result.get('image_path')}")
            
            print(f"  Instruction: {result.get('instruction', '')[:80]}...")
    
    def get_performance_report(self) -> Dict:
        """Get performance report as dictionary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.stats["total"],
            "overall_success_rate": (self.stats["successful"] / self.stats["total"] * 100) if self.stats["total"] > 0 else 0,
            "overall_valid_rate": (self.stats["valid"] / self.stats["total"] * 100) if self.stats["total"] > 0 else 0,
            "by_difficulty": dict(self.stats["by_difficulty"]),
            "error_count": len(self.stats["errors"]),
            "top_errors": self.stats["errors"][:5]
        }
    
    def export_csv(self, output_file: str = None):
        """Export results to CSV"""
        import csv
        
        if output_file is None:
            output_file = f"benchmark_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "Test Name", "Difficulty", "Success", "Valid", 
                    "Execution Time (s)", "Attempts", "Error"
                ])
                
                # Write data
                for result in self.results:
                    writer.writerow([
                        result.get("test_name", ""),
                        result.get("difficulty", ""),
                        "Yes" if result.get("success") else "No",
                        "Yes" if result.get("is_valid") else "No",
                        result.get("execution_time", ""),
                        result.get("attempts", ""),
                        result.get("error", "")
                    ])
            
            print(f"Results exported to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return None
    
    def generate_html_report(self, output_file: str = None) -> str:
        """Generate HTML report"""
        
        if output_file is None:
            output_file = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        report = self.get_performance_report()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Plot Generation Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .stats-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .stats-table th, .stats-table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        .stats-table th {{ background-color: #34495e; color: white; }}
        .stats-table tr:nth-child(even) {{ background-color: #ecf0f1; }}
        .easy {{ background-color: #d5f4e6; }}
        .intermediate {{ background-color: #fff9e6; }}
        .advanced {{ background-color: #ffe6e6; }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .failure {{ color: #e74c3c; font-weight: bold; }}
        .percent {{ color: #3498db; font-weight: bold; }}
        h1, h2 {{ color: #2c3e50; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Plot Generation Benchmark Report</h1>
        <p>Generated: {report['timestamp']}</p>
    </div>
    
    <div class="summary">
        <h2>Overview</h2>
        <div class="metric">
            <strong>Total Tests:</strong> <span class="percent">{report['total_tests']}</span>
        </div>
        <div class="metric">
            <strong>Success Rate:</strong> <span class="percent">{report['overall_success_rate']:.1f}%</span>
        </div>
        <div class="metric">
            <strong>Valid Rate:</strong> <span class="percent">{report['overall_valid_rate']:.1f}%</span>
        </div>
    </div>
    
    <h2>Results by Difficulty Level</h2>
    <table class="stats-table">
        <tr>
            <th>Difficulty</th>
            <th>Total</th>
            <th>Successful</th>
            <th>Success Rate</th>
            <th>Valid Rate</th>
            <th>Avg Time (s)</th>
            <th>Avg Attempts</th>
        </tr>
"""
        
        for difficulty in ["EASY", "INTERMEDIATE", "ADVANCED"]:
            if difficulty in report["by_difficulty"]:
                stats = report["by_difficulty"][difficulty]
                row_class = difficulty.lower()
                html += f"""
        <tr class="{row_class}">
            <td><strong>{difficulty}</strong></td>
            <td>{stats.get('total', 0)}</td>
            <td>{stats.get('successful', 0)}</td>
            <td>{stats.get('success_rate', 0):.1f}%</td>
            <td>{stats.get('valid_rate', 0):.1f}%</td>
            <td>{stats.get('avg_time', 0):.2f}</td>
            <td>{stats.get('avg_attempts', 0):.2f}</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>Key Metrics</h2>
    <ul>
"""
        
        if report["error_count"] > 0:
            html += f"        <li>Errors: {report['error_count']}</li>"
        
        for difficulty in ["EASY", "INTERMEDIATE", "ADVANCED"]:
            if difficulty in report["by_difficulty"]:
                stats = report["by_difficulty"][difficulty]
                if stats.get('max_time'):
                    html += f"        <li>{difficulty} - Max Time: {stats.get('max_time', 0):.2f}s</li>"
        
        html += """
    </ul>
    
</body>
</html>
"""
        
        try:
            with open(output_file, 'w') as f:
                f.write(html)
            print(f"HTML report generated: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error generating HTML report: {e}")
            return None


def main():
    """Main entry point"""
    
    import sys
    
    analyzer = BenchmarkAnalyzer()
    
    if not analyzer.results:
        print("No benchmark results found. Run the benchmark first:")
        print("  python benchmark_plot_gen_visual_agent.py")
        return
    
    # Print summary
    analyzer.print_summary()
    
    # Print detailed results for failed tests
    failed_tests = [r for r in analyzer.results if not r.get("success")]
    if failed_tests:
        print(f"\n\nFailed Tests ({len(failed_tests)}):")
        for test in failed_tests[:5]:
            analyzer.print_test_details(test.get("test_name"))
    
    # Export reports
    analyzer.export_csv()
    analyzer.generate_html_report()
    
    # Print performance report
    report = analyzer.get_performance_report()
    print("\n" + "=" * 80)
    print("FINAL PERFORMANCE REPORT:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
