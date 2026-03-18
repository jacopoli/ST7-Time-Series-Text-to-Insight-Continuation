# 🚀 Quick Start - Benchmark Visualization

## Installation (1 minute)

```bash
# Install dependencies
pip install pandas numpy matplotlib langchain-openai
pip install openpyxl  # Optional, for Excel output
```

## Run Benchmark (Pick One)

### **Fastest** (~1 min)

```bash
# Test just 1 scenario to verify setup
python benchmark_visualization.py --limit 1
```

### **Quick Test** (~2-3 min)

```bash
# Test first 5 scenarios
python benchmark_visualization.py --limit 5
```

### **Standard** (~10-15 min)

```bash
# Run all 20 scenarios
python benchmark_visualization.py
```

### **Interactive Menu**

```bash
# Choose what to run
python run_benchmark.py
```

## Check Results

After running, look for:

```
benchmarks/viz_results/
├── benchmark_summary.json          ← Summary stats
└── visualization_benchmark_results.xlsx  ← Full report
reports/*.png                           ← Generated charts
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
