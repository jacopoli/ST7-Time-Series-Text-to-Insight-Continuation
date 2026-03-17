# Visualization Agent Benchmark

## Overview

`benchmark_visualization.py` is a comprehensive testing script for the **Visualization Agent**, following the same structure and conventions as the SQL Agent benchmark. It measures the agent's ability to generate and execute visualization code based on natural language instructions.

## Features

### 1. **Test Scenarios (20 in total)**

Organized by difficulty level:

- **Simple (3)**: Basic charts (line, bar, scatter)
- **Intermediate (7)**: Multi-metric, subplots, heatmaps, distributions
- **Complex (10)**: Edge cases, missing data, multi-axis, dashboards

### 2. **Metrics Captured**

| Metric              | Type          | Description                                                            |
| ------------------- | ------------- | ---------------------------------------------------------------------- |
| `execution_success` | Boolean       | Did the generated Python code execute successfully?                    |
| `llm_calls_count`   | Integer       | Number of LLM attempts/retries (from `visualization_codegen_attempts`) |
| `readability_score` | Integer (1-5) | **[Placeholder]** Code clarity, proper labels, legends, titles         |
| `coherence_score`   | Integer (1-5) | **[Placeholder]** Alignment between user request and generated chart   |
| `error_message`     | String        | Error details if execution failed                                      |
| `output_paths`      | List          | Paths to generated visualization files                                 |
| `warnings`          | List          | Non-critical warnings during execution                                 |

### 3. **Test Data**

The benchmark generates 8 synthetic datasets:

- **simple_ts**: Time series with 100 days of data
- **multi_ts**: Multiple sensors over time
- **categorical**: Categories with timestamps
- **wide_metrics**: Multiple metrics in wide format
- **with_nan**: Data with missing values (NaN handling)
- **multi_site**: Multi-site temperature data
- **measurements**: High-frequency channel readings
- **statistics**: Aggregated min/mean/max statistics

### 4. **Output Structure**

```
benchmarks/viz_results/
├── benchmark_summary.json          # Summary statistics
├── visualization_benchmark_results.xlsx  # Detailed results (Excel)
└── [generated visualizations]      # PNG files from test scenarios
```

## Usage

### Basic Run (All Scenarios)

```bash
python benchmark_visualization.py
```

### With Options

```bash
# Run only first 5 scenarios
python benchmark_visualization.py --limit 5

# Start from scenario 10
python benchmark_visualization.py --start 10

# Custom output file
python benchmark_visualization.py --output my_results.xlsx

# Custom visualization output directory
python benchmark_visualization.py --output-dir /path/to/viz_output
```

### Full Example

```bash
python benchmark_visualization.py \
  --limit 20 \
  --output visualization_benchmark_full.xlsx \
  --output-dir ./benchmarks/visualization_results
```

## Output Files

### 1. **Excel Report** (`visualization_benchmark_results.xlsx`)

Columns:

- Scenario ID, Difficulty, Question
- Expected Chart Type, Description
- Datasets Used
- **Execution Success** (✓/✗)
- **LLM Attempts** (count)
- **Readability & Coherence Scores** (1-5 scale for review)
- **Average Quality Score** (auto-calculated)
- Error Message (if failed)
- Output Paths (generated PNG files)
- Warnings Count

### 2. **Summary JSON** (`benchmarks/viz_results/benchmark_summary.json`)

```json
{
  "timestamp": "2024-03-17T15:30:45.123456",
  "total_scenarios": 20,
  "successful_scenarios": 18,
  "success_rate": 90.0,
  "average_attempts": 1.5,
  "by_difficulty": {
    "simple": {
      "count": 3,
      "success_rate": 100.0
    },
    "intermediate": {
      "count": 7,
      "success_rate": 85.7
    },
    "complex": {
      "count": 10,
      "success_rate": 90.0
    }
  }
}
```

## Implementation Details

### Architecture

The benchmark follows the same structure as `test_benchmark_sql.py`:

1. **Load scenarios** from code or JSON
2. **Generate test data** (synthetic DataFrames)
3. **For each scenario**:
   - Create a DataStore with test dataframes
   - Initialize VisualizationState
   - Invoke the compiled visualization graph
   - Capture metrics (success, attempts, outputs)
   - Save results incrementally

### Execution Flow

```
Load Scenarios
    ↓
Generate Test Data
    ↓
For each scenario:
    ├─ Create DataStore
    ├─ Invoke visualization graph
    │   ├─ load_context_node: Prepare data
    │   ├─ generate_code_node: LLM generates code
    │   └─ execute_code_node: Execute code safely
    ├─ Extract metrics
    ├─ Save results
    └─ Report progress
    ↓
Generate Summary
```

### Key Design Decisions

1. **Direct DataStore Injection**: Unlike SQL benchmark that queries DB, visualization receives prepared DataFrames
2. **Isolated Execution**: Each scenario gets fresh DataStore to prevent state pollution
3. **Safety Sandbox**: Code execution is restricted (no imports, limited file I/O)
4. **Incremental Saving**: Results saved after each scenario (crash-safe)
5. **Placeholder Scores**: Readability and coherence scores are 0 (reserved for human review tools)

## Extensibility

### Adding New Scenarios

Edit `create_benchmark_scenarios()` in `benchmark_visualization.py` or add to `benchmark_visualization.json`:

```python
{
    'id': 'viz_XXX',
    'difficulty': 'intermediate',
    'question': 'Your visualization request here',
    'expected_chart_type': 'line|bar|heatmap|etc',
    'description': 'Short description',
    'dataframes': ['key1', 'key2'],  # from generate_test_dataframes()
}
```

### Adding New Test Datasets

Modify `generate_test_dataframes()` to create additional DataFrame fixtures:

```python
df_custom = pd.DataFrame({
    'time': pd.date_range('2024-01-01', periods=100),
    'value': np.random.randn(100),
})
```

### Custom Metrics

Extend `run_visualization_benchmark()` to compute additional metrics:

```python
# Example: Count plot elements
num_subplots = final_state.get('visualization_code', '').count('plt.subplot')
```

## Troubleshooting

### ImportError: langchain_openai

```bash
pip install langchain-openai
```

### ImportError: openpyxl (Excel export)

```bash
pip install openpyxl
# Falls back to CSV if not available
```

### OOM or Timeout

```bash
# Reduce number of scenarios
python benchmark_visualization.py --limit 5
```

### LLM Rate Limits

The benchmark respects your configured LLM limits. If you hit rate limits, add delays:

```python
import time
time.sleep(1)  # Add before run_visualization_benchmark()
```

## Interpreting Results

### Success Rate

- **Simple (100% expected)**: Basic charts should always work
- **Intermediate (80-95%)**: Some complexity, minor failures acceptable
- **Complex (70-90%)**: Multiple retries may occur

### LLM Attempts

- **1.0 = Perfect**: Code generated correctly on first try
- **1.5-2.0 = Good**: 1-2 retry attempts needed
- **>2.0 = Concerning**: Excessive retries indicate generation issues

### Quality Scores (Manual Review)

After running, open the Excel file and manually score:

- **Readability (1-5)**:
  - 5: Clear labels, legend, title, axis labels
  - 1: Barely readable, missing labels
- **Coherence (1-5)**:
  - 5: Perfect match to user request
  - 1: Doesn't match request at all

## Production Considerations

### Performance

- **Runtime**: ~2-5 min for 20 scenarios (depends on LLM latency)
- **Memory**: ~500MB for test data + LLM context
- **Storage**: ~1-2MB per benchmark run (Excel + JSON + PNGs)

### CI/CD Integration

```bash
#!/bin/bash
python benchmark_visualization.py --limit 5 --output ci_results.xlsx
if grep -q "false" ci_results.xlsx; then
  echo "Benchmark failures detected!"
  exit 1
fi
```

## Comparison with SQL Benchmark

| Aspect  | SQL Benchmark           | Visualization Benchmark  |
| ------- | ----------------------- | ------------------------ |
| Input   | Natural language query  | Visualization request    |
| Output  | SQL query + results     | Python code + chart      |
| Storage | Database                | DataStore                |
| Metrics | SQL correctness         | Code execution success   |
| Retries | SQL generation attempts | Code generation attempts |

---

**Last Updated**: March 2024  
**Related Files**: `benchmark_sql.py`, `agents/visualization_agent.py`, `utils/datastore.py`
