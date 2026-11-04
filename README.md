# 🤖 Multi-Agent Literature Review Assistant

> Système multi-agents (SMA) qui automatise la revue de littérature scientifique et détecte les **research gaps**.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agents-1C3C3C)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-orange)
![Gemini](https://img.shields.io/badge/Gemini-LLM-4285F4?logo=google&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-Workflow-EA4B71?logo=n8n&logoColor=white)

**Contexte :** projet académique — module *SMA / Agentic AI*, 4ᵉ année IA & Data Science, EMSI Rabat (2025-2026).

---

## 🎯 Problématique

La revue de littérature est longue et fastidieuse : il ne s'agit pas seulement de résumer des articles, mais
d'identifier les évolutions, les consensus, les contradictions et surtout **ce qui n'a pas encore été fait**.

Ce projet met en place un SMA capable de :

1. **Ingérer** un corpus d'articles scientifiques (PDF) dans une base vectorielle ;
2. **Synthétiser** le domaine par thème grâce au RAG ;
3. **Détecter** automatiquement les lacunes de recherche (chain-of-thought) ;
4. **Générer** un rapport structuré, validé par un humain (*human-in-the-loop*).

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  COUCHE 1 – ORCHESTRATION   n8n (visuel) + LangGraph (Python)    │
├──────────────────────────────────────────────────────────────────┤
│  COUCHE 2 – COGNITIVE       Ingestion │ Synthèse │ Gap Detection │
├──────────────────────────────────────────────────────────────────┤
│  COUCHE 3 – CONNAISSANCE    ChromaDB + sentence-transformers     │
├──────────────────────────────────────────────────────────────────┤
│  COUCHE 4 – ACTION          Fallback loops │ Human-in-the-Loop   │
└──────────────────────────────────────────────────────────────────┘

[PDFs] → Agent Ingestion → ChromaDB → Agent Synthèse (RAG)
       → Agent Gap Detection (CoT) → Validation humaine → Rapport final
```

## 🧰 Stack technique

| Composant | Technologie |
|-----------|-------------|
| LLM | Google Gemini (via `llm_adapter.py`, interchangeable) |
| Orchestration des agents | LangGraph (state machine) |
| Orchestration visuelle | n8n (`Source/n8n_workflow.json`) |
| Base vectorielle | ChromaDB |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local) |
| Extraction PDF | pdfplumber, pypdf |

## 📁 Structure

```
├── Source/
│   ├── 01_agent_ingestion.ipynb        # Agent 1 – pipeline RAG
│   ├── 02_agent_synthese.ipynb         # Agent 2 – synthèse thématique
│   ├── 03_agent_detection_gaps.ipynb   # Agent 3 – research gaps
│   ├── 04_orchestrateur_sma.ipynb      # Orchestrateur LangGraph
│   ├── run.py                          # Exécution du pipeline en ligne de commande
│   ├── llm_adapter.py                  # Adaptateur LLM (Gemini)
│   ├── n8n_workflow.json               # Export du workflow n8n
│   ├── pyproject.toml
│   └── .env.example
├── logs/                               # Exemples de sorties (synthèse, gaps)
├── Rapport/                            # Rapport académique complet
├── Learning Log/
└── LinkedIn/
```

## 🚀 Installation

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS : source .venv/bin/activate
pip install -e "Source/.[dev]"

cp Source/.env.example Source/.env   # puis ajoutez votre GEMINI_API_KEY
# Déposez vos PDF dans Source/papers/
jupyter lab
```

Ordre d'exécution : `01` → `02` → `03`, ou directement `04_orchestrateur_sma.ipynb` qui enchaîne tout le pipeline.

## 📊 Résultats

Des exemples de sorties sont disponibles dans [`logs/`](logs/) : rapport de gaps
([`gap_report.md`](logs/gap_report.md)), synthèse thématique et journal d'ingestion.
Le rapport complet se trouve dans [`Rapport/rapport_complet.md`](Rapport/rapport_complet.md).

## 👩‍💻 Auteure

**Maha El Yamni** — Étudiante ingénieure IA & Data Science, EMSI Rabat ·
[LinkedIn](https://www.linkedin.com/in/maha-el-yamni/) · [GitHub](https://github.com/maha-yam)
