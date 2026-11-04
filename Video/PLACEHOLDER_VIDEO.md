# Démo Vidéo – SMA Revue de Littérature

Ce dossier contiendra la vidéo de démonstration du projet.

## Contenu attendu de la démo (~5 minutes)

1. **Introduction** (30s) : Présentation du problème et de la solution SMA
2. **Architecture n8n** (1min) : Montrer le workflow visuel dans n8n
3. **Exécution Agent 1** (1min) : Ingestion de 3 papers scientifiques, vérification ChromaDB
4. **Exécution Agent 2** (1min) : Synthèse thématique en action, résultats JSON
5. **Exécution Agent 3** (1min) : Détection des gaps, rapport généré
6. **Human-in-the-Loop** (30s) : Montrer la validation humaine dans l'orchestrateur
7. **Rapport final** (30s) : Présenter le rapport markdown généré

## Format suggéré

- Résolution : 1920x1080 (Full HD)
- Format : MP4
- Logiciel de capture : OBS Studio (gratuit) ou Loom
- Outil de présentation : Montrer côte à côte Jupyter + n8n

## Script de démo

```
1. Ouvrir JupyterLab avec les 4 notebooks
2. Montrer le dossier papers/ avec 3 PDFs d'exemples
3. Exécuter 01_agent_ingestion.ipynb – montrer les chunks indexés
4. Exécuter 02_agent_synthese.ipynb – montrer la synthèse JSON
5. Exécuter 03_agent_detection_gaps.ipynb – montrer les gaps détectés
6. Exécuter 04_orchestrateur_sma.ipynb – montrer le graphe LangGraph
7. Ouvrir n8n et montrer le workflow importé (n8n_workflow.json)
8. Montrer le rapport final généré dans Rapport/rapport_final.md
```
