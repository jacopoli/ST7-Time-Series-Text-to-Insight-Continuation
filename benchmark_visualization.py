"""
Benchmark script for the Visualization Agent.
Tests various visualization scenarios from simple to complex.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

from agents.visualisation_agent import create_visualization_agent
from utils.datastore import DataStore
from utils.states import VisualizationState
from utils.general_helpers import llm_from
from utils.output_basemodels import VisualizationCodeOutput


# ============================================================================
# TEST CASE GENERATOR
# ============================================================================

def generate_test_dataframes() -> Dict[str, pd.DataFrame]:
    """Generate sample dataframes for testing."""
    np.random.seed(42)
    
    # Simple time series data
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df_simple_ts = pd.DataFrame({
        'ts': dates,
        'value': 100 + np.cumsum(np.random.randn(100) * 2),
    })
    
    # Multi-series time series
    df_multi_ts = pd.DataFrame({
        'ts': dates.repeat(3),
        'metric': ['sensor_1', 'sensor_2', 'sensor_3'] * 100,
        'value': np.tile(100 + np.cumsum(np.random.randn(100) * 2), 3),
    })
    
    # Categorical data with time
    df_categorical = pd.DataFrame({
        'timestamp': dates,
        'category': np.random.choice(['A', 'B', 'C', 'D'], 100),
        'count': np.random.poisson(50, 100),
    })
    
    # Multi-metric wide format
    df_wide = pd.DataFrame({
        'date': dates,
        'metric_a': 100 + np.cumsum(np.random.randn(100) * 1.5),
        'metric_b': 50 + np.cumsum(np.random.randn(100) * 1),
        'metric_c': 200 + np.cumsum(np.random.randn(100) * 2),
    })
    
    # Data with missing values
    df_with_nan = df_simple_ts.copy()
    df_with_nan.loc[::10, 'value'] = np.nan
    
    # Site comparison data
    dates_long = pd.date_range('2024-01-01', periods=150, freq='H')
    df_sites = pd.DataFrame({
        'datetime': dates_long.repeat(4),
        'site': ['North', 'South', 'East', 'West'] * 150,
        'temperature': np.concatenate([
            20 + np.cumsum(np.random.randn(150) * 0.5),
            18 + np.cumsum(np.random.randn(150) * 0.6),
            22 + np.cumsum(np.random.randn(150) * 0.4),
            19 + np.cumsum(np.random.randn(150) * 0.7),
        ]),
    })
    
    # Measurements with multiple channels
    df_measurements = pd.DataFrame({
        'time': pd.date_range('2024-01-01', periods=120, freq='15min').repeat(5),
        'channel': ['CH1', 'CH2', 'CH3', 'CH4', 'CH5'] * 120,
        'reading': np.random.normal(100, 15, 600),
    })
    
    # Statistics aggregation
    df_stats = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=30, freq='D').repeat(3),
        'type': ['min', 'mean', 'max'] * 30,
        'value': np.random.uniform(10, 100, 90),
    })
    
    return {
        'simple_ts': df_simple_ts,
        'multi_ts': df_multi_ts,
        'categorical': df_categorical,
        'wide_metrics': df_wide,
        'with_nan': df_with_nan,
        'multi_site': df_sites,
        'measurements': df_measurements,
        'statistics': df_stats,
    }


# ============================================================================
# BENCHMARK SCENARIOS
# ============================================================================

def create_benchmark_scenarios() -> List[Dict[str, Any]]:
    """Create a comprehensive list of visualization test scenarios."""
    scenarios = [
        # ===== SIMPLE SCENARIOS =====
        {
            'id': 'viz_001',
            'difficulty': 'simple',
            'question': 'Create a simple line chart of the time series data.',
            'dataframes': ['simple_ts'],
            'expected_chart_type': 'line',
            'description': 'Basic line plot with time on x-axis',
        },
        {
            'id': 'viz_002',
            'difficulty': 'simple',
            'question': 'Plot the values as a bar chart.',
            'dataframes': ['categorical'],
            'expected_chart_type': 'bar',
            'description': 'Bar chart showing counts by category',
        },
        {
            'id': 'viz_003',
            'difficulty': 'simple',
            'question': 'Create a scatter plot of the measurements.',
            'dataframes': ['measurements'],
            'expected_chart_type': 'scatter',
            'description': 'Scatter plot of channel readings',
        },
        # ===== INTERMEDIATE SCENARIOS =====
        {
            'id': 'viz_004',
            'difficulty': 'intermediate',
            'question': 'Plot multiple metrics on the same chart with legend and labels.',
            'dataframes': ['wide_metrics'],
            'expected_chart_type': 'line',
            'description': 'Multi-line chart with proper labels and legend',
        },
        {
            'id': 'viz_005',
            'difficulty': 'intermediate',
            'question': 'Create a grouped bar chart comparing statistics (min, mean, max).',
            'dataframes': ['statistics'],
            'expected_chart_type': 'bar',
            'description': 'Grouped bar chart with categories',
        },
        {
            'id': 'viz_006',
            'difficulty': 'intermediate',
            'question': 'Plot time series with multiple sensor data in subplots.',
            'dataframes': ['multi_ts'],
            'expected_chart_type': 'line',
            'description': 'One subplot per sensor',
        },
        {
            'id': 'viz_007',
            'difficulty': 'intermediate',
            'question': 'Create a heatmap of the multi-site temperature data.',
            'dataframes': ['multi_site'],
            'expected_chart_type': 'heatmap',
            'description': 'Heatmap with sites as rows and time as columns',
        },
        # ===== COMPLEX SCENARIOS =====
        {
            'id': 'viz_008',
            'difficulty': 'complex',
            'question': 'Plot the data with missing values (NaN), handle gracefully and visualize what data is available.',
            'dataframes': ['with_nan'],
            'expected_chart_type': 'line',
            'description': 'Handles NaN values appropriately',
        },
        {
            'id': 'viz_009',
            'difficulty': 'complex',
            'question': 'Compare temperature trends across all four sites on the same plot with color differentiation.',
            'dataframes': ['multi_site'],
            'expected_chart_type': 'line',
            'description': 'Multi-line chart with different colors per site',
        },
        {
            'id': 'viz_010',
            'difficulty': 'complex',
            'question': 'Create a combined visualization: a line chart for temperature trends with a secondary y-axis.',
            'dataframes': ['multi_site'],
            'expected_chart_type': 'line',
            'description': 'Dual-axis plot with different units',
        },
        {
            'id': 'viz_011',
            'difficulty': 'complex',
            'question': 'Visualize the distribution of measurements across channels using boxplots.',
            'dataframes': ['measurements'],
            'expected_chart_type': 'boxplot',
            'description': 'Boxplot showing distribution per channel',
        },
        {
            'id': 'viz_012',
            'difficulty': 'complex',
            'question': 'Create a time series with confidence intervals or error bands.',
            'dataframes': ['multi_ts'],
            'expected_chart_type': 'line',
            'description': 'Time series with error bands',
        },
        {
            'id': 'viz_013',
            'difficulty': 'complex',
            'question': 'Generate a dashboard-style visualization with 4 subplots showing different aspects of the data.',
            'dataframes': ['simple_ts', 'wide_metrics'],
            'expected_chart_type': 'multi-subplot',
            'description': '4-panel dashboard layout',
        },
        # ===== EDGE CASES =====
        {
            'id': 'viz_014',
            'difficulty': 'complex',
            'question': 'Visualize data where some time periods have no measurements at all.',
            'dataframes': ['with_nan'],
            'expected_chart_type': 'line',
            'description': 'Handle sparse data gracefully',
        },
        {
            'id': 'viz_015',
            'difficulty': 'complex',
            'question': 'Create a heatmap correlation matrix for numeric columns in the wide metrics data.',
            'dataframes': ['wide_metrics'],
            'expected_chart_type': 'heatmap',
            'description': 'Correlation heatmap of numeric columns',
        },
        {
            'id': 'viz_016',
            'difficulty': 'intermediate',
            'question': 'Show the time series decomposition of the simple time series data.',
            'dataframes': ['simple_ts'],
            'expected_chart_type': 'line',
            'description': 'Multi-panel decomposition plot',
        },
        {
            'id': 'viz_017',
            'difficulty': 'intermediate',
            'question': 'Create a cumulative distribution plot for the measurement readings.',
            'dataframes': ['measurements'],
            'expected_chart_type': 'line',
            'description': 'CDF plot of readings',
        },
        {
            'id': 'viz_018',
            'difficulty': 'simple',
            'question': 'Create a histogram showing the distribution of categorical values.',
            'dataframes': ['categorical'],
            'expected_chart_type': 'histogram',
            'description': 'Histogram of category counts',
        },
        {
            'id': 'viz_019',
            'difficulty': 'intermediate',
            'question': 'Create a violin plot showing the distribution of temperature by site.',
            'dataframes': ['multi_site'],
            'expected_chart_type': 'violin',
            'description': 'Violin distribution plot per site',
        },
        {
            'id': 'viz_020',
            'difficulty': 'complex',
            'question': 'Generate an interactive-style visualization with multiple metrics aligned on time axis with proper formatting.',
            'dataframes': ['multi_ts', 'multi_site'],
            'expected_chart_type': 'multi-line',
            'description': 'Complex multi-metric time series',
        },
    ]
    return scenarios


# ============================================================================
# VISUALIZATION AGENT EXECUTION
# ============================================================================

def run_visualization_benchmark(
    instruction: str,
    dataframe_keys: List[str],
    test_dataframes: Dict[str, pd.DataFrame],
    llm,
    output_dir: Path,
    scenario_id: str = '',
) -> Dict[str, Any]:
    """
    Execute visualization agent for a given instruction and dataset.
    Returns metrics including execution success, attempts, and scoring data.
    """
    
    # Prepare datastore with selected dataframes
    datastore = DataStore()
    for key in dataframe_keys:
        if key in test_dataframes:
            df = test_dataframes[key]
            datastore.put(df, ref=key, description=f"Test dataset: {key}")
    
    # Create visualization agent - visualisation_agent handles everything from here
    viz_graph = create_visualization_agent(llm)
    
    # Build initial state for the visualization workflow
    initial_state: VisualizationState = {
        'instruction': instruction,
        'datastore': datastore,
        'datastore_summary': '',
        'datastore_obj': datastore,
        'datastore_frames': {},
        'input_profile': [],
        'input_profile_summary': '',
        'chart_plan': {},
        'visualization_code': '',
        'visualization_code_summary': '',
        'visualization_codegen_attempts': 0,
        'visualization_error_context': None,
        'selected_dataset': dataframe_keys[0] if dataframe_keys else '',
        'detected_columns': {},
        'output_path': str(output_dir),
        'output_paths': [],
        'visualizations': [],
        'warnings': [],
        'error_message': None,
        'visualization_agent_final_answer': '',
    }
    
    execution_success = False
    error_message = None
    llm_attempts = 0
    generated_code = ''
    output_paths: List[str] = []
    warnings: List[str] = []
    final_answer = ''
    
    try:
        # Execute the visualization graph
        final_state = viz_graph.invoke(initial_state)
        
        # Extract metrics from final state
        llm_attempts = int(final_state.get('visualization_codegen_attempts', 0)) + 1
        generated_code = final_state.get('visualization_code', '')
        output_paths = final_state.get('output_paths', [])
        warnings = final_state.get('warnings', [])
        error_message = final_state.get('error_message')
        final_answer = final_state.get('visualization_agent_final_answer', '')
        
        # Determine success: if visualizations were generated without critical error
        output_paths = final_state.get('output_paths', [])
        execution_success = (
            len(output_paths) > 0 and 
            not error_message and 
            len(generated_code) > 0
        )
        
    except (OSError, ValueError) as e:
        execution_success = False
        error_message = str(e)
        llm_attempts = 1
        print(f"   Error executing visualization: {e}")
    
    # Save generated code to file
    code_file = None
    if generated_code and scenario_id:
        code_dir = output_dir / 'generated_code'
        code_dir.mkdir(parents=True, exist_ok=True)
        code_file = code_dir / f'{scenario_id}.py'
        try:
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(generated_code)
        except Exception as e:
            print(f"   Warning: Could not save code file: {e}")
    
    return {
        'execution_success': execution_success,
        'llm_calls_count': llm_attempts,
        'readability_score': 0,  # Placeholder: would be filled by human review
        'coherence_score': 0,    # Placeholder: would be filled by human review
        'error_message': error_message,
        'generated_code': generated_code,
        'code_file': str(code_file) if code_file else '',
        'output_paths': output_paths,
        'warnings': warnings,
        'final_answer': final_answer,
    }


# ============================================================================
# MAIN BENCHMARK
# ============================================================================

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Benchmark the Visualization Agent')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of scenarios')
    parser.add_argument('--start', type=int, default=0, help='Start index')
    parser.add_argument('--output', type=str, default='visualization_benchmark_results.xlsx',
                        help='Output Excel file')
    parser.add_argument('--output-dir', type=str, default='benchmarks/viz_results',
                        help='Output directory for generated visualizations')
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize LLM once - will be reused for all benchmarks
    llm = llm_from(agent_name="Visualization Agent").with_structured_output(VisualizationCodeOutput)
    
    # Generate test data
    print("[*] Generating test dataframes...")
    test_dataframes = generate_test_dataframes()
    print(f"    Generated {len(test_dataframes)} test datasets")
    for key, df in test_dataframes.items():
        print(f"    - {key}: {len(df)} rows, {len(df.columns)} columns")
    
    # Save test dataframes for later use
    data_dir = output_dir / 'test_data'
    data_dir.mkdir(parents=True, exist_ok=True)
    for key, df in test_dataframes.items():
        try:
            csv_path = data_dir / f'{key}.csv'
            df.to_csv(csv_path, index=False)
            print(f"    Saved: {csv_path}")
        except Exception as e:
            print(f"    Warning: Could not save {key}: {e}")
    
    # Get scenarios
    print("\n[*] Loading benchmark scenarios...")
    scenarios = create_benchmark_scenarios()
    print(f"    Total scenarios: {len(scenarios)}")
    
    # Slice scenarios
    scenarios_slice = scenarios[args.start:]
    if args.limit is not None:
        scenarios_slice = scenarios_slice[:args.limit]
    
    # Run benchmarks
    results = []
    
    for i, scenario in enumerate(scenarios_slice):
        scenario_id = scenario.get('id', f'scenario_{i}')
        question = scenario.get('question', '')
        difficulty = scenario.get('difficulty', 'unknown')
        expected_chart = scenario.get('expected_chart_type', 'unknown')
        description = scenario.get('description', '')
        dataframe_keys = scenario.get('dataframes', [])
        
        progress = i + args.start + 1
        total = len(scenarios_slice) + args.start
        print(f"\n[{progress}/{total}] {scenario_id} ({difficulty})")
        print(f"    Question: {question}")
        print(f"    Datasets: {', '.join(dataframe_keys)}")
        
        try:
            result = run_visualization_benchmark(
                instruction=question,
                dataframe_keys=dataframe_keys,
                test_dataframes=test_dataframes,
                llm=llm,
                output_dir=output_dir,
                scenario_id=scenario_id,
            )
        except (OSError, ValueError, RuntimeError) as e:
            print(f"    ✗ EXCEPTION: {e}")
            result = {
                'execution_success': False,
                'llm_calls_count': 0,
                'readability_score': 0,
                'coherence_score': 0,
                'error_message': str(e),
                'generated_code': '',
                'output_paths': [],
                'warnings': [],
                'final_answer': '',
            }
        
        # Collect row data
        row = {
            'Scenario ID': scenario_id,
            'Difficulty': difficulty,
            'Question': question,
            'Expected Chart Type': expected_chart,
            'Description': description,
            'Datasets Used': ', '.join(dataframe_keys),
            'Execution Success': result['execution_success'],
            'LLM Attempts': result['llm_calls_count'],
            'Readability Score': result['readability_score'],
            'Coherence Score': result['coherence_score'],
            'Average Quality Score': (result['readability_score'] + result['coherence_score']) / 2,
            'Error Message': (result['error_message'] or 'N/A')[:200],
            'Code File': result.get('code_file', ''),
            'Output Paths': '; '.join(result['output_paths'][:2]) if result['output_paths'] else 'N/A',
            'Warnings Count': len(result['warnings']),
            'Final Answer': (result['final_answer'] or 'N/A')[:100],
        }
        
        results.append(row)
        
        # Save progress incrementally
        df = pd.DataFrame(results)
        if args.output.endswith('.csv'):
            df.to_csv(args.output, index=False)
        else:
            try:
                df.to_excel(args.output, index=False)
            except ImportError:
                print("    Warning: openpyxl not installed, saving as CSV instead")
                args.output = args.output.replace('.xlsx', '.csv')
                df.to_csv(args.output, index=False)
        
        status = "✓" if result['execution_success'] else "✗"
        print(f"    {status} Success={result['execution_success']}, Attempts={result['llm_calls_count']}, Outputs={len(result['output_paths'])}")
        if result.get('code_file'):
            print(f"    Code: {result['code_file']}")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    
    df_results = pd.DataFrame(results)
    
    total_count = len(results)
    success_count = (df_results['Execution Success'].sum())
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    avg_attempts = df_results['LLM Attempts'].mean() if total_count > 0 else 0
    
    print(f"Total Scenarios: {total_count}")
    print(f"Successful: {success_count}/{total_count} ({success_rate:.1f}%)")
    print(f"Average LLM Attempts: {avg_attempts:.2f}")
    print(f"Output File: {args.output}")
    print(f"Visualizations Dir: {output_dir}")
    print()
    
    # Breakdown by difficulty
    for difficulty in ['simple', 'intermediate', 'complex']:
        subset = df_results[df_results['Difficulty'] == difficulty]
        if len(subset) > 0:
            success_rate_diff = (subset['Execution Success'].sum() / len(subset) * 100)
            print(f"  {difficulty.upper()}: {success_rate_diff:.1f}% success ({len(subset)} scenarios)")
    
    print("=" * 80)
    
    # Save JSON summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_scenarios': total_count,
        'successful_scenarios': int(success_count),
        'success_rate': float(success_rate),
        'average_attempts': float(avg_attempts),
        'by_difficulty': {},
    }
    
    for difficulty in ['simple', 'intermediate', 'complex']:
        subset = df_results[df_results['Difficulty'] == difficulty]
        if len(subset) > 0:
            summary['by_difficulty'][difficulty] = {
                'count': len(subset),
                'success_rate': float(subset['Execution Success'].sum() / len(subset) * 100),
            }
    
    summary_file = output_dir / 'benchmark_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to: {summary_file}")


if __name__ == '__main__':
    main()
