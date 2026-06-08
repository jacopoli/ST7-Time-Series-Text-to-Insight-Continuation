import os
import sys
import json
import shutil
import time
from datetime import datetime
from typing import Dict, List
import pandas as pd
import numpy as np
import traceback
import psycopg
from dotenv import load_dotenv

# --- Détection de la racine du projet ---
current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(current_dir, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# --- Imports du projet ---
from utils.output_basemodels import VisualizationCodeOutput
from agents.visualisation_agent import create_visualization_agent

# --- Imports LangChain AWS ---
from langchain_aws import ChatBedrock
from langchain_core.callbacks import BaseCallbackHandler

class BedrockTokenTracker(BaseCallbackHandler):
    """Tracker de tokens pour AWS Bedrock"""
    def __init__(self):
        self.total_tokens = 0
    def on_llm_end(self, response, **kwargs):
        try:
            usage = response.generations[0][0].message.response_metadata.get("usage", {})
            p_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
            c_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
            self.total_tokens += (p_tokens + c_tokens)
        except Exception:
            pass


class VisualisationAgentBenchmark:
    
    def __init__(self, questions_file: str = "questions_visualisation_benchmark.json"):
        self.questions_path = os.path.join(os.path.dirname(__file__), questions_file)
        self.results = []
        self.questions = self._load_json(self.questions_path)
        
        # 1. Chargement des données depuis PostgreSQL vers Pandas
        self.local_datastore = self._load_dataframes_from_db()
        
        # 2. Initialisation du LLM AWS Bedrock structuré
        base_llm = ChatBedrock(
            model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0", 
            model_kwargs={"temperature": 0}
        )
        self.llm = base_llm.with_structured_output(VisualizationCodeOutput)
        self.agent_graph = create_visualization_agent(self.llm)

    def _load_dataframes_from_db(self) -> Dict[str, pd.DataFrame]:
        """Se connecte à Postgres et télécharge les tables pour l'ancien agent."""
        DSN = os.getenv("POSTGRES_DSN")
        dataframes = {}
        tables_to_load = ["projects", "sites", "gateways", "configs", "variables_metrics_raw_data"]
        
        print("\n📥 Chargement des tables PostgreSQL en mémoire pour l'Agent...")
        if not DSN:
            print("❌ ERREUR : POSTGRES_DSN introuvable dans le .env !")
            return {}

        try:
            with psycopg.connect(DSN) as conn:
                for table in tables_to_load:
                    try:
                        with conn.cursor() as cur:
                            cur.execute(f"SELECT * FROM {table};")
                            cols = [desc[0] for desc in cur.description]
                            dataframes[table] = pd.DataFrame(cur.fetchall(), columns=cols)
                            print(f"  ✅ Table '{table}' chargée : {len(dataframes[table])} lignes.")
                    except Exception as e:
                        print(f"  ⚠️ Table '{table}' ignorée : {e}")
                        conn.rollback()
        except Exception as e:
            print(f"❌ Erreur globale de connexion à la DB : {e}")
            
        print("-" * 50)
        return dataframes

    def _load_json(self, path: str) -> List[Dict]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur de chargement des questions : {e}")
            return []

    def _execute_test(self, question: Dict) -> Dict:
        start_time = time.time()
        
        result = {
            "test_name": f"viz_Q{question.get('id', '?')}",
            "difficulty": question.get("category", "UNKNOWN").split(" - ")[0],
            "instruction": question.get("question", ""),
            "timestamp": datetime.now().isoformat(),
            "success": False, "valid": False, "error": None, 
            "execution_time": 0, "image_path": None, "attempts": 0, "tokens": 0
        }
        
        token_tracker = BedrockTokenTracker()
        
        try:
            # On ajoute un rappel invisible pour forcer la fonction de sauvegarde du bac à sable
            safe_instruction = (
                result["instruction"] + 
                "\n\nCRITICAL: You MUST save the final plot by calling `save_figure(plt.gcf())`. "
                "Do NOT use plt.show() or standard plt.savefig()."
            )

            # L'ancien agent reçoit les DataFrames fraîchement chargés
            initial_state = {
                "instruction": safe_instruction,
                "datastore": self.local_datastore
            }
            
            final_state = self.agent_graph.invoke(
                initial_state, 
                config={"callbacks": [token_tracker]}
            )
            
            output_paths = final_state.get("output_paths", [])
            has_image = len(output_paths) > 0
            
            result.update({
                "success": has_image,
                "valid": has_image, 
                "image_path": output_paths[0] if has_image else None,
                "attempts": final_state.get("visualization_codegen_attempts", 0),
                "error": final_state.get("error_message"),
                "tokens": token_tracker.total_tokens
            })

            try:
                images_dir = os.path.join(os.path.dirname(__file__), "viz_results")
                os.makedirs(images_dir, exist_ok=True)
            
                if result["image_path"] and os.path.exists(result["image_path"]):
                    new_filename = f"viz_Q{question.get('id')}.png"
                    new_img_path = os.path.join(images_dir, new_filename)
                    shutil.copy2(result["image_path"], new_img_path)
                else:
                    result["error"] = result["error"] or "Code exécuté mais aucune image générée (fonction save_figure non appelée)."

            except Exception as e:
                print(f"Erreur lors de la sauvegarde de l'image : {e}")
                    
        except Exception as e:
            result["error"] = str(e)
            
        result["execution_time"] = time.time() - start_time
        return result

    def run(self):
        if not self.questions:
            return

        print("=" * 60)
        print(f"  Lancement du Benchmark Visualisation Agent ({len(self.questions)} questions)")
        print("=" * 60)

        grouped_questions = {}
        for q in self.questions:
            diff = q.get("category", "UNKNOWN").split(" - ")[0]
            grouped_questions.setdefault(diff, []).append(q)

        for diff in ["Theme 1", "Theme 2", "Theme 3", "Theme 4"]:
            if diff not in grouped_questions: continue
            
            print(f"\n--- {diff} TESTS ({len(grouped_questions[diff])}) ---")
            for q in grouped_questions[diff]:
                res = self._execute_test(q)
                self.results.append(res)
                
                if res['success']:
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                    
                print(f" [{diff}] {res['test_name']}: {status} ({res['execution_time']:.1f}s | {res['tokens']} tokens)")

        self._print_and_save_summary()

    def _print_and_save_summary(self):
        total = len(self.results)
        if total == 0: return

        valid_count = sum(1 for r in self.results if r["success"])
        avg_time = np.mean([r["execution_time"] for r in self.results])
        total_tokens = sum(r["tokens"] for r in self.results)
        
        print("\n" + "=" * 60)
        print(f"RÉSUMÉ GLOBAL ANCIEN AGENT : {valid_count}/{total} Valides ({(valid_count/total)*100:.1f}%)")
        print(f"Temps moyen: {avg_time:.2f}s | Tokens totaux: {total_tokens}")
        print("=" * 60)

        output_dir = os.path.join(os.path.dirname(__file__), "vis_agent_results")
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"report_vis_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        clean_results = [{k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) 
                         for k, v in r.items()} for r in self.results]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(clean_results, f, indent=2, ensure_ascii=False)
            
        print(f"Rapport détaillé sauvegardé dans : {filename}")

if __name__ == "__main__":
    benchmark = VisualisationAgentBenchmark()
    benchmark.run()