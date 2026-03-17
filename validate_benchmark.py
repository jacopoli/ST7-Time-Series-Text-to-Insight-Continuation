#!/usr/bin/env python3
"""
Validation script for Benchmark Visualization implementation.
Checks that all required files exist and have correct structure.
"""

import sys
from pathlib import Path
import json

# Define required files
REQUIRED_FILES = {
    'benchmark_visualization.py': {
        'type': 'python_script',
        'min_size': 10000,  # Bytes
        'must_contain': ['run_visualization_benchmark', 'create_benchmark_scenarios', 'generate_test_dataframes']
    },
    'benchmark_visualization.json': {
        'type': 'json',
        'min_size': 1000,
        'structure': ['benchmark_scenarios']
    },
    'BENCHMARK_VISUALIZATION_README.md': {
        'type': 'markdown',
        'min_size': 5000,
        'must_contain': ['Usage', 'Metrics', 'Output']
    },
    'IMPLEMENTATION_SUMMARY.md': {
        'type': 'markdown',
        'min_size': 3000,
        'must_contain': ['Architecture', 'Metrics', 'Test Datasets']
    },
    'QUICK_START.md': {
        'type': 'markdown',
        'min_size': 1000,
        'must_contain': ['Installation', 'Run Benchmark']
    },
    'run_benchmark.py': {
        'type': 'python_script',
        'min_size': 2000,
        'must_contain': ['run_benchmark', 'menu']
    },
}


def validate_file(file_path, config):
    """Validate a single file."""
    results = []
    
    # Check existence
    if not file_path.exists():
        return [f"❌ MISSING: {file_path.name}"]
    results.append(f"✅ EXISTS: {file_path.name}")
    
    # Check size
    size = file_path.stat().st_size
    if size < config['min_size']:
        results.append(f"   ⚠️  Small size: {size} bytes (expected >{config['min_size']})")
    else:
        results.append(f"   ✅ Size OK: {size} bytes")
    
    # Read content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        results.append(f"   ❌ Cannot read: {e}")
        return results
    
    # Check for required strings (Python)
    if config['type'] == 'python_script' and 'must_contain' in config:
        for required in config['must_contain']:
            if required in content:
                results.append(f"   ✅ Contains '{required}'")
            else:
                results.append(f"   ❌ Missing '{required}'")
    
    # Check for required strings (Markdown)
    if config['type'] == 'markdown' and 'must_contain' in config:
        for required in config['must_contain']:
            if required in content:
                results.append(f"   ✅ Contains '{required}'")
            else:
                results.append(f"   ❌ Missing '{required}'")
    
    # Check JSON structure
    if config['type'] == 'json':
        try:
            data = json.loads(content)
            for key in config['structure']:
                if key in data:
                    if isinstance(data[key], list):
                        results.append(f"   ✅ JSON key '{key}' contains {len(data[key])} items")
                    else:
                        results.append(f"   ✅ JSON key '{key}' exists")
                else:
                    results.append(f"   ❌ JSON key '{key}' missing")
        except json.JSONDecodeError as e:
            results.append(f"   ❌ Invalid JSON: {e}")
    
    return results


def main():
    """Run validation."""
    base_path = Path(__file__).parent
    
    print("\n" + "=" * 70)
    print("BENCHMARK VISUALIZATION - VALIDATION CHECK")
    print("=" * 70 + "\n")
    
    all_results = {}
    has_errors = False
    
    for filename, config in REQUIRED_FILES.items():
        file_path = base_path / filename
        results = validate_file(file_path, config)
        all_results[filename] = results
        
        for result in results:
            print(result)
            if "❌" in result or "⚠️" in result:
                has_errors = True
        print()
    
    # Summary
    print("=" * 70)
    total_checks = sum(len(results) for results in all_results.values())
    failed_checks = sum(len([r for r in results if "❌" in r]) for results in all_results.values())
    
    if failed_checks == 0:
        print("✅ ALL VALIDATION CHECKS PASSED")
        print(f"\nFiles: {len(REQUIRED_FILES)}")
        print(f"Total checks: {total_checks}")
        print("\nReady to run: python benchmark_visualization.py")
    else:
        print(f"❌ VALIDATION FAILED: {failed_checks} critical errors")
        print(f"\nFiles: {len(REQUIRED_FILES)}")
        print(f"Total checks: {total_checks}")
        print(f"Failed: {failed_checks}")
    
    print("=" * 70 + "\n")
    
    return 0 if failed_checks == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
