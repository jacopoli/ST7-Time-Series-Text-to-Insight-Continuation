import os
import sys
from dotenv import load_dotenv
import json
import shutil
import time
from datetime import datetime
from typing import Dict, List
import pandas as pd
import numpy as np
import traceback

# --- NOUVEAUX IMPORTS POUR LES TOKENS ---
from langchain_core.callbacks import BaseCallbackHandler

load_dotenv()
PROJECT_ROOT = os.getenv("PROJECT_ROOT")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agents.plot_gen_visual_agent import build_plotgen_graph, PlotGenState

# --- 1. AJOUT DU TRACKER DE TOKENS BEDROCK ---
class BedrockTokenTracker(BaseCallbackHandler):
    """Écoute les réponses du LLM pour compter les tokens sur AWS Bedrock."""
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


EXPECTED_SCHEMA = {
    "projects": [
        ("id", "integer"), ("name", "text"), ("country", "text"),
        ("client_company_name", "text"), ("time_zone", "text"), ("city", "text"),
        ("start_date", "text"), ("description", "text")
    ],
    "sites": [
        ("id_1", "integer"), ("name_2", "text"), ("type", "text"), ("extent", "text"),
        ("start_date_3", "text"), ("previsional_end", "text"), ("project_id", "integer"),
        ("created_at", "text"), ("updated_at", "text"), ("deleted", "text"),
        ("operating_rate", "double precision"), ("main_site", "double precision")
    ],
    "gateways": [
        ("id", "integer"), ("gateway_name", "text"), ("serial_number", "text"),
        ("transfer_protocol", "text"), ("power_supply", "text"), ("installation_date", "text"),
        ("operating_team", "text"), ("x", "double precision"), ("y", "double precision"),
        ("z", "double precision"), ("time_zone", "text"), ("geom", "text"),
        ("created_at", "text"), ("updated_at", "text"), ("provider", "integer"),
        ("site_id", "integer")
    ],
    "configs": [
        ("id_1", "integer"), ("file_name", "text"), ("last_treatment", "text"),
        ("ftp", "text"), ("ftp_ip", "text"), ("ftp_user", "text"),
        ("ftp_password", "text"), ("ftp_directory", "text"), ("config", "text"),
        ("gateway_id", "integer"), ("parsing_id", "integer"), ("file_id", "double precision"),
        ("to_move", "boolean"), ("regex_variables", "text"), ("created_at_1", "text"),
        ("updated_at_1", "text"), ("active", "boolean"), ("error_message", "text"),
        ("last_modified", "text"), ("keep_folder", "double precision")
    ],
    "variables_metrics_raw_data": [
        ("gateway_name", "text"), ("variable_name", "text"), ("variable_alias", "text"),
        ("sensor_id", "integer"), ("value", "double precision"), ("timestamp", "text"),
        ("variable_id", "integer"), ("unit", "text"), ("metric", "text")
    ]
}


class PlotGenBenchmark:
    
    def __init__(self, datasets_path: str = None, questions_file: str = "questions_visualisation_benchmark.json"):
        self.datasets_path = datasets_path or os.path.join(PROJECT_ROOT, "datasets")
        self.questions_path = os.path.join(os.path.dirname(__file__), questions_file)
        self.results = []
        
        self.questions = self._load_json(self.questions_path)
        self.data_summary = self._load_and_summarize_datasets()

    def _load_json(self, path: str) -> List[Dict]:
        """Charge le fichier JSON des questions."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur de chargement des questions : {e}")
            return []

    def _load_and_summarize_datasets(self) -> str:
        """Génère le contexte complet de la base PostgreSQL pour le LLM."""

        def summarize_db_table_for_llm(table_name: str, columns_and_types: list) -> str:
            schema_lines = [f"- `{col_name}` ({col_type})" for col_name, col_type in columns_and_types]
            schema_markdown = "\n".join(schema_lines)

            load_code = f"""import os
import psycopg
import pandas as pd

# Chargement sécurisé depuis l'environnement local
DSN = os.getenv("POSTGRES_DSN")

with psycopg.connect(DSN) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM {table_name};")
        cols = [desc[0] for desc in cur.description]
        df_{table_name} = pd.DataFrame(cur.fetchall(), columns=cols)"""

            return (
                f"### DATABASE TABLE: {table_name.upper()}\n"
                f"**CRITICAL - Exact Python code to load this table into a DataFrame (`df_{table_name}`):**\n"
                f"```python\n{load_code}\n```\n\n"
                f"Available Columns & Types:\n{schema_markdown}\n"
                f"--------------------------------------------------\n"
            )

        db_context = "VOICI LES TABLES POSTGRESQL DISPONIBLES ET COMMENT LES REQUÊTER :\n\n"
        
        try:
            for table_name, schema_info in EXPECTED_SCHEMA.items():
                db_context += summarize_db_table_for_llm(table_name, schema_info)
        except NameError:
            print("ERREUR : Le dictionnaire EXPECTED_SCHEMA est introuvable. Ajoute-le en haut du fichier.")
            
        return db_context


    def _execute_test(self, question: Dict) -> Dict:
        """Exécute l'agent PlotGen pour une question donnée."""
        start_time = time.time()
        
        # Initialisation de la structure du résultat (ajout du champ 'tokens')
        result = {
            "test_name": f"Q{question.get('id', '?')}: {question.get('category', 'UNKNOWN')}",
            "difficulty": question.get("category", "UNKNOWN").split(" - ")[0],
            "instruction": question.get("question", ""),
            "timestamp": datetime.now().isoformat(),
            "success": False, "valid": False, "error": None, 
            "execution_time": 0, "image_path": None, "attempts": 0, "tokens": 0
        }
        
        # 2. INITIALISATION DU TRACKER
        token_tracker = BedrockTokenTracker()
        
        try:
            graph = build_plotgen_graph()
            initial_state = PlotGenState(
                instruction=result["instruction"],
                data_summary=self.data_summary,
                plan=None, code=None, image_path=None, error_log=None,
                numeric_feedback=None, lexical_feedback=None, visual_feedback=None,
                is_valid=False, attempts=0
            )
            
            # 3. INJECTION DU TRACKER DANS L'APPEL LANGGRAPH
            final_state = graph.invoke(initial_state, config={"callbacks": [token_tracker]})
            
            result.update({
                "success": True,
                "valid": final_state.get("is_valid", False),
                "image_path": final_state.get("image_path"),
                "attempts": final_state.get("attempts", 0),
                "tokens": token_tracker.total_tokens  # 4. RÉCUPÉRATION DES TOKENS
            })

            try:
                images_dir = os.path.join(os.path.dirname(__file__), "plot_gen_results_NoVLM")
                os.makedirs(images_dir, exist_ok=True)
            
                new_filename = f"plot_gen_Q{question.get('id')}.png"
                new_img_path = os.path.join(images_dir, new_filename)
                original_img_path = final_state.get("image_path")
                
                if original_img_path and os.path.exists(original_img_path):
                    shutil.copy2(original_img_path, new_img_path)
                    print(f"Image sauvegardée sous : {new_img_path}")
                else:
                    print("Aucune image n'a été générée par l'agent à sauvegarder.")

            except Exception as e:
                print(f"Erreur lors de la sauvegarde de l'image : {e}")
                    
        except Exception as e:
            print(f"\n💥 ERREUR FATALE DANS LANGGRAPH :")
            traceback.print_exc() 
            result["error"] = str(e)
            
        result["execution_time"] = time.time() - start_time
        return result

    def run(self):
        """Point d'entrée pour exécuter tous les tests groupés par difficulté."""
        if not self.questions:
            print("Aucune question à traiter. Vérifiez le fichier JSON.")
            return

        print("=" * 60)
        print(f"  Lancement du Benchmark PlotGen ({len(self.questions)} questions)")
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
                
                if res['success'] and res['valid']:
                    status = "✅ PASS"
                elif res['success']:
                    status = "⚠️ INVALIDE (Refus Agent Evaluateur)"
                else:
                    status = "❌ CRASH (Erreur Python)"
                    
                # 5. AFFICHAGE DES TOKENS DANS LA CONSOLE
                print(f" [{diff}] {res['test_name']}: {status} ({res['execution_time']:.1f}s | {res['tokens']} tokens)")

        self._print_and_save_summary()

    def _print_and_save_summary(self):
        """Affiche le résumé dans la console et sauvegarde un fichier JSON."""
        total = len(self.results)
        if total == 0: return

        valid_count = sum(1 for r in self.results if r["valid"])
        avg_time = np.mean([r["execution_time"] for r in self.results])
        total_tokens = sum(r["tokens"] for r in self.results)
        
        print("\n" + "=" * 60)
        print(f"RÉSUMÉ GLOBAL : {valid_count}/{total} Valides ({(valid_count/total)*100:.1f}%)")
        print(f"Temps moyen: {avg_time:.2f}s | Tokens totaux: {total_tokens}")
        print(f"Graphiques avec Erreurs/Refus: {sum(1 for r in self.results if r['error'])}")
        print("=" * 60)

        output_dir = os.path.join(os.path.dirname(__file__), "plot_gen_results")
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        clean_results = [{k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) 
                         for k, v in r.items()} for r in self.results]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(clean_results, f, indent=2, ensure_ascii=False)
            
        print(f"Rapport détaillé sauvegardé dans : {filename}")

if __name__ == "__main__":
    benchmark = PlotGenBenchmark()
    benchmark.run()