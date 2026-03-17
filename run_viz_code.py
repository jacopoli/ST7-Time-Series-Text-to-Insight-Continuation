#!/usr/bin/env python
"""
Wrapper to run generated visualization code with proper environment.
Provides all required functions (list_datasets, get_df, save_figure, etc.)
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils.datastore import DATASTORE, DataStore


def create_execution_environment():
    """
    Create the environment variables needed to run generated visualization code.
    Returns a dict with all inject functions.
    """
    
    # Get datastore
    datastore_obj = DATASTORE
    datastore_frames = {}
    datastore_snapshot = datastore_obj.snapshot()
    
    # For all datasets in datastore, also load the actual frames
    for key in datastore_snapshot.keys():
        try:
            datastore_frames[key] = datastore_obj.get_df(key)
        except Exception:
            pass
    
    # Also try to load datasets from benchmarks/viz_results/test_data/
    test_data_dir = Path('benchmarks/viz_results/test_data')
    if test_data_dir.exists():
        for csv_file in sorted(test_data_dir.glob('*.csv')):
            key = csv_file.stem
            try:
                df = pd.read_csv(csv_file)
                # Try to parse datetime columns
                for col in df.columns:
                    if any(hint in col.lower() for hint in ['time', 'timestamp', 'date', 'datetime', 'ts']):
                        try:
                            df[col] = pd.to_datetime(df[col])
                        except Exception:
                            pass
                datastore_frames[key] = df
                datastore_snapshot[key] = {
                    'description': f'Test dataset: {key}',
                    'row_count': len(df),
                    'columns': list(df.columns),
                    'datastore_ref': key,
                }
            except Exception as e:
                print(f"Warning: Could not load {key}: {e}")
    
    # Create reports directory
    reports_dir = Path("reports")
    warnings = []
    outputs = []
    
    # Define all injected functions
    
    def list_datasets():
        """List available dataset keys."""
        keys = list(datastore_snapshot.keys())
        if not keys and datastore_frames:
            keys = list(datastore_frames.keys())
        return keys
    
    def get_df(key: str) -> pd.DataFrame:
        """Get a dataframe by key."""
        if key in datastore_frames:
            return datastore_frames[key].copy()
        return datastore_obj.get_df(key)
    
    def get_all_dfs() -> dict:
        """Get all dataframes."""
        return {key: get_df(key) for key in list_datasets()}
    
    def dataset_meta(key: str) -> dict:
        """Get metadata for a dataset."""
        payload = datastore_snapshot.get(key, {})
        return dict(payload) if isinstance(payload, dict) else {}
    
    def warn(message: str) -> None:
        """Add a warning."""
        if message:
            warnings.append(str(message))
    
    def inspect_dataset(key: str) -> dict:
        """Inspect a dataset."""
        df = get_df(key)
        columns = [str(col) for col in df.columns]
        dtypes = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
        
        time_columns = []
        numeric_columns = []
        categorical_columns = []
        
        TIME_HINTS = ("time", "timestamp", "date", "datetime", "ts")
        for col in df.columns:
            name = str(col).lower()
            series = df[col]
            if pd.api.types.is_datetime64_any_dtype(series) or any(hint in name for hint in TIME_HINTS):
                time_columns.append(str(col))
                continue
            if pd.api.types.is_numeric_dtype(series):
                numeric_columns.append(str(col))
            else:
                categorical_columns.append(str(col))
        
        return {
            "key": key,
            "row_count": len(df),
            "columns": columns,
            "dtypes": dtypes,
            "time_columns": time_columns,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
        }
    
    def inspect_inputs(max_datasets=None):
        """Inspect all inputs."""
        keys = list_datasets()
        if isinstance(max_datasets, int) and max_datasets > 0:
            keys = keys[:max_datasets]
        return [inspect_dataset(key) for key in keys]
    
    def register_output(path: str, summary: str = None, meta: dict = None) -> None:
        """Register an output."""
        outputs.append({
            "chart_path": str(path),
            "summary": summary or "",
            "meta": meta or {},
        })
    
    def save_figure(fig, filename: str = None, summary: str = None, meta: dict = None) -> str:
        """Save a figure to reports directory."""
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        file_name = filename or f"visualization-{len(outputs) + 1}.png"
        path = Path(file_name)
        suffix = path.suffix or ".png"
        base = path.stem or "visualization"
        output_path = reports_dir / f"{base}{suffix}"
        
        fig.savefig(str(output_path), dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        register_output(str(output_path), summary=summary, meta=meta)
        return str(output_path)
    
    def make_subplots(rows: int, cols: int, **kwargs):
        """Create subplots."""
        fig, axes = plt.subplots(rows, cols, **kwargs)
        return fig, axes
    
    # Return execution environment
    return {
        'list_datasets': list_datasets,
        'get_df': get_df,
        'get_all_dfs': get_all_dfs,
        'dataset_meta': dataset_meta,
        'warn': warn,
        'inspect_dataset': inspect_dataset,
        'inspect_inputs': inspect_inputs,
        'register_output': register_output,
        'save_figure': save_figure,
        'make_subplots': make_subplots,
        # Standard imports
        'pd': pd,
        'np': np,
        'plt': plt,
        'Path': Path,
        'pd': pd,
    }


def run_visualization_code(code_file: Path) -> dict:
    """
    Run a visualization code file with proper environment.
    Returns execution result.
    """
    
    print(f"\n{'='*70}")
    print(f"Running: {code_file.name}")
    print(f"{'='*70}\n")
    
    # Create execution environment
    env = create_execution_environment()
    
    # Read code file
    try:
        with open(code_file, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return {'success': False, 'error': str(e)}
    
    # Execute code
    try:
        # Merge env with builtins for proper execution context
        exec_globals = {'__builtins__': __builtins__, **env}
        exec(code, exec_globals)
        print(f"\n✓ Successfully executed {code_file.name}")
        return {
            'success': True,
            'error': None,
            'outputs': exec_globals.get('result', {}),
        }
    except Exception as e:
        print(f"\n✗ Error executing code: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python run_viz_code.py <viz_file.py>")
        print("\nExample:")
        print("  python run_viz_code.py benchmarks/viz_results/generated_code/viz_001.py")
        return 1
    
    code_file = Path(sys.argv[1])
    
    if not code_file.exists():
        print(f"Error: File not found: {code_file}")
        return 1
    
    result = run_visualization_code(code_file)
    
    if result['success']:
        print("\n" + "="*70)
        print("EXECUTION SUCCESSFUL")
        print("="*70)
        outputs = result.get('outputs', {})
        if outputs:
            print("\nOutput:")
            print(f"  Summary: {outputs.get('summary', 'N/A')}")
            print(f"  Status: {outputs.get('status', 'N/A')}")
            paths = outputs.get('output_paths', [])
            if paths:
                print(f"  Generated files:")
                for path in paths:
                    print(f"    - {path}")
        return 0
    else:
        print("\n" + "="*70)
        print("EXECUTION FAILED")
        print("="*70)
        print(f"\nError: {result.get('error', 'Unknown error')}")
        if 'traceback' in result:
            print("\nFull traceback:")
            print(result['traceback'])
        return 1


if __name__ == "__main__":
    sys.exit(main())
