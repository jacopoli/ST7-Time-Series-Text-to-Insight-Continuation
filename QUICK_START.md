# 🚀 Quick Start - Benchmark Visualization

## Installation (1 minute)

```bash
# Install dependencies
pip install pandas numpy matplotlib langchain-openai
pip install openpyxl  # Optional, for Excel output
```

## Run Benchmark (Pick One)

### 🟢 **Fastest** (~1 min)

```bash
# Test just 1 scenario to verify setup
python benchmark_visualization.py --limit 1
```

### 🟡 **Quick Test** (~2-3 min)

```bash
# Test first 5 scenarios
python benchmark_visualization.py --limit 5
```

### 🔵 **Standard** (~10-15 min)

```bash
# Run all 20 scenarios
python benchmark_visualization.py
```

### 🟣 **Interactive Menu**

```bash
# Choose what to run
python run_benchmark.py
```

## Check Results

After running, look for:

```
benchmarks/viz_results/
├── benchmark_summary.json          ← Summary stats
├── visualization_benchmark_results.xlsx  ← Full report
└── *.png                           ← Generated charts
```

## Key Files Reference

| File                                | Purpose               |
| ----------------------------------- | --------------------- |
| `benchmark_visualization.py`        | Main benchmark script |
| `benchmark_visualization.json`      | 20 test scenarios     |
| `run_benchmark.py`                  | Interactive menu      |
| `BENCHMARK_VISUALIZATION_README.md` | Full documentation    |
| `IMPLEMENTATION_SUMMARY.md`         | Technical overview    |

## Common Commands

```bash
# Run 10 scenarios with custom output
python benchmark_visualization.py --limit 10 --output my_results.xlsx

# Continue from scenario 15
python benchmark_visualization.py --start 15

# Simple scenarios only (3 tests, ~1 min)
python benchmark_visualization.py --limit 3
```

## What Gets Tested?

✅ **20 Visualization Scenarios**

- 3 Simple (line, bar, scatter)
- 7 Intermediate (multi-metric, heatmaps, subplots)
- 10 Complex (NaN handling, dual-axis, dashboards)

✅ **8 Synthetic Datasets**

- Time series, multi-sensor, categorical, wide-format, sparse data, multi-site, etc.

✅ **Metrics Captured**

- execution_success (did it run?)
- llm_calls_count (how many retries?)
- error_message (what went wrong?)
- output_paths (where are the charts?)

## Expected Results

```
Typical success rates:
- Simple:       100% ✓
- Intermediate: 80-95% ✓
- Complex:      70-90% ✓
```

## Troubleshooting

**ImportError: langchain_openai**
→ `pip install langchain-openai`

**ImportError: openpyxl**  
→ Will auto-fall back to CSV

**LLM not configured**
→ Set `OPENAI_API_KEY` environment variable

**Out of memory**
→ Use `--limit 5` to test fewer scenarios

## Next: Read Full Docs

For detailed information, see:

- `BENCHMARK_VISUALIZATION_README.md` - Complete guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details

---

**That's it!** Run the benchmark and check the results. 🎉
