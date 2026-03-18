"""
Simplified Benchmark for the Visualization Agent.
Loads test scenarios from benchmark_visualization.json and test data from CSV files.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from agents.visualisation_agent import create_visualization_agent
from utils.datastore import DataStore
from utils.states import VisualizationState
from utils.general_helpers import llm_from
from utils.output_basemodels import VisualizationCodeOutput


# ============================================================================
# CONFIGURATION
# ============================================================================


TEST_DATA_DIR = Path('benchmarks/viz_results/test_data')
SCENARIOS_FILE = TEST_DATA_DIR / 'benchmark_visualization.json'
RESULTS_DIR = Path('benchmarks/viz_results')
GENERATED_CODE_DIR = RESULTS_DIR / 'generated_code'


# ============================================================================
# LOAD SCENARIOS AND DATA
# ============================================================================

def load_scenarios(scenarios_file: str) -> List[Dict[str, Any]]:
    """Load test scenarios from JSON file."""
    path = Path(scenarios_file)
    if not path.exists():
        print(f"[✗] Error: {scenarios_file} not found")
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        scenarios = data.get("benchmark_scenarios", [])
        print(f"[✓] Loaded {len(scenarios)} scenarios")
        return scenarios
    except Exception as e:
        print(f"[✗] Error loading scenarios: {e}")
        return []


def load_test_data(data_dir: Path = TEST_DATA_DIR) -> Dict[str, pd.DataFrame]:
    """Load all CSV test data files."""
    datasets = {}
    
    if not data_dir.exists():
        print(f"[✗] Test data directory not found: {data_dir}")
        return datasets
    
    for csv_file in sorted(data_dir.glob('*.csv')):
        key = csv_file.stem
        try:
            df = pd.read_csv(csv_file)
            # Parse datetime columns
            for col in df.columns:
                if any(hint in col.lower() for hint in ['time', 'timestamp', 'date', 'datetime', 'ts']):
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except Exception:
                        pass
            datasets[key] = df
        except Exception as e:
            print(f"[!] Warning: Could not load {key}: {e}")
    
    print(f"[✓] Loaded {len(datasets)} test datasets")
    return datasets


# ============================================================================
# RUN VISUALIZATION BENCHMARK
# ============================================================================

def run_benchmark_scenario(
    scenario: Dict[str, Any],
    test_data: Dict[str, pd.DataFrame],
    llm,
    output_dir: Path,
) -> Dict[str, Any]:
    """Execute one benchmark scenario."""
    scenario_id = scenario.get('id', 'unknown')
    question = scenario.get('question', '')
    dataframe_keys = scenario.get('dataframes', [])
    
    # Prepare datastore
    datastore = DataStore()
    for key in dataframe_keys:
        if key in test_data:
            datastore.put(test_data[key], ref=key, description=f"Test dataset: {key}")
    
    # Create and execute visualization agent
    viz_graph = create_visualization_agent(llm)
    initial_state: VisualizationState = {
        'instruction': question,
        'datastore': datastore,
        'datastore_obj': datastore,
        'output_path': str(output_dir),
        'output_paths': [],
        'visualizations': [],
        'warnings': [],
        'error_message': None,
    }
    
    try:
        final_state = viz_graph.invoke(initial_state)
        llm_attempts = int(final_state.get('visualization_codegen_attempts', 0)) + 1
        generated_code = final_state.get('visualization_code', '')
        output_paths = final_state.get('output_paths', [])
        error_message = final_state.get('error_message')
        execution_success = len(output_paths) > 0 and not error_message
    except Exception as e:
        llm_attempts = 1
        generated_code = ''
        output_paths = []
        error_message = str(e)
        execution_success = False
        print(f"    [✗] Error: {e}")
    
    # Save code
    code_file = None
    if generated_code and scenario_id:
        GENERATED_CODE_DIR.mkdir(parents=True, exist_ok=True)
        code_file = GENERATED_CODE_DIR / f'{scenario_id}.py'
        try:
            code_file.write_text(generated_code, encoding='utf-8')
        except Exception as e:
            print(f"    [!] Could not save code: {e}")
    
    return {
        'execution_success': execution_success,
        'llm_attempts': llm_attempts,
        'code_file': str(code_file) if code_file else '',
        'output_paths': output_paths,
        'error_message': error_message,
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Benchmark the Visualization Agent')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of scenarios')
    parser.add_argument('--start', type=int, default=0, help='Start index')
    parser.add_argument('--output', type=str, default='visualization_benchmark_results.xlsx')
    args = parser.parse_args()
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\n[*] Loading scenarios and test data...")
    scenarios = load_scenarios(SCENARIOS_FILE)
    test_data = load_test_data(TEST_DATA_DIR)
    
    if not scenarios or not test_data:
        print("[✗] Missing scenarios or test data")
        return 1
    
    # Initialize LLM
    print("[*] Initializing LLM...")
    llm = llm_from(agent_name="Visualization Agent").with_structured_output(VisualizationCodeOutput)
    
    # Run benchmarks
    scenarios_slice = scenarios[args.start:]
    if args.limit:
        scenarios_slice = scenarios_slice[:args.limit]
    
    print(f"\n[*] Running {len(scenarios_slice)} scenarios...\n")
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
        
        print(f"[{progress}/{total}] {scenario_id} ({difficulty})")
        print(f"    Q: {question[:70]}...")
        
        result = run_benchmark_scenario(scenario, test_data, llm, RESULTS_DIR)
        
        row = {
            'Scenario ID': scenario_id,
            'Difficulty': difficulty,
            'Question': question,
            'Expected Chart': expected_chart,
            'Description': description,
            'Datasets': ', '.join(dataframe_keys),
            'Success': result['execution_success'],
            'Attempts': result['llm_attempts'],
            'Code File': result['code_file'],
            'Error': (result['error_message'] or 'N/A')[:100],
        }
        results.append(row)
        
        status = "✓" if result['execution_success'] else "✗"
        print(f"    {status} {result['execution_success']}, Attempts: {result['llm_attempts']}\n")
        
        # Save incrementally
        df = pd.DataFrame(results)
        if args.output.endswith('.csv'):
            df.to_csv(args.output, index=False)
        else:
            try:
                df.to_excel(args.output, index=False)
            except ImportError:
                args.output = args.output.replace('.xlsx', '.csv')
                df.to_csv(args.output, index=False)
    
    # Summary
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    
    df_results = pd.DataFrame(results)
    total = len(results)
    success = df_results['Success'].sum()
    rate = (success / total * 100) if total > 0 else 0
    avg = df_results['Attempts'].mean() if total > 0 else 0
    
    print(f"Total: {total}")
    print(f"Success: {success}/{total} ({rate:.1f}%)")
    print(f"Avg Attempts: {avg:.2f}")
    print(f"Results: {args.output}")
    print("=" * 70)
    
    # Save summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total': total,
        'successful': int(success),
        'success_rate': float(rate),
        'average_attempts': float(avg),
    }
    
    summary_file = RESULTS_DIR / 'benchmark_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
