"""Simple test script for analysis agent."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from agents.analysis_agent_implem import create_analysis_agent
from utils.states import AnalysisState
from utils.llm_judge import llm_from
from utils.datastore import DataStore, store_df


def test_analysis(instruction: str, df: pd.DataFrame):
    """
    Simple test function: just pass an instruction and DataFrame.
    The agent will automatically choose between forecast and anomaly detection.
    
    Args:
        instruction: What you want the agent to do
        df: DataFrame with 'timestamp' and 'value' columns
    """
    print(f"\n{'='*60}")
    print(f"Instruction: {instruction}")
    print(f"DataFrame shape: {df.shape}")
    print(f"{'='*60}\n")
    
    # Initialize the LLM
    llm = llm_from(agent_name="Analysis Agent")
    
    # Create the analysis agent
    analysis_agent = create_analysis_agent(llm)

    # Create state with instruction and datastore containing the df
    state: AnalysisState = {
        "instruction": instruction,
        "datastore": {
            "timeseries_data": {
                "description": "Time series data for analysis",
                "datastore_ref": None,
                "data": df.to_dict('records')
            }
        },
        "datastore_obj": None,
    }

    # Run the agent
    result = analysis_agent.invoke(state)
    
    # Print results
    print(f"Final Answer:\n{result.get('analysis_agent_final_answer')}\n")
    print(f"Insights: {result.get('insights')}\n")
    print(f"Follow-up Questions: {result.get('follow_up_questions')}\n")
    if result.get('error_message'):
        print(f"Error: {result.get('error_message')}\n")
    
    return result


def create_sample_timeseries(n_points=100):
    """Generate sample time series data with trend and noise."""
    dates = [datetime.now() - timedelta(hours=i) for i in range(n_points)]
    dates.reverse()
    
    trend = np.linspace(20, 25, n_points)
    noise = np.random.normal(0, 1, n_points)
    values = trend + noise
    # Add anomalies
    values[50] = 50
    values[75] = 5
    
    return pd.DataFrame({
        'timestamp': dates,
        'value': values
    })


if __name__ == "__main__":
    # Create sample data once
    df = create_sample_timeseries(100)
    
    # Test 1: Forecast
    test_analysis("Forecast the next values in this time series", df)
    
    # Test 2: Anomaly detection
    test_analysis("Detect anomalies in this time series", df)
