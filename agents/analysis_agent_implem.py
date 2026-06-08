from __future__ import annotations
from typing import Any, Dict
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from pydantic import BaseModel, Field
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import START, END, StateGraph

# Add necessary imports for agent
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from utils.datastore import load_df, DataStore
from utils.output_basemodels import AnalysisAgentOutput
from utils.states import AnalysisDatastore, AnalysisState

DEFAULT_DATASTORE_MESSAGE = "No datastore entries are available for analysis."
Datastore = AnalysisDatastore


# Process du df d'entrée
def prepare_df(
    df: pd.DataFrame,
    col_valeur: str = "value",
    col_temps: str = "timestamp",
) -> pd.DataFrame:
    if col_temps not in df.columns or col_valeur not in df.columns:
        raise ValueError(f"Les colonnes '{col_temps}' et '{col_valeur}' doivent être présentes dans le DataFrame.")
    
    df_local = df.copy()
    df_local[col_temps] = pd.to_datetime(df_local[col_temps])
    df_local = df_local.sort_values(col_temps)
    df_local = df_local.dropna(subset=[col_valeur]).reset_index(drop=True)
    return df_local

# Forecast :

def differenciation(df: pd.Series) -> int:
    d = 0
    resultat = adfuller(df.dropna())
    print('p-value :', resultat[1])
    if resultat[1] > 0.05:
        df_diff = df.diff().dropna()
        print('p-value après différenciation :', adfuller(df_diff)[1])
        d += 1
        if adfuller(df_diff.dropna())[1] > 0.05:
            df_diff2 = df_diff.diff().dropna()
            print('p-value après différenciation 2 :', adfuller(df_diff2)[1])
            d += 1
    return d

def choix_p_q(entrainement, test, p_range, q_range, diff):
    best_rmse = np.inf
    best_order = None

    for p in range(p_range+1):
        for q in range(q_range+1):
            print(p, q)
            try:
                model = ARIMA(entrainement, order=(p, diff, q))
                result = model.fit()
                forecast = result.forecast(steps=len(test))
                rmse = np.sqrt(np.mean((forecast - test) ** 2))

                if rmse < best_rmse:
                    best_rmse = rmse
                    best_order = (p, diff, q)
            except Exception:
                continue
    print(best_order)
    return best_order


# TRAITER LONG_FORECAST AVEC LE STATE
def forecast_ARIMA(
    df: pd.DataFrame,
    col_valeur: str = "value",
    col_temps: str = "timestamp",
    train_ratio: float = 0.8,
    max_p: int = 3,
    max_q: int = 3,
    long_forecast: int = 100,
) -> dict:

    local_df = prepare_df(
        df,
        col_valeur=col_valeur,
        col_temps=col_temps,
    )

    y = local_df[col_valeur]

    if len(y) < 10:
        raise ValueError("Pas assez de points dans la série temporelle pour un forecasting fiable.")

    train_size = int(len(y) * train_ratio)
    training = y.iloc[:train_size]
    test = y.iloc[train_size:]

    if len(test) == 0:
        raise ValueError("Le test set est vide. Diminue train_ratio.")

    # On choisit d sur l'entraînement seulement pour éviter de regarder le futur
    d = differenciation(training)

    param_ARIMA = choix_p_q(
        entrainement=training,
        test=test,
        p_range=max_p,
        q_range=max_q,
        diff=d,
    )

    history = training.copy()
    predictions = []

    for idx, true_value in test.items():
        model = ARIMA(history, order=param_ARIMA)
        fitted = model.fit()

        # Prévision d'un seul point
        y_pred = fitted.forecast(steps=1)

        # format selon si statsmodels renvoie Series ou array
        if hasattr(y_pred, "iloc"):
            y_pred_value = y_pred.iloc[0]
        else:
            y_pred_value = y_pred[0]

        predictions.append(float(y_pred_value))

        # On ajoute la vraie valeur observée avant de prédire le point suivant
        new_obs = pd.Series([true_value], index=[idx])
        history = pd.concat([history, new_obs])

    forecast = pd.Series(predictions, index=test.index)

    # Visualisation
 
    """try:
        fig, ax = plt.subplots(figsize=(12, 6))

        x_axis = np.arange(len(y))

        train_x = np.arange(len(training))
        test_x = np.arange(len(training), len(y))

        ax.plot(train_x, training.values, "b-", label="Training Data", linewidth=2)
        ax.plot(test_x, test.values, "k-", label="Test Data", linewidth=2)
        ax.plot(test_x, forecast.values, "r--", label="One-step-ahead Forecast", linewidth=2)

        # Ligne de séparation train / test
        ax.axvline(x=len(training) - 0.5, color="gray", linestyle="--", alpha=0.5)

        ax.set_xlabel("Time Index", fontsize=12)
        ax.set_ylabel(col_valeur, fontsize=12)
        ax.set_title(
            f"One-step-ahead Forecast (ARIMA{param_ARIMA})",
            fontsize=14,
            fontweight="bold",
        )

        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        Path("reports").mkdir(exist_ok=True)
        plot_path = "reports/forecast_plot.png"
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"Forecast plot saved to {plot_path}")

        try:
            os.startfile(os.path.abspath(plot_path))
        except Exception as e:
            print(f"[WARN] Could not open plot: {e}")

    except Exception as e:
        print(f"[WARN] Could not create forecast plot: {e}")"""

    return {
        "fonctionnalité": "forecast",
        "order": param_ARIMA,
        "forecast_values": [float(x) for x in forecast.tolist()]
    }

def detecter_anomalies(
    df: pd.DataFrame,
    col_valeur: str = "value",
    col_temps: str = "timestamp",
    seuil: float = 3.0,
) -> dict:

    local_df = prepare_df(
        df,
        col_valeur=col_valeur,
        col_temps=col_temps,
    )

    y = local_df[col_valeur]
    mean = y.mean()
    std = y.std()

    if std == 0:
        return {
            "fonctionnalité": "detect_timeseries_anomalies",
            "message": "No anomalies detected (zero standard deviation)",
            "anomalies": [],
        }
    
    z_scores = abs(y - mean) / std
    mask = z_scores.abs() > seuil

    anomalies = local_df[mask].index.tolist()
    
    # Create visualization
    """try:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        timestamps = local_df[col_temps].values
        x_axis = np.arange(len(y))  # Use integer indices for cleaner plot
        
        # Plot all data points
        ax.plot(x_axis, y.values, 'b-', label='Time Series Data', linewidth=2)
        
        # Add mean and std band
        ax.axhline(y=mean, color='green', linestyle='-', linewidth=2, label='Mean', alpha=0.7)
        ax.axhline(y=mean + 3*std, color='orange', linestyle='--', linewidth=2, label='Mean + 3 * Std', alpha=0.7)
        ax.axhline(y=mean - 3*std, color='orange', linestyle='--', linewidth=2, label='Mean - 3 * Std', alpha=0.7)
        
        # Highlight anomalies in red
        if anomalies:
            anomaly_values = y.iloc[anomalies].values
            anomaly_x = np.array(anomalies)
            ax.scatter(anomaly_x, anomaly_values, color='red', s=100, 
                      label=f'Anomalies (threshold={seuil})', zorder=5, marker='o', edgecolors='darkred', linewidth=2)
        
        ax.set_xlabel('Time Index', fontsize=12)
        ax.set_ylabel(col_valeur, fontsize=12)
        ax.set_title('Anomaly Detection - Time Series Analysis', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save figure
        Path("reports").mkdir(exist_ok=True)
        plot_path = "reports/anomaly_detection_plot.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[INFO] Anomaly detection plot saved to {plot_path}")
        
        try:
            os.startfile(os.path.abspath(plot_path))
        except Exception as e:
            print(f"[WARN] Could not open plot: {e}")
    except Exception as e:
        print(f"[WARN] Could not create anomaly detection plot: {e}")"""

    return {
        "fonctionnalité": "detect_timeseries_anomalies",
        "message": f"Anomalies detected at indices: {anomalies}",
        "anomalies": anomalies,
        "z_scores": z_scores[mask].tolist(),
    }

# Helper functions from analysis_agent.py
def _normalize_datastore_input(source: Any) -> AnalysisDatastore:
    if isinstance(source, DataStore):
        return source.snapshot()
    if isinstance(source, dict):
        return dict(source)
    return {}

def _collect_datastore_context(
    state: AnalysisState,
    datastore_loader: Optional[Callable[[], Datastore]],
) -> tuple[Datastore, str, List[str], Optional[str]]:
    raw_datastore = state.get("datastore")
    datastore_obj = state.get("datastore_obj")

    datastore = _normalize_datastore_input(raw_datastore)
    if not datastore and isinstance(datastore_obj, DataStore):
        datastore = datastore_obj.snapshot()

    if not datastore and datastore_loader is not None:
        try:
            loaded = datastore_loader() or {}
            datastore = _normalize_datastore_input(loaded)
        except Exception as exc:
            return {}, "Unable to load datastore snapshot.", [], f"Failed to load datastore: {exc}"

    if not datastore:
        return {}, DEFAULT_DATASTORE_MESSAGE, [], None

    summary = f"Datastore has {len(datastore)} entries."
    return datastore, summary, list(datastore.keys()), None

# Schéma des fonctionnalités pour les outils de sélection du llm

class Forecast_tool(BaseModel):
    col_valeur: str = Field(
        default="value",
        description="Name of the numeric column containing the time series values.",
    )
    col_temps: str = Field(
        default="timestamp",
        description="Name of the timestamp column used to sort the time series.",
    )
    train_ratio: float = Field(
        default=0.8,
        description="Fraction of the series used for training. The rest is forecasted.",
    )
    max_p: int = Field(
        default=3,
        description="Maximum AR order p to test in the ARIMA grid search.",
    )
    max_q: int = Field(
        default=3,
        description="Maximum MA order q to test in the ARIMA grid search.",
    )
    long_forecast: int = Field(
        default=100,
        description="Number of steps to forecast into the future.",
    )


class Anomalie_tool(BaseModel):
    col_valeur: str = Field(
        default="value",
        description="Name of the numeric column containing the time series values.",
    )
    col_temps: str = Field(
        default="timestamp",
        description="Name of the timestamp column used to sort the time series.",
    )
    seuil: float = Field(
        default=3.0,
        description="Z-score threshold above which a point is considered anomalous.",
    )


# Construction des outils d'analyse pour les faire connaitre puis sélectionner par le llm
def analyse_tool(df: pd.DataFrame) -> list[StructuredTool]:
    
    def forecast_serietemp(
        col_valeur: str = "value",
        col_temps: str = "timestamp",
        train_ratio: float = 0.8,
        max_p: int = 3,
        max_q: int = 3,
        long_forecast: int = 100,
    ) -> dict:
        return forecast_ARIMA(
            df=df,
            col_valeur=col_valeur,
            col_temps=col_temps,
            train_ratio=train_ratio,
            max_p=max_p,
            max_q=max_q,
            long_forecast=long_forecast,
        )

    def detecter_anomalies_serietemp(
        col_valeur: str = "value",
        col_temps: str = "timestamp",
        seuil: float = 3.0,
    ) -> dict:
        return detecter_anomalies(
            df=df,
            col_valeur=col_valeur,
            col_temps=col_temps,
            seuil=seuil,
        )

    forecast_tool = StructuredTool.from_function(
        func=forecast_serietemp,
        name="forecast_serietemp",
        description=(
            "Use this tool when the user asks for forecasting, prediction, ARIMA forecasting, "
            "or future estimation of a time series. "
            "Do not use it for anomaly detection."
        ),
        args_schema=Forecast_tool,
    )

    anomalie_tool = StructuredTool.from_function(
        func=detecter_anomalies_serietemp,
        name="detect_timeseries_anomalies",
        description=(
            "Use this tool when the user asks for anomaly detection, outlier detection, "
            "abnormal points, z-score analysis, or detection of extreme observations "
            "in a time series. Do not use it for forecasting."
        ),
        args_schema=Anomalie_tool,
    )

    return [forecast_tool, anomalie_tool]


# Sélection de la fonctionnalité à exécuter

def fallback_tool_selection(instruction: str, tool_map: dict) -> list:
    """
    Fallback tool selection using keyword matching.
    Returns list of tool call dicts.
    """
    instruction_lower = instruction.lower()
    
    asks_forecast = any(word in instruction_lower for word in ["forecast", "predict", "future", "next", "arima"])
    asks_anomaly = any(word in instruction_lower for word in ["anomal", "outlier", "abnormal", "unusual", "detect"])
    
    tool_calls = []
    
    if asks_anomaly:
        tool_calls.append({
            "name": "detect_timeseries_anomalies",
            "args": {"col_valeur": "value", "col_temps": "timestamp", "seuil": 3.0}
        })
    
    if asks_forecast:
        tool_calls.append({
            "name": "forecast_serietemp",
            "args": {"col_valeur": "value", "col_temps": "timestamp", "train_ratio": 0.8, "max_p": 3, "max_q": 3, "long_forecast": 100}
        })
    
    if not tool_calls:
        raise ValueError("Could not determine which tool to use from instruction.")
    
    return tool_calls


def select_fonctionnalite(df: pd.DataFrame, instruction: str, llm) -> Dict[str, Any]:
    if not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame.")

    if not instruction:
        raise ValueError("instruction must be non-empty.")

    tools = analyse_tool(df)
    tool_map = {tool.name: tool for tool in tools}
    
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = (
    "You are an analysis router. "
    "A pandas DataFrame is already loaded and is already captured inside the available tools. "
    "You must not ask the user to provide data. "
    "Your only job is to select and call the correct tool(s). "
    "Use forecast_serietemp for forecasting, prediction, ARIMA forecasting, or future estimation. "
    "Use detect_timeseries_anomalies for anomaly detection, outlier detection, abnormal points, "
    "z-score analysis, or extreme observations. "
    "If the user requests both forecasting and anomaly detection, call both tools. "
    "If the request does not match any available tool, do not call a tool."
    "If none of your functionnalities are relevant, do not call any tool and return a message indicating you could not find a relevant analysis to perform."
)
    
    try:
        response = llm_with_tools.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=instruction)
        ])
        print(f"DEBUG: LLM response type: {type(response)}")
        print(f"DEBUG: LLM response: {response}")
        print(f"DEBUG: Has tool_calls attr: {hasattr(response, 'tool_calls')}")
        
        tool_calls = getattr(response, "tool_calls", None) or []
        print(f"DEBUG: tool_calls extracted: {tool_calls}")
        
        if not tool_calls:
            print(f"DEBUG: No tool calls made by LLM, using fallback keyword matching")
            tool_calls = fallback_tool_selection(instruction, tool_map)
        
        print(f"DEBUG: LLM called {len(tool_calls)} tool(s)")
        results = {}
        
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {}) or {}
            print(f"DEBUG: Executing tool: {tool_name}")
            tool = tool_map[tool_name]
            results[tool_name] = tool.invoke(tool_args)
        
        if len(results) > 1:
            return {
                "Fonctionnalité choisie": "combined",
                "resultat de l'analyse": {
                    "fonctionnalité": "combined",
                    "results": results,
                    "message": f"Multiple analyses executed: {', '.join(results.keys())}"
                }
            }
        else:
            tool_name = list(results.keys())[0]
            return {
                "Fonctionnalité choisie": results[tool_name].get("fonctionnalité", tool_name),
                "resultat de l'analyse": results[tool_name]
            }
    except Exception as e:
        print(f"LLM tool calling failed: {e}")
        raise ValueError(f"Failed to select and execute analysis tool: {e}")

def create_analysis_agent(
    llm,
    *,
    datastore_loader: Optional[Callable[[], Datastore]] = None,
):
    """
    Build a LangGraph-powered analysis agent that uses implementation functions.
    Args:
        llm: Base chat model that supports tool calling.
        datastore_loader: Optional callable returning a datastore snapshot when the
            runtime state does not provide one.
    """

    def load_datastore_node(state: AnalysisState) -> AnalysisState:
        """Collect datastore context from the incoming state or a loader."""
        print("Loading datastore context")
        datastore, summary, referenced_keys, error = _collect_datastore_context(
            state, datastore_loader
        )
        if error:
            state["error_message"] = error
        state["datastore"] = datastore
        state["datastore_summary"] = summary
        state["referenced_keys"] = referenced_keys
        return state

    def generate_analysis_node(state: AnalysisState) -> AnalysisState:
        """Use LLM to select tool and perform analysis."""
        print("Generate analysis insights")
        instruction = state.get("instruction", "").strip()
        datastore = state.get("datastore", {})
        if not datastore:
            state["error_message"] = "No datastore available for analysis."
            state["analysis_agent_final_answer"] = "Analysis agent could not perform analysis due to missing data."
            state["insights"] = []
            state["follow_up_questions"] = []
            state.setdefault("referenced_keys", [])
            return state
        
        # Load the first available DataFrame from datastore
        ref_key = list(datastore.keys())[0]
        try:
            df = load_df(ref_key)
        except Exception as exc:
            state["error_message"] = f"Failed to load data: {exc}"
            state["analysis_agent_final_answer"] = "Analysis agent could not load data for analysis."
            state["insights"] = []
            state["follow_up_questions"] = []
            state.setdefault("referenced_keys", [])
            return state
        
        try:
            result = select_fonctionnalite(df, instruction, llm)
            fonctionnalite = result["Fonctionnalité choisie"]
            analyse_result = result["resultat de l'analyse"]
            
            if fonctionnalite == "forecast":
                final_answer = f"Forecast completed with ARIMA order {analyse_result['order']}. Forecast values: {analyse_result['forecast_values'][:10]}..."
                insights = [f"Best ARIMA order: {analyse_result['order']}", "Forecast generated for future steps."]
                follow_ups = ["Consider validating the forecast with additional data."]
            elif fonctionnalite == "detect_timeseries_anomalies":
                final_answer = analyse_result.get("message", "Anomaly detection completed.")
                insights = [f"Anomalies detected at indices: {analyse_result.get('anomalies', [])}"]
                follow_ups = ["Review the detected anomalies for potential issues."]
            elif fonctionnalite == "combined":
                results = analyse_result.get("results", {})
                anomaly_result = results.get("detect_timeseries_anomalies", {})
                forecast_result = results.get("forecast_serietemp", {})
                
                anomaly_msg = anomaly_result.get("message", "Anomalies detected")
                forecast_order = forecast_result.get("order", "unknown")
                forecast_vals = forecast_result.get("forecast_values", [])[:5]
                
                final_answer = f"Combined Analysis Results:\n- {anomaly_msg}\n- Forecast completed with ARIMA order {forecast_order}. First 5 forecast values: {forecast_vals}..."
                
                anomalies = anomaly_result.get("anomalies", [])
                insights = [
                    f"Anomalies detected at indices: {anomalies}",
                    f"Best ARIMA order: {forecast_order}",
                    "Both analyses completed successfully."
                ]
                follow_ups = [
                    "Review the detected anomalies before making forecasting decisions.",
                    "Consider how anomalies might affect the forecast accuracy."
                ]
            else:
                final_answer = "Analysis completed."
                insights = []
                follow_ups = []
            
        except Exception as exc:
            print(f"Failed to generate analysis: {exc}")
            state["error_message"] = f"Failed to generate analysis: {exc}"
            state["analysis_agent_final_answer"] = "Analysis agent could not generate insights."
            state["insights"] = []
            state["follow_up_questions"] = []
            state.setdefault("referenced_keys", [])
            return state
        
        state["analysis_agent_final_answer"] = final_answer
        state["insights"] = insights
        state["follow_up_questions"] = follow_ups
        state["referenced_keys"] = [ref_key]
        return state

    workflow = StateGraph(AnalysisState)
    workflow.add_node("load_datastore", load_datastore_node)
    workflow.add_node("generate_analysis", generate_analysis_node)
    workflow.add_edge(START, "load_datastore")
    workflow.add_edge("load_datastore", "generate_analysis")
    workflow.add_edge("generate_analysis", END)
    return workflow.compile()


__all__ = ["create_analysis_agent", "AnalysisState"]