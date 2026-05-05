import base64
import os
from typing import Annotated, Any, Dict, List, Optional, TypedDict
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from langchain_aws import ChatBedrock
from langgraph.graph import END, START, StateGraph
from utils.general_helpers import llm_from
from utils.token_counter import wrap_llm_with_token_counter

# --- 1. L'ÉTAT DU GRAPHE (Adapté pour PlotGen) ---
class PlotGenState(TypedDict):
    instruction: str
    data_summary: str
    
    # Artefacts
    plan: Optional[str]              # Sortie du Query Planning Agent
    code: Optional[str]              # Sortie du Code Generation Agent
    image_path: Optional[str]
    
    # Feedbacks spécifiques à PlotGen
    error_log: Optional[str]         # Erreurs Python
    numeric_feedback: Optional[str]  # Erreurs de données sur le graphique
    lexical_feedback: Optional[str]  # Erreurs de textes/labels
    visual_feedback: Optional[str]   # Erreurs d'esthétique
    
    is_valid: bool
    attempts: int

# --- 2. INITIALISATION CLAUDE (BEDROCK) ---
def get_llm():
    """Initialise et retourne l'LLM avec les variables d'environnement"""
    return wrap_llm_with_token_counter(
        llm_from(
            os.getenv("USE_PROVIDER", "aws"),
            os.getenv("USE_MODEL", "us.anthropic.claude-sonnet-4-5-20250929-v1:0"),
            agent_name="PlotGen Agent"
        )
    )

# --- 3. LES 5 AGENTS PLOTGEN ---

def query_planning_node(state: PlotGenState):
    """Agent 1: Query Planning Agent"""
    llm = get_llm()
    prompt = f"""Décompose cette requête de visualisation en étapes de code logiques (Pseudo-code).
    Instruction: {state['instruction']}
    Données: {state['data_summary']}"""
    
    response = llm.invoke(prompt)
    return {**state, "plan": response.content}

def code_generation_node(state: PlotGenState):
    """Agent 2: Code Generation Agent avec Self-Reflection"""
    llm = get_llm()
    attempts = state.get("attempts", 0)
    
    prompt = f"""Tu es l'Agent Codeur. Écris le script Python Matplotlib.
    Plan d'action: {state['plan']}
    
    --- FEEDBACK DES ITÉRATIONS PRÉCÉDENTES ---
    Erreur Python: {state.get('error_log', 'Aucune')}
    Feedback Numérique: {state.get('numeric_feedback', 'Aucun')}
    Feedback Lexical: {state.get('lexical_feedback', 'Aucun')}
    Feedback Visuel: {state.get('visual_feedback', 'Aucun')}
    
    Génère uniquement le code Python. Sauvegarde dans 'plotgen_out.png'.
    """
    
    response = llm.invoke(prompt)
    try:
        code = response.content.split("```python")[1].split("```")[0].strip()
    except IndexError:
        code = response.content # Fallback
    
    return {**state, "code": code, "attempts": attempts + 1}

def execute_code_node(state: PlotGenState):
    """Bac à sable d'exécution"""
    try:
        plt.clf()
        plt.close('all')
        exec(state["code"], {"plt": plt, "pd": pd, "np": np})
        
        if os.path.exists("plotgen_out.png"):
            # Si le code marche, on efface l'erreur python et on passe aux critiques
            return {**state, "image_path": "plotgen_out.png", "error_log": None}
        return {**state, "error_log": "Image non trouvée."}
    except Exception as e:
        return {**state, "error_log": str(e), "image_path": None}

def get_image_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def numeric_feedback_node(state: PlotGenState):
    """Agent 3: Numeric Feedback (Vérifie la cohérence des courbes/barres)"""
    llm = get_llm()
    if state["error_log"]: return state # On ne critique pas s'il n'y a pas d'image
    
    img_b64 = get_image_base64(state["image_path"])
    msg = llm.invoke([{"role": "user", "content": [
        {"type": "text", "text": f"Vérifie la cohérence numérique de ce graphique par rapport aux données: {state['data_summary']}. Le type de graphique est-il le bon ? Réponds 'VALIDE' ou donne les corrections."},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}
    ]}])
    return {**state, "numeric_feedback": msg.content if "VALIDE" not in msg.content.upper() else None}

def lexical_feedback_node(state: PlotGenState):
    """Agent 4: Lexical Feedback (Vérifie les textes)"""
    llm = get_llm()
    if state["error_log"] or state.get("numeric_feedback"): return state
    
    img_b64 = get_image_base64(state["image_path"])
    msg = llm.invoke([{"role": "user", "content": [
        {"type": "text", "text": f"Vérifie que les titres, axes et légendes correspondent bien à l'instruction : {state['instruction']}. Réponds 'VALIDE' ou donne les corrections."},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}
    ]}])
    return {**state, "lexical_feedback": msg.content if "VALIDE" not in msg.content.upper() else None}

def visual_feedback_node(state: PlotGenState):
    """Agent 5: Visual Feedback (Vérifie l'esthétique)"""
    llm = get_llm()
    # Ne s'exécute que si les maths et les textes sont corrects
    if state["error_log"] or state.get("numeric_feedback") or state.get("lexical_feedback"): 
        return {**state, "is_valid": False}
        
    img_b64 = get_image_base64(state["image_path"])
    msg = llm.invoke([{"role": "user", "content": [
        {"type": "text", "text": "Vérifie l'esthétique : les couleurs sont-elles distinctes ? Y a-t-il des textes qui se chevauchent ? La mise en page est-elle propre ? Réponds 'VALIDE' ou donne les corrections."},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}
    ]}])
    
    is_ok = "VALIDE" in msg.content.upper()
    return {**state, "visual_feedback": msg.content if not is_ok else None, "is_valid": is_ok}

# --- 4. ASSEMBLAGE DU GRAPHE PLOTGEN ---

def build_plotgen_graph():
    workflow = StateGraph(PlotGenState)

    workflow.add_node("planner", query_planning_node)
    workflow.add_node("coder", code_generation_node)
    workflow.add_node("executor", execute_code_node)
    workflow.add_node("numeric_critic", numeric_feedback_node)
    workflow.add_node("lexical_critic", lexical_feedback_node)
    workflow.add_node("visual_critic", visual_feedback_node)

    # Flux d'exécution
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "executor")
    
    # La chaîne de critiques (S'exécute séquentiellement)
    workflow.add_edge("executor", "numeric_critic")
    workflow.add_edge("numeric_critic", "lexical_critic")
    workflow.add_edge("lexical_critic", "visual_critic")

    # Routeur : On boucle si une erreur est détectée à n'importe quelle étape
    def router(state: PlotGenState):
        if state["is_valid"] or state["attempts"] >= 4:
            return END
        return "coder"

    workflow.add_conditional_edges("visual_critic", router)
    
    return workflow.compile()