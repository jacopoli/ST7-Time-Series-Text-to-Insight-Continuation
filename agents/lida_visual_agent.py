import os
import base64
import pandas as pd
from lida import Manager, TextGenerationConfig, llm

# --- CONFIGURATION AWS BEDROCK ---
# On utilise la v2 de Sonnet via l'adaptateur LiteLLM
MODEL_ID = os.getenv("USE_MODEL", "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0")

def run_standalone_lida(csv_path: str, instruction: str, output_image_name: str = "lida_output.png"):
    """
    Exécute l'agent LIDA de manière totalement indépendante.
    """
    print(f" Initialisation de LIDA avec {MODEL_ID}...")
    
    # 1. Connexion au LLM
    try:
        lida_llm = llm("litellm", model=MODEL_ID)
        lida = Manager(text_gen=lida_llm)
        textgen_config = TextGenerationConfig(n=1, temperature=0.0)
    except Exception as e:
        print(f"Erreur d'initialisation du LLM : {e}")
        return
    
    try:
        # 2. Phase de résumé (LIDA lit les données et crée un contexte)
        print(f"Analyse du dataset : {csv_path}")
        summary = lida.summarize(csv_path, summary_method="default", textgen_config=textgen_config)
        
        # 3. Phase de génération (LIDA écrit le code et génère le graphique)
        print(f"Génération du graphique pour : '{instruction}'")
        charts = lida.visualize(
            summary=summary,
            goal=instruction,
            library="matplotlib", # On force matplotlib pour ton projet
            textgen_config=textgen_config
        )
        
        # 4. Traitement du résultat
        if charts and len(charts) > 0:
            chart = charts[0]
            
            # Sauvegarde du code généré par LIDA
            print("\n--- CODE GÉNÉRÉ PAR LIDA ---")
            print(chart.code)
            print("----------------------------\n")
            
            # Sauvegarde de l'image (LIDA renvoie du base64)
            img_data = base64.b64decode(chart.raster)
            with open(output_image_name, "wb") as f:
                f.write(img_data)
                
            print(f"Succès ! L'image a été sauvegardée sous : {output_image_name}")
            return chart.code
        else:
            print("/!\ LIDA n'a retourné aucun graphique.")
            return None
            
    except Exception as e:
        print(f"Erreur pendant l'exécution de LIDA : {str(e)}")
        return None

# --- TEST DIRECT ---
if __name__ == "__main__":
    # Assure-toi que ce fichier existe, ou remplace-le par un chemin valide chez toi
    mon_csv = "datasets/gateways_configs_sensors(in).csv" 
    
    ma_question = "Génère un diagramme en barres montrant le nombre de gateways par type de protocole de transfert (transfer_protocol)."
    
    # Exécution
    if os.path.exists(mon_csv):
        run_standalone_lida(mon_csv, ma_question, "test_lida_gateways.png")
    else:
        print(f"Fichier introuvable : {mon_csv}.")