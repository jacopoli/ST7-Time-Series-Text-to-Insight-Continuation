# Benchmark Visualization - Implémentation Complète

## 📋 Résumé de la Mission

Création d'un script **benchmark_visualization.py** reprenant l'architecture du benchmark SQL existant, adapté pour tester l'**Visualization Agent** avec des cas d'usage variés (simple au complexe).

---

## 📦 Fichiers Créés/Modifiés

### 1. **benchmark_visualization.py** ⭐ (PRINCIPAL)

- **Taille**: ~600 lignes
- **Structure** : Reprend la même architecture et conventions que `test_benchmark_sql.py`
- **Fonctionnalités** :
  - Génère 8 DataFrames synthétiques pour les tests
  - Crée 20 scénarios de visualisation (simple → complexe)
  - Exécute l'agent de visualisation pour chaque scénario
  - Capture les métriques : succès, tentatives LLM, qualité
  - Sauvegarde incrémentale des résultats (Excel/CSV)
  - Génère un rapport JSON récapitulatif

### 2. **benchmark_visualization.json**

- **Contenu** : Configuration de 20 scénarios de test
- **Structure** : Format compatible avec le benchmark SQL
- **Scénarios** : 3 simples + 7 intermédiaires + 10 complexes

### 3. **BENCHMARK_VISUALIZATION_README.md** 📚

- **Documentation complète** : Usage, architecture, métriques
- **Cas d'usage** : Exemples d'exécution
- **Troubleshooting** : Solutions aux problèmes courants
- **Extensibilité** : Comment ajouter des scenarios/datasets

### 4. **run_benchmark.py** (BONUS)

- Script interactif pour exécuter les benchmarks
- Menu avec options pré-configurées (basic, quick, simple, advanced)
- Usage autonome ou via CLI

---

## 🎯 Cas de Test (20 Scénarios)

### **Simples (3)**

- `viz_001` : Line chart basic
- `viz_002` : Bar chart
- `viz_003` : Scatter plot

### **Intermédiaires (7)**

- `viz_004` : Multi-metric line chart with legend
- `viz_005` : Grouped bar chart
- `viz_006` : Subplots pour multi-sensors
- `viz_007` : Heatmap multi-site
- `viz_016` : Time series decomposition
- `viz_017` : Cumulative distribution
- `viz_019` : Violin plot by site

### **Complexes (10)**

- `viz_008` : Gestion des valeurs manquantes (NaN)
- `viz_009` : Multi-site comparison avec couleurs
- `viz_010` : Dual-axis plot
- `viz_011` : Boxplot distributions
- `viz_012` : Time series avec confidence intervals
- `viz_013` : Dashboard 4-panel
- `viz_014` : Sparse data handling
- `viz_015` : Correlation heatmap
- `viz_018` : Histogram
- `viz_020` : Complex multi-metric visualization

---

## 📊 Métriques Capturées

| Métrique            | Type          | Description                                  |
| ------------------- | ------------- | -------------------------------------------- |
| `execution_success` | Boolean       | Le code généré s'est-il exécuté ?            |
| `llm_calls_count`   | Integer       | Nombre de tentatives de génération           |
| `readability_score` | Integer (1-5) | **[Placeholder]** Clarté du code             |
| `coherence_score`   | Integer (1-5) | **[Placeholder]** Alignement avec la demande |
| `error_message`     | String        | Détails de l'erreur si echec                 |
| `output_paths`      | List          | Chemins des visualisations générées          |
| `warnings`          | List          | Avertissements non-critiques                 |

---

## 🏗️ Architecture

### Hiérarchie Execution Flow

```
START
  ↓
Générer 8 DataFrames de test
  ↓
Charger 20 scénarios
  ↓
Pour chaque scénario:
  ├─ Créer DataStore isolé
  ├─ Initialiser VisualizationState
  ├─ Invoquer le graphe de visualisation:
  │  ├─ load_context_node
  │  ├─ generate_code_node (LLM genère code)
  │  └─ execute_code_node (execute code safe)
  ├─ Capturer les métriques
  ├─ Sauvegarder les résultats
  └─ Reporter le progrès
  ↓
Générer résumé (JSON + Excel)
  ↓
END
```

### Différences avec le SQL Benchmark

| Métrique      | SQL Benchmark          | Viz Benchmark                    |
| ------------- | ---------------------- | -------------------------------- |
| **Input**     | Query SQL              | Texte (demande visua)            |
| **Output**    | SQL généré + résultats | Python code + PNG                |
| **Storage**   | Database               | DataStore (memory)               |
| **Isolation** | Via context            | DataStore isolé par scénario     |
| **Retries**   | `sql_codegen_attempts` | `visualization_codegen_attempts` |

---

## 🚀 Usage

### Option 1 : CLI Direct

```bash
# Lancer tous les tests
python benchmark_visualization.py

# 5 premiers scénarios
python benchmark_visualization.py --limit 5

# À partir du 10e scénario
python benchmark_visualization.py --start 10

# Output personnalisé
python benchmark_visualization.py --output results.xlsx --output-dir ./my_results
```

### Option 2 : Menu Interactif

```bash
# Lancer le menu
python run_benchmark.py

# Ou en ligne de commande
python run_benchmark.py quick
python run_benchmark.py basic
python run_benchmark.py advanced
```

---

## 📁 Outputs

```
benchmarks/viz_results/
├── benchmark_summary.json
│   ├── timestamp
│   ├── total_scenarios: 20
│   ├── successful_scenarios: 18
│   ├── success_rate: 90.0%
│   ├── average_attempts: 1.2
│   └── by_difficulty: {simple: 100%, intermediate: 85.7%, complex: 90%}
│
└── visualization_benchmark_results.xlsx
    └── Colonnes:
        ├── Scenario ID, Difficulty, Question
        ├── Execution Success (✓/✗)
        ├── LLM Attempts
        ├── Readability/Coherence Scores
        ├── Average Quality Score
        ├── Output Paths
        └── Error Message (si applicable)
```

---

## 🔧 Test Datasets (8 en total)

Tous générés synthétiquement dans `generate_test_dataframes()`:

1. **simple_ts** : 100 jours de données temporelles
2. **multi_ts** : 3 capteurs sur 100 jours
3. **categorical** : Données catégorisées avec timestamps
4. **wide_metrics** : 3 métriques en format large
5. **with_nan** : Données avec valeurs manquantes
6. **multi_site** : 4 sites avec températures (150h)
7. **measurements** : 5 canaux, haute fréquence (120 samples)
8. **statistics** : Agrégations min/mean/max (30 jours)

---

## ✨ Caractéristiques Clés

### 1. **Reprise du Style SQL Benchmark**

- Même structure de code, mêmes conventions de nommage
- Sauvegarde incrémentale (crash-safe)
- Rapport JSON + Excel
- Gestion cohérente des erreurs

### 2. **Isolation des Tests**

- Chaque scénario obtient un DataStore frais
- Pas de pollution d'état entre essais
- Execution safe (sandbox)

### 3. **Extensibilité**

- Facile d'ajouter des scénarios
- Facile d'ajouter des datasets
- Support pour métriques custom

### 4. **Scores Placeholders**

- `readability_score` et `coherence_score` = 0
- Réservés pour évaluation manuelle
- Peuvent être remplies par des outils de review

---

## 📥 Dépendances Requises

```bash
pip install pandas numpy matplotlib langchain-openai openpyxl
```

Si `openpyxl` manque → fallback to CSV

---

## 🎓 Interprétation des Résultats

### Success Rate par Difficulté

- **Simple**: 100% (attendu)
- **Intermediate**: 80-95% (good)
- **Complex**: 70-90% (acceptable)

### LLM Attempts

- **1.0** = Parfait (code correct du 1er coup)
- **1.5-2.0** = Bon (1-2 retries)
- **>2.0** = Préoccupant (trop de retries)

---

## 🔄 Prochaines Étapes (Suggestions)

1. **Human Review Tool** : Interface pour scorer readability/coherence
2. **Automated Scoring** : Parser le code généré pour évaluer la qualité
3. **Regression Testing** : Archiver les résultats pour comparaisons
4. **Performance Profiling** : Mesurer temps d'exécution
5. **Dataset Expansion** : Ajouter des cas réels de données temporelles

---

## 📝 Notes d'Implementation

### Conception

- Inspiration directe de `test_benchmark_sql.py`
- Adaptation pour Visualization Agent (pas de DB, utilise DataStore)
- Code bien commenté et documenté

### Robustesse

- Gestion gracieuse des erreurs LLM
- Encoding UTF-8 explicite
- Exception handling spécifique (pas too general)
- Création préalable des répertoires de sortie

### Performance

- Sauvegarde incrémentale (pas d'attente pour la fin)
- Synthétique datasets (pas de I/O)
- Optionnel: `--limit` pour tests rapides

---

## 📞 Support & Troubleshooting

Voir **BENCHMARK_VISUALIZATION_README.md** pour:

- Guide complet d'usage
- Exemples de commandes
- Solutions aux erreurs courantes
- Architecture détaillée
- Extensibilité

---

**Status**: ✅ COMPLETI  
**Version**: 1.0  
**Date**: Mars 2024  
**Auteur**: AI Assistant

Pour questions, consulter la documentation ou le code source.
