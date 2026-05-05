"""
Benchmark for plot_gen_visual_agent.py

Tests the plot generation agent with progressively complex visualization requests
based on the three datasets:
- gateways_configs_sensors(in).csv
- projects_sites(in).csv  
- variables_metrics_raw_data(in).csv

Difficulty levels: EASY -> INTERMEDIATE -> ADVANCED
"""

import os
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.plot_gen_visual_agent import build_plotgen_graph, PlotGenState


class PlotGenBenchmark:
    """Benchmark suite for plot generation agent"""
    
    def __init__(self, datasets_path: str = "./datasets"):
        self.datasets_path = datasets_path
        self.results = []
        self.data_summaries = {}
        self._load_datasets()
    
    def _load_datasets(self):
        """Load and summarize the available datasets"""
        try:
            # Load raw measurements
            self.raw_data = pd.read_csv(
                os.path.join(self.datasets_path, "variables_metrics_raw_data-1760453175763(in).csv")
            )
            self.data_summaries["raw_data"] = f"""
Time-series Data: {len(self.raw_data)} records
- Gateways: {self.raw_data['gateway_name'].nunique()}
- Variables: {self.raw_data['variable_name'].nunique()}
- Date range: {self.raw_data['timestamp'].min()} to {self.raw_data['timestamp'].max()}
- Metrics available: {', '.join(self.raw_data['metric'].unique())}
- Units: {', '.join(self.raw_data['unit'].unique())}
            """
            
            # Load projects/sites
            self.sites_data = pd.read_csv(
                os.path.join(self.datasets_path, "projects_sites(in).csv"),
                sep=";"
            )
            self.data_summaries["sites"] = f"""
Projects & Sites: {len(self.sites_data)} records
- Sites: {self.sites_data['name_2'].nunique()}
- Time zones: {self.sites_data['time_zone'].nunique()}
- Operating rates: {self.sites_data['operating_rate'].min()} to {self.sites_data['operating_rate'].max()}
            """
            
            # Load gateway configs
            self.gateway_data = pd.read_csv(
                os.path.join(self.datasets_path, "gateways_configs_sensors(in).csv")
            )
            self.data_summaries["gateways"] = f"""
Gateway Configs: {len(self.gateway_data)} records
- Gateways: {self.gateway_data.iloc[:, 1].nunique() if len(self.gateway_data.columns) > 1 else 0}
            """
            
        except Exception as e:
            print(f"Error loading datasets: {e}")
            self.raw_data = None
            self.sites_data = None
            self.gateway_data = None
    
    def _create_data_summary(self) -> str:
        """Create concatenated data summary for the agent"""
        summary = "Available Datasets:\n"
        for key, value in self.data_summaries.items():
            summary += f"\n{key.upper()}:{value}"
        return summary
    
    def _execute_test(self, instruction: str, test_name: str, difficulty: str) -> Dict:
        """Execute a single plot generation test"""
        
        start_time = time.time()
        result = {
            "test_name": test_name,
            "difficulty": difficulty,
            "instruction": instruction,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "execution_time": 0,
            "image_path": None,
            "valid": False
        }
        
        try:
            # Build and invoke the plot generation graph
            graph = build_plotgen_graph()
            data_summary = self._create_data_summary()
            
            initial_state = PlotGenState(
                instruction=instruction,
                data_summary=data_summary,
                plan=None,
                code=None,
                image_path=None,
                error_log=None,
                numeric_feedback=None,
                lexical_feedback=None,
                visual_feedback=None,
                is_valid=False,
                attempts=0
            )
            
            # Execute the graph
            final_state = graph.invoke(initial_state)
            
            result["execution_time"] = time.time() - start_time
            result["success"] = True
            result["is_valid"] = final_state.get("is_valid", False)
            result["image_path"] = final_state.get("image_path")
            result["attempts"] = final_state.get("attempts", 0)
            
            # Check for validation errors
            if final_state.get("error_log"):
                result["error"] = f"Execution error: {final_state['error_log']}"
            if final_state.get("numeric_feedback"):
                result["error"] = f"Numeric validation issue: {final_state['numeric_feedback']}"
            if final_state.get("lexical_feedback"):
                result["error"] = f"Lexical validation issue: {final_state['lexical_feedback']}"
            if final_state.get("visual_feedback"):
                result["error"] = f"Visual validation issue: {final_state['visual_feedback']}"
                
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            result["execution_time"] = time.time() - start_time
        
        return result
    
    def create_easy_tests(self) -> List[Tuple[str, str]]:
        """EASY level tests: Single metric, time-series line plot"""
        tests = [
            (
                "Create a simple line chart showing Acceleration measurements over time",
                "test_easy_01_acceleration_timeseries"
            ),
            (
                "Plot the Temperature values across all gateways",
                "test_easy_02_temperature_plot"
            ),
            (
                "Show a bar chart of operating rates for different sites",
                "test_easy_03_operating_rates"
            ),
            (
                "Display a histogram of variable values distribution",
                "test_easy_04_distribution"
            ),
            (
                "Create a scatter plot of sensor readings",
                "test_easy_05_scatter"
            )
        ]
        return tests
    
    def create_intermediate_tests(self) -> List[Tuple[str, str]]:
        """INTERMEDIATE level tests: Multiple metrics, filtering, aggregations"""
        tests = [
            (
                "Create a multi-line chart comparing different sensors' acceleration over time, "
                "with different colors for each sensor",
                "test_intermediate_01_multi_sensor"
            ),
            (
                "Plot acceleration measurements by gateway, showing the average and standard deviation bars",
                "test_intermediate_02_agg_by_gateway"
            ),
            (
                "Create a time-series plot with two Y-axes: one for acceleration and one for temperature, "
                "if available",
                "test_intermediate_03_dual_axis"
            ),
            (
                "Generate a heatmap showing the correlation between different metrics across gateways",
                "test_intermediate_04_correlation_heatmap"
            ),
            (
                "Create subplots: one for each major gateway showing their acceleration trends",
                "test_intermediate_05_subplots"
            ),
            (
                "Plot the time-series data with a rolling average (7-day window) overlay",
                "test_intermediate_06_rolling_avg"
            )
        ]
        return tests
    
    def create_advanced_tests(self) -> List[Tuple[str, str]]:
        """ADVANCED level tests: Complex transformations, statistical analysis, multi-dimensional"""
        tests = [
            (
                "Create a comprehensive dashboard with 4 subplots: "
                "(1) Time-series of raw acceleration, (2) Distribution histogram, "
                "(3) Box plots by gateway, (4) Daily aggregated statistics",
                "test_advanced_01_dashboard"
            ),
            (
                "Generate a time-series decomposition plot showing trend, seasonality, and residuals "
                "for the acceleration data",
                "test_advanced_02_timeseries_decomposition"
            ),
            (
                "Create an interactive-style plot showing anomalies detected using statistical methods "
                "(values beyond 2 standard deviations), with highlighted outlier regions",
                "test_advanced_03_anomaly_detection"
            ),
            (
                "Plot the correlation matrix as a heatmap with hierarchical clustering for all available metrics, "
                "using annotations for correlation values",
                "test_advanced_04_clustered_heatmap"
            ),
            (
                "Create a faceted plot comparing the distribution of measurements across different time periods "
                "(morning/afternoon/evening) and different gateways, with violin plots",
                "test_advanced_05_faceted_violin"
            ),
            (
                "Generate a comprehensive time-series analysis plot with:"
                "(1) Raw data line, (2) Exponential moving average, (3) Bollinger bands (±2 std), "
                "(4) Signal strength indicator (colored background)",
                "test_advanced_06_technical_analysis"
            ),
            (
                "Create a 3D scatter plot visualization if possible, or an equivalent 2D projection showing "
                "relationships between acceleration, timestamp, and gateway with size/color encoding",
                "test_advanced_07_multidimensional"
            ),
            (
                "Generate a statistical summary visualization showing hypothesis test results, "
                "p-values distribution, and effect sizes between different gateways",
                "test_advanced_08_statistical_summary"
            )
        ]
        return tests
    
    def run_benchmark_suite(self) -> Dict:
        """Run all benchmarks and collect results"""
        
        print("=" * 80)
        print("PLOT GENERATION AGENT BENCHMARK SUITE")
        print("=" * 80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        all_tests = []
        
        # Run EASY tests
        print("Running EASY tests...")
        easy_tests = self.create_easy_tests()
        for instruction, test_name in easy_tests:
            result = self._execute_test(instruction, test_name, "EASY")
            self.results.append(result)
            all_tests.append(result)
            print(f"  [{result['difficulty']}] {test_name}: {('✓ PASS' if result['success'] else '✗ FAIL')}")
        
        print()
        
        # Run INTERMEDIATE tests
        print("Running INTERMEDIATE tests...")
        intermediate_tests = self.create_intermediate_tests()
        for instruction, test_name in intermediate_tests:
            result = self._execute_test(instruction, test_name, "INTERMEDIATE")
            self.results.append(result)
            all_tests.append(result)
            print(f"  [{result['difficulty']}] {test_name}: {('✓ PASS' if result['success'] else '✗ FAIL')}")
        
        print()
        
        # Run ADVANCED tests
        print("Running ADVANCED tests...")
        advanced_tests = self.create_advanced_tests()
        for instruction, test_name in advanced_tests:
            result = self._execute_test(instruction, test_name, "ADVANCED")
            self.results.append(result)
            all_tests.append(result)
            print(f"  [{result['difficulty']}] {test_name}: {('✓ PASS' if result['success'] else '✗ FAIL')}")
        
        print()
        print("=" * 80)
        
        # Generate summary report
        summary = self._generate_summary(all_tests)
        return summary
    
    def _generate_summary(self, tests: List[Dict]) -> Dict:
        """Generate summary statistics"""
        
        summary = {
            "total_tests": len(tests),
            "timestamp": datetime.now().isoformat(),
            "by_difficulty": {},
            "overall_success_rate": 0,
            "overall_valid_rate": 0,
            "avg_execution_time": 0,
            "avg_attempts": 0,
            "errors": [],
            "details": tests
        }
        
        if not tests:
            return summary
        
        # Calculate overall metrics
        successful = sum(1 for t in tests if t["success"])
        valid = sum(1 for t in tests if t.get("is_valid", False))
        
        summary["overall_success_rate"] = (successful / len(tests)) * 100
        summary["overall_valid_rate"] = (valid / len(tests)) * 100
        summary["avg_execution_time"] = np.mean([t["execution_time"] for t in tests])
        summary["avg_attempts"] = np.mean([t.get("attempts", 0) for t in tests])
        
        # Collect errors
        summary["errors"] = [
            {
                "test": t["test_name"],
                "error": t["error"],
                "difficulty": t["difficulty"]
            }
            for t in tests if t["error"]
        ]
        
        # Break down by difficulty
        for difficulty in ["EASY", "INTERMEDIATE", "ADVANCED"]:
            difficulty_tests = [t for t in tests if t["difficulty"] == difficulty]
            if difficulty_tests:
                successful_diff = sum(1 for t in difficulty_tests if t["success"])
                valid_diff = sum(1 for t in difficulty_tests if t.get("is_valid", False))
                summary["by_difficulty"][difficulty] = {
                    "total": len(difficulty_tests),
                    "successful": successful_diff,
                    "valid": valid_diff,
                    "success_rate": (successful_diff / len(difficulty_tests)) * 100,
                    "valid_rate": (valid_diff / len(difficulty_tests)) * 100,
                    "avg_execution_time": np.mean([t["execution_time"] for t in difficulty_tests]),
                    "avg_attempts": np.mean([t.get("attempts", 0) for t in difficulty_tests])
                }
        
        # Print summary
        print("BENCHMARK SUMMARY REPORT")
        print("=" * 80)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Overall Success Rate: {summary['overall_success_rate']:.2f}%")
        print(f"Overall Valid Rate: {summary['overall_valid_rate']:.2f}%")
        print(f"Average Execution Time: {summary['avg_execution_time']:.2f}s")
        print(f"Average Attempts: {summary['avg_attempts']:.2f}")
        print()
        
        for difficulty in ["EASY", "INTERMEDIATE", "ADVANCED"]:
            if difficulty in summary["by_difficulty"]:
                stats = summary["by_difficulty"][difficulty]
                print(f"{difficulty} Level:")
                print(f"  Tests: {stats['total']} | Success: {stats['success_rate']:.2f}% | Valid: {stats['valid_rate']:.2f}%")
                print(f"  Avg Time: {stats['avg_execution_time']:.2f}s | Avg Attempts: {stats['avg_attempts']:.2f}")
                print()
        
        if summary["errors"]:
            print(f"Errors ({len(summary['errors'])}):")
            for error in summary["errors"][:5]:  # Show first 5 errors
                print(f"  - [{error['difficulty']}] {error['test']}: {error['error'][:100]}...")
            print()
        
        print("=" * 80)
        
        return summary
    
    def save_results(self, output_path: str = "./benchmarks/plot_gen_results/"):
        """Save benchmark results to file"""
        os.makedirs(output_path, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(output_path, f"benchmark_report_{timestamp}.json")
        
        # Convert numpy types to Python types for JSON serialization
        serializable_results = []
        for result in self.results:
            item = result.copy()
            for key in item:
                if isinstance(item[key], (np.floating, np.integer)):
                    item[key] = float(item[key])
            serializable_results.append(item)
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Results saved to: {results_file}")
        return results_file


def main():
    """Main entry point for benchmark"""
    
    # Initialize benchmark
    benchmark = PlotGenBenchmark(datasets_path="./datasets")
    
    # Run all tests
    summary = benchmark.run_benchmark_suite()
    
    # Save results
    benchmark.save_results()
    
    return summary


if __name__ == "__main__":
    main()
