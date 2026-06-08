import os
import time
import json
import re
import base64
from typing import Annotated, Any, Dict, List, Optional, TypedDict
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from langchain_aws import ChatBedrock
from langgraph.graph import StateGraph, START, END
import psycopg
import io
from contextlib import redirect_stdout


# Import de tes helpers existants
from utils.general_helpers import llm_from
from utils.token_counter import wrap_llm_with_token_counter

# --- 1. CHARGEMENT DES PROMPTS ET UTILITAIRES ---
PROMPTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "plot_gen_visualisation_prompt.json")
with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
    PROMPTS = json.load(f)

def extract_xml_tag(text: str, tag: str) -> str:
    """Extrait proprement le contenu situé entre <tag> et </tag>."""
    match = re.search(f"<{tag}>(.*?)</{tag}>", text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""

def get_image_base64(path: str) -> str:
    """Encode l'image en Base64 pour l'agent de Vision."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# --- 2. L'ÉTAT DU GRAPHE ---
class PlotGenState(TypedDict):
    instruction: str
    data_summary: str
    
    # Artefacts
    plan: Optional[str]
    code: Optional[str]
    image_path: Optional[str]
    
    # Feedbacks
    error_log: Optional[str]
    numeric_feedback: Optional[str]
    lexical_feedback: Optional[str]
    visual_feedback: Optional[str]
    
    is_valid: bool
    attempts: int


# --- 3. INITIALISATION CLAUDE (BEDROCK) ---
def get_llm():
    """Initialise et retourne l'LLM avec les variables d'environnement"""
    return wrap_llm_with_token_counter(
        llm_from(
            os.getenv("USE_PROVIDER", "aws"),
            os.getenv("USE_MODEL", "us.anthropic.claude-sonnet-4-5-20250929-v1:0"),
            agent_name="PlotGen Agent"
        )
    )


# --- 4. LES AGENTS (NŒUDS) ---

def query_planning_node(state: PlotGenState):
    """Agent 1: Query Planning"""
    start_time = time.time()
    llm = get_llm()
    
    system_prompt = PROMPTS["query_planning_node"].format(
        data_summary=state['data_summary'],
        instruction=state['instruction']
    )
    
    msg = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Analyze the request and provide your logical plan."}
    ])
    
    plan = extract_xml_tag(msg.content, "plan") or msg.content
    elapsed = time.time() - start_time
    print(f"query_planning_node: {elapsed:.2f}s")
    return {**state, "plan": plan}


def code_generation_node(state: PlotGenState):
    """Agent 2: Code Generation"""
    start_time = time.time()
    llm = get_llm()
    attempts = state.get("attempts", 0)
    
    feedbacks = []
    if state.get("error_log"): feedbacks.append(f"Python Execution Error:\n{state['error_log']}")
    if state.get("numeric_feedback"): feedbacks.append(f"Numeric Critic Rejection:\n{state['numeric_feedback']}")
    if state.get("lexical_feedback"): feedbacks.append(f"Lexical Critic Rejection:\n{state['lexical_feedback']}")
    if state.get("visual_feedback"): feedbacks.append(f"Visual Critic Rejection:\n{state['visual_feedback']}")
    
    feedback_log_str = "\n\n".join(feedbacks) if feedbacks else "None"
    
    system_prompt = PROMPTS["code_generation_node"].format(
        data_summary=state['data_summary'],
        instruction=state['instruction'],
        plan=state['plan'],
        feedback_log=feedback_log_str
    )
    
    msg = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Write the clean Python code block now."}
    ])
    
    raw_code = msg.content
    code_match = re.search(r"```python(.*?)```", raw_code, re.DOTALL)
    code = code_match.group(1).strip() if code_match else raw_code.strip()
    
    elapsed = time.time() - start_time
    print(f"code_generation_node: {elapsed:.2f}s")
    
    return {
        **state, 
        "code": code, 
        "attempts": attempts + 1,
        "error_log": None,
        "is_valid": False 
    }


def execute_code_node(state: PlotGenState):
    """Bac à sable d'exécution"""
    start_time = time.time()
    
    if os.path.exists("plotgen_out.png"):
        os.remove("plotgen_out.png")
        
    try:
        plt.clf()
        plt.close('all')
        
        # Exécution
        DB_URL = os.getenv("POSTGRES_DSN")
        try:
            # On passe directement la chaîne de connexion dans le bac à sable !
            exec(state["code"], {"plt": plt, "pd": pd, "np": np, "psycopg": psycopg, "os": os, "DB_URL": DB_URL})

        except Exception as e:
            print(f"Erreur lors de l'exécution du code: {e}")

        if os.path.exists("plotgen_out.png"):
            elapsed = time.time() - start_time
            print(f"execute_code_node: {elapsed:.2f}s | ✅ Succès de l'exécution")
            return {**state, "image_path": "plotgen_out.png", "error_log": None}
            
        # Si le code marche mais qu'il n'y a pas d'image
        elapsed = time.time() - start_time
        erreur = "Le code a tourné sans erreur, mais plt.savefig('plotgen_out.png') est manquant ou a échoué."
        print(f"execute_code_node: {elapsed:.2f}s | ❌ ERREUR SAUVEGARDE")
        print(f"\n--- 🕵️ CODE GÉNÉRÉ SANS SAUVEGARDE ---\n{state['code']}\n--------------------------------------\n")
        return {**state, "error_log": erreur, "is_valid": False}
        
    except Exception as e:
        # Si le code Python plante
        elapsed = time.time() - start_time
        erreur = f"{type(e).__name__}: {str(e)}"
        print(f"execute_code_node: {elapsed:.2f}s | 💥 CRASH PYTHON : {erreur}")
        print(f"\n--- 🕵️ CODE QUI A PLANTÉ ---\n{state['code']}\n----------------------------\n")
        return {**state, "error_log": erreur, "image_path": None, "is_valid": False}

# def numeric_feedback_node(state: PlotGenState):
#     """Agent 3: Numeric Feedback (Lecture Code)"""
#     start_time = time.time()
#     llm = get_llm()
    
#     if state.get("error_log"): return state 

#     image_path = state.get("image_path")
#     if not image_path or not os.path.exists(image_path):
#         return {**state, "lexical_feedback": "Aucune image générée à évaluer.", "is_valid": False}
    
#     img_b64 = get_image_base64(image_path)
    
#     system_prompt = PROMPTS["numeric_feedback_node"].format(
#         data_summary=state['data_summary'],
#         instruction=state['instruction'],
#         code=state['code']
#     )
    
#     msg = llm.invoke([
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": [
#             {"type": "text", "text": "Analyze the code and provide your XML evaluation."},
#             {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}
#         ]}
#     ])
    
#     is_valid = (extract_xml_tag(msg.content, "is_valid").lower() == "true")
#     feedback = extract_xml_tag(msg.content, "feedback")
    
#     elapsed = time.time() - start_time
#     print(f"numeric_feedback_node: {elapsed:.2f}s | Valid: {is_valid}")
    
#     return {**state, "numeric_feedback": None if is_valid else feedback, "is_valid": is_valid}


# def lexical_feedback_node(state: PlotGenState):
#     """Agent 4: Lexical Feedback (Lecture Code)"""
#     start_time = time.time()
#     llm = get_llm()
    
#     if state.get("error_log") or state.get("numeric_feedback"): return state
    
#     system_prompt = PROMPTS["lexical_feedback_node"].format(
#         instruction=state['instruction'],
#         code=state['code']
#     )

#     image_path = state.get("image_path")
#     if not image_path or not os.path.exists(image_path):
#         return {**state, "lexical_feedback": "Aucune image générée à évaluer.", "is_valid": False}
    
#     img_b64 = get_image_base64(image_path)
    
#     msg = llm.invoke([
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": [
#             {"type": "text", "text": "Analyze the code and provide your XML evaluation."},
#             {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}
#         ]}
#     ])
    
#     is_valid = (extract_xml_tag(msg.content, "is_valid").lower() == "true")
#     feedback = extract_xml_tag(msg.content, "feedback")
    
#     elapsed = time.time() - start_time
#     print(f"lexical_feedback_node: {elapsed:.2f}s | Valid: {is_valid}")
    
#     return {**state, "lexical_feedback": None if is_valid else feedback, "is_valid": is_valid}


def numeric_feedback_node(state: PlotGenState):
    """Agent 3: Numeric Feedback (Lecture de Code uniquement)"""
    start_time = time.time()
    llm = get_llm()
    
    if state.get("error_log"): return state 

    system_prompt = PROMPTS["numeric_feedback_node"].format(
        data_summary=state['data_summary'],
        instruction=state['instruction'],
        code=state['code']
    )
    
    # Appel simplifié : on n'envoie plus le bloc "image"
    msg = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Analyze the code and provide your XML evaluation."}
    ])
    
    is_valid = (extract_xml_tag(msg.content, "is_valid").lower() == "true")
    feedback = extract_xml_tag(msg.content, "feedback")
    
    elapsed = time.time() - start_time
    print(f"numeric_feedback_node: {elapsed:.2f}s | Valid: {is_valid}")
    
    return {**state, "numeric_feedback": None if is_valid else feedback, "is_valid": is_valid}


def lexical_feedback_node(state: PlotGenState):
    """Agent 4: Lexical Feedback (Lecture de Code uniquement)"""
    start_time = time.time()
    llm = get_llm()
    
    if state.get("error_log") or state.get("numeric_feedback"): return state
    
    system_prompt = PROMPTS["lexical_feedback_node"].format(
        instruction=state['instruction'],
        code=state['code']
    )

    # Appel simplifié : on n'envoie plus le bloc "image"
    msg = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Analyze the code and provide your XML evaluation."}
    ])
    
    is_valid = (extract_xml_tag(msg.content, "is_valid").lower() == "true")
    feedback = extract_xml_tag(msg.content, "feedback")
    
    elapsed = time.time() - start_time
    print(f"lexical_feedback_node: {elapsed:.2f}s | Valid: {is_valid}")
    
    return {**state, "lexical_feedback": None if is_valid else feedback, "is_valid": is_valid}

# =====================================================================
# AGENT 5 : VISUAL FEEDBACK 
# =====================================================================

# ---------------------------------------------------------------------
# VERSION A : LECTURE DE CODE (RAPIDE - ACTIF)
# ---------------------------------------------------------------------
def visual_feedback_node(state: PlotGenState):
    """Agent 5: Visual Feedback (Heuristiques basées sur le Code)"""
    start_time = time.time()
    llm = get_llm()
    
    if state.get("error_log") or state.get("numeric_feedback") or state.get("lexical_feedback"): 
        return state
        
    system_prompt = PROMPTS["visual_feedback_node"].format(
    instruction=state['instruction'], 
    code=state['code']
)
    
    msg = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Analyze the code and provide your XML evaluation."}
    ])
    
    is_valid = (extract_xml_tag(msg.content, "is_valid").lower() == "true")
    feedback = extract_xml_tag(msg.content, "feedback")
    
    elapsed = time.time() - start_time
    print(f"visual_feedback_node (Code): {elapsed:.2f}s | Valid: {is_valid}")
    
    return {**state, "visual_feedback": None if is_valid else feedback, "is_valid": is_valid}

# ---------------------------------------------------------------------
# VERSION B : VISION MULTIMODALE
# ---------------------------------------------------------------------
# def visual_feedback_node(state: PlotGenState):
#     """Agent 5: Visual Feedback (Regarde la vraie image générée)"""
#     start_time = time.time()
#     llm = get_llm()
    
#     if state.get("error_log") or state.get("numeric_feedback") or state.get("lexical_feedback"): 
#         return state
        
#     img_b64 = get_image_base64(state["image_path"])
    
#     system_prompt = PROMPTS["visual_feedback_node"].format(
#     instruction=state['instruction'], 
#     code=state['code']
# )
    
#     msg = llm.invoke([
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": [
#             {"type": "text", "text": "Analyze this chart visually and provide your XML evaluation."},
#             {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}
#         ]}
#     ])
    
#     is_valid = (extract_xml_tag(msg.content, "is_valid").lower() == "true")
#     feedback = extract_xml_tag(msg.content, "feedback")
    
#     elapsed = time.time() - start_time
#     print(f"visual_feedback_node (Vision): {elapsed:.2f}s | Valid: {is_valid}")
    
    # return {**state, "visual_feedback": None if is_valid else feedback, "is_valid": is_valid}
# =====================================================================


# --- 5. ASSEMBLAGE DU GRAPHE PLOTGEN ---

def build_plotgen_graph():
    workflow = StateGraph(PlotGenState)

    workflow.add_node("planner", query_planning_node)
    workflow.add_node("coder", code_generation_node)
    workflow.add_node("executor", execute_code_node)
    workflow.add_node("numeric_critic", numeric_feedback_node)
    workflow.add_node("lexical_critic", lexical_feedback_node)
    workflow.add_node("visual_critic", visual_feedback_node)

    # Flux initial
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "executor")
    
    # Routeur de l'exécuteur Python
    def route_executor(state: PlotGenState):
        if state.get("error_log"):
            return END if state.get("attempts", 0) >= 4 else "coder"
        return "numeric_critic"

    workflow.add_conditional_edges("executor", route_executor)

    # Routeurs des Critiques (Early Stopping)
    def route_numeric(state: PlotGenState):
        if not state.get("is_valid"): 
            return END if state.get("attempts", 0) >= 4 else "coder"
        return "lexical_critic"
        # return "visual_critic"

    def route_lexical(state: PlotGenState):
        if not state.get("is_valid"):
            return END if state.get("attempts", 0) >= 4 else "coder"
        return "visual_critic"

    def route_visual(state: PlotGenState):
        if not state.get("is_valid"):
            return END if state.get("attempts", 0) >= 4 else "coder"
        return END

    workflow.add_conditional_edges("numeric_critic", route_numeric)
    workflow.add_conditional_edges("lexical_critic", route_lexical)
    workflow.add_conditional_edges("visual_critic", route_visual)
    
    return workflow.compile()