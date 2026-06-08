"""
Benchmark test script for the analysis agent.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from agents.analysis_agent_implem import create_analysis_agent
from utils.states import AnalysisState
from utils.llm_judge import llm_from
from utils.datastore import DATASTORE
from utils.sql_utils import connect_postgres, execute_sql_tool


def convert_excel_to_csv(excel_path: str) -> str:
    """
    Convert Excel file to CSV format.
    """
    try:
        csv_path = excel_path.replace('.xlsx', '.csv').replace('.xls', '.csv')
        df = pd.read_excel(excel_path)
        df.to_csv(csv_path, index=False)
        print(f"[OK] Converted {excel_path} to {csv_path}")
        return csv_path
    except Exception as e:
        print(f"[ERROR] Failed to convert Excel to CSV: {str(e)}")
        return None


def load_benchmark_data_from_db(csv_path: str = None) -> pd.DataFrame:
    """
    Load time series data from a CSV file.
    """
    if csv_path:
        try:
            df = pd.read_csv(csv_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna(subset=['value']).reset_index(drop=True)
            print(f"[OK] Loaded {len(df)} data points from CSV: {csv_path}")
            return df
        except Exception as e:
            print(f"[WARN] Could not load from CSV: {str(e)}, using synthetic data")
            return create_realistic_timeseries(200)
    else:
        print(f"[WARN] No CSV path provided, using synthetic data")
        return create_realistic_timeseries(200)


def create_realistic_timeseries(n_points=200, trend=False, seasonality=True, noise=True, anomalies=True):
    """
    Generate realistic time series data with multiple components.
    
    Args:
        n_points: Number of data points
        trend: Add upward trend if True
        seasonality: Add seasonal pattern if True
        noise: Add random noise if True
        anomalies: Add anomalous points if True
    
    Returns:
        DataFrame with 'timestamp' and 'value' columns
    """
    dates = [datetime.now() - timedelta(hours=i) for i in range(n_points)]
    dates.reverse()
    
    base = np.linspace(20, 30, n_points) if trend else np.full(n_points, 25)
    
    if seasonality:
        seasonal = 5 * np.sin(np.linspace(0, 4*np.pi, n_points))
    else:
        seasonal = np.zeros(n_points)
    
    if noise:
        random_noise = np.random.normal(0, 1.5, n_points)
    else:
        random_noise = np.zeros(n_points)
    
    values = base + seasonal + random_noise
    
    if anomalies:
        values[30] = 55      # Spike
        values[100] = 5      # Dip
        values[150:152] = 45 # Sustained anomaly
    
    return pd.DataFrame({
        'timestamp': dates,
        'value': values
    })


def run_benchmark_test(test_name: str, instruction: str, df: pd.DataFrame):
    """
    Run a single benchmark test.
    """
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)
    print(f"Instruction: {instruction}")
    print(f"Data shape: {df.shape}")
    print("-"*80)
    
    try:
        llm = llm_from(agent_name="Analysis Agent")
        
        analysis_agent = create_analysis_agent(llm)

        ref = DATASTORE.put(df, description="Benchmark time series data", namespace="benchmark")
        
        state: AnalysisState = {
            "instruction": instruction,
            "datastore": {
                ref: {"description": "Benchmark time series data"}
            },
            "datastore_obj": None,
        }

        result = analysis_agent.invoke(state)
        
        # Print results
        print(f"\n[RESULT] FINAL ANSWER:\n{result.get('analysis_agent_final_answer')}\n")
        
        if result.get('error_message'):
            print(f"\n[WARN] WARNING: {result.get('error_message')}\n")
        
        return result
        
    except Exception as e:
        print(f"\n ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None



def main():
    """Run all benchmark tests."""
    
    DATA_FILE = None#"C:/Users/charl/OneDrive/Documents/db_benchmark.xlsx"
    
    print("\n" + "="*80)
    print("ANALYSIS AGENT BENCHMARK TESTS")
    print("="*80)
    print("Testing time series analysis capabilities:\n")
    print("1. Forecast all the data")
    print("2. Detect anomaly within the data")
    print("3. Forecast and detect anomaly within the data")
    print("4. Compute the first 4 moments of the data")
    print("="*80)
    
    # Load data from file (convert Excel to CSV if needed)
    print("\n[DATA] Loading benchmark dataset...")
    csv_path = "C:/Users/charl/OneDrive/Documents/db_benchmark.xlsx"
    
    if DATA_FILE and DATA_FILE.endswith(('.xlsx', '.xls')):
        print(f"Detected Excel file, converting to CSV...")
        csv_path = convert_excel_to_csv(DATA_FILE)
        
    df = load_benchmark_data_from_db(csv_path=csv_path)
    
    print(f"[OK] Dataset loaded: {df.shape[0]} points")
    print(f"Spanning from {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    results = {}
    
    # Test 1
    results['forecast'] = run_benchmark_test(
        test_name="1. FORECAST ALL THE DATA WITHIN THE DATA of variable 255806",
        instruction="Forecast the next 50 values in this time series. What are the predicted values?",
        df=df
    )
    
    # Test 2
    results['anomaly'] = run_benchmark_test(
        test_name="2. DETECT ANOMALY WITHIN THE DATA of variable 255806",
        instruction="Detect anomalies in this time series. What are the anomalous points?",
        df=df
    )
    
    # Test 3
    results['combined'] = run_benchmark_test(
        test_name="3. FORECAST AND DETECT ANOMALY of the data of variable 255806",
        instruction="First detect anomalies in this time series, then forecast the next values. Provide both analysis.",
        df=df
    )
    
    # Test 4
    results['moments'] = run_benchmark_test(
        test_name="4. COMPUTE THE FIRST 4 MOMENTS of the data of variable 255806",
        instruction="Compute the first 4 moments of this data.",
        df=df
    )
    
    # Test 5
    results['predict'] = run_benchmark_test(
        test_name="5. Predict the next values of the series.",
        instruction="Predict the next values of the series.",
        df=df
    )
    
    # Test 6
    results['anomalies'] = run_benchmark_test(
        test_name="6. Find abnormal points in the data.",
        instruction="Find abnormal points in the data.",
        df=df
    )
    
    # Test 7
    results['unusual'] = run_benchmark_test(
        test_name="7. Can you tell me if some points look unusual?",
        instruction="Can you tell me if some points look unusual?",
        df=df
    )

    # Test 8
    results['highlight'] = run_benchmark_test(
        test_name="8. Highlight the outliers in the time series.",
        instruction="Highlight the outliers in the time series.",
        df=df
    )
    
    # Test 9
    results['give me'] = run_benchmark_test(
        test_name="9. Give me a prediction and check if the past data contains abnormal values.",
        instruction="Give me a prediction and check if the past data contains abnormal values.",
        df=df
    )
    
    #Test 10
    results['autocorrelation'] = run_benchmark_test(
        test_name="10. Plot the autocorrelation function of the series.",
        instruction="Plot the autocorrelation function of the series.",
        df=df
    )
    
    # Test 11 
    results['increase'] = run_benchmark_test(
        test_name="11. Tell me whether the next 100 values will increase or decrease.",
        instruction="Tell me whether the next 100 values will increase or decrease.",
        df=df
    )
    
    # Test 12
    results['every'] = run_benchmark_test(
        test_name="12. Run every available analysis tool on this dataset.",
        instruction="Run every available analysis tool on this dataset.",
        df=df
    )
    
    # Test 13
    results['everything'] = run_benchmark_test(
        test_name="13. Run everything you can on this dataset.",
        instruction="Run everything you can on this dataset.",
        df=df
    )
    
    # Test 14
    results['Fourier'] = run_benchmark_test(
        test_name="14. Compute the Fourier transform of the signal.",
        instruction="Compute the Fourier transform of the signal.",
        df=df
    )
    
    # Test 15
    results['nega1'] = run_benchmark_test(
        test_name="15. I don’t want anomaly detection, just forecast the series.",
        instruction="I don’t want anomaly detection, just forecast the series.",
        df=df
    )
    
    # Test 16
    results['nega2'] = run_benchmark_test(
        test_name="16. I don’t want forecasting, just detect anomalies in the series.",
        instruction="I don’t want forecasting, just detect anomalies in the series.",
        df=df
    )
    
    # Test 17
    results['non et oui'] = run_benchmark_test(
        test_name="17. Remove noise and forecast the signal.",
        instruction="Remove noise and forecast the signal.",
        df=df
    )
    
if __name__ == "__main__":
    main()
