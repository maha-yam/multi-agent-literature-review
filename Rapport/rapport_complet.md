# Rapport de Projet – SMA Agentic AI
## Sujet 8 : L'Assistant "Revue de Littérature" et Détection de Research Gaps

---

| | |
|---|---|
| **Module** | SMA – Agentic AI |
| **Classe** | 4AISDR |
| **Professeurs** | Pr. Hasnâa CHAABI & Pr. Nadia IDRISSI Zouggari |
| **Sujet** | N°8 – Assistant Revue de Littérature & Détection de Research Gaps |
| **Date** | Mai 2026 |

---

## Résumé Exécutif

Ce projet présente la conception et l'implémentation d'un **Système Multi-Agents (SMA) Agentic** dédié à l'automatisation de la revue de littérature scientifique et à la détection de lacunes de recherche (*Research Gaps*). Le système s'adresse aux doctorants et chercheurs qui consacrent en moyenne 3 à 6 mois à cette activité fastidieuse avant même de commencer à rédiger.

Le SMA intègre **3 agents cognitifs spécialisés** orchestrés via **LangGraph** et modélisés visuellement dans **n8n**, une base de connaissances vectorielle **ChromaDB**, un accès fichiers standardisé via le protocole **MCP**, et des mécanismes de robustesse incluant fallback loops et Human-in-the-Loop.

**Résultats clés :** Corpus de 5 papers → synthèse complète en 3 minutes, 8 research gaps identifiés et justifiés, rapport markdown généré automatiquement.

---

## Table des Matières

1. Introduction et Contexte
2. Architecture Globale du SMA
3. Engineering Workflow
   - 3.1 Logigramme du Flux de Données
   - 3.2 Pipeline RAG Détaillé
   - 3.3 Description des Agents
   - 3.4 Logs de Raisonnement
4. Gestion de la Context Window
5. Gestion des Fallbacks et Hallucinations
6. Points Techniques
7. Réponses aux Questions du Bac à Sable (5 Phases)
8. Conclusion et Perspectives
9. Références

---

## 1. Introduction et Contexte

### 1.1 Problématique

La revue de littérature est une étape fondamentale de toute recherche scientifique. Elle ne se limite pas à résumer des articles existants — elle consiste à **raconter une histoire scientifique** : tracer l'évolution d'un domaine, identifier les contradictions entre auteurs, les méthodologies dominantes, et surtout les **lacunes** (*Research Gaps*) qui justifient un nouveau travail de recherche.

En pratique, cette activité est :
- **Chronophage** : 3 à 6 mois pour un doctorant en début de thèse
- **Cognitive** : nécessite de croiser des dizaines à des centaines de sources
- **Non-automatisée** : aucun outil actuel ne va au-delà du simple résumé

### 1.2 Solution Proposée

Un **Système Multi-Agents (SMA) Agentic** qui automatise le pipeline complet :

```
[Corpus de PDFs] → Ingestion & Indexation → Synthèse RAG → Détection de Gaps → Rapport
```

### 1.3 Domaine d'Application

Le système est généraliste et applicable à tout domaine scientifique. Pour la démonstration, nous l'appliquons au domaine : **"NLP et Traitement Automatique de la Langue pour la recherche académique"**.

---

## 2. Architecture Globale du SMA

Le système respecte strictement les **4 couches** définies dans le cadre pédagogique.

### 2.1 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────┐
│  COUCHE 1 – ORCHESTRATION                                           │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐   │
│  │  n8n (Visuel)   │    │  LangGraph (State Machine Python)    │   │
│  │  Triggers       │    │  Nœuds, Edges Conditionnels, HITL    │   │
│  └─────────────────┘    └──────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│  COUCHE 2 – COGNITIVE (3 Agents Distincts)                          │
│  ┌───────────────┐ ┌─────────────────┐ ┌────────────────────────┐  │
│  │  Agent 1      │ │    Agent 2      │ │       Agent 3          │  │
│  │  Ingestion    │→│    Synthèse     │→│  Détection de Gaps     │  │
│  │  + RAG Build  │ │  Thématique RAG │ │  Chain-of-Thought      │  │
│  └───────────────┘ └─────────────────┘ └────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  COUCHE 3 – CONNAISSANCE                                            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  ChromaDB (Vector DB Persistante)                             │  │
│  │  Embeddings : sentence-transformers/all-MiniLM-L6-v2 (384d)  │  │
│  │  Collection : "literature_review"                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  COUCHE 4 – ACTION & RÉSILIENCE                                     │
│  ┌──────────────┐ ┌────────────────┐ ┌──────────────────────────┐  │
│  │ MCP          │ │ Fallback Loop  │ │  Human-in-the-Loop       │  │
│  │ Filesystem   │ │ retry ≤ 3      │ │  Validation avant export │  │
│  └──────────────┘ └────────────────┘ └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Topologie du SMA

**Topologie choisie : Pipeline Séquentiel avec Boucle de Rétroaction**

La topologie est séquentielle (A → B → C) car chaque agent a besoin du résultat de l'agent précédent pour fonctionner. Elle n'est pas purement linéaire : elle intègre une boucle de rétroaction controlée (Human-in-the-Loop rejette → re-run Agent 3 avec contrainte ≤ 3 fois).

**Justification :** La topologie hiérarchique (Manager → Workers) aurait créé un Single Point of Failure au niveau du Manager. La topologie séquentielle est plus résiliente : si un agent échoue, le fallback peut relancer uniquement cet agent sans affecter les autres.

### 2.3 Stack Technologique

| Composant | Technologie | Version | Rôle |
|-----------|------------|---------|------|
| LLM | Claude Sonnet 4.5 | claude-sonnet-4-5 | Synthèse + Gaps |
| LLM Économique | Claude Haiku 4.5 | claude-haiku-4-5-20251001 | Tâches simples |
| Orchestration agents | LangGraph | ≥0.2.0 | State machine |
| Orchestration visuelle | n8n | Cloud/Docker | Workflow visuel |
| Vector DB | ChromaDB | ≥0.5.0 | Stockage embeddings |
| Embeddings | sentence-transformers | all-MiniLM-L6-v2 | Local, gratuit |
| PDF Extraction | pdfplumber | ≥0.11.0 | Extraction texte |
| Accès fichiers | MCP Filesystem | Standard MCP | Abstraction I/O |
| Configuration | python-dotenv | ≥1.0.0 | Gestion des clés |

---

## 3. Engineering Workflow

### 3.1 Logigramme du Flux de Données

```
                    ┌─────────────┐
                    │    START    │
                    │  (Trigger)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Agent 1    │
                    │  Ingestion  │
                    └──────┬──────┘
                           │
              ┌────────────▼───────────┐
              │  PDFs dans papers/     │
              │  ──────────────────    │
              │  pdfplumber extract    │
              │  ↓                     │
              │  RecursiveTextSplitter │
              │  chunk=800, overlap=150│
              │  ↓                     │
              │  SentenceTransformer   │
              │  all-MiniLM-L6-v2      │
              │  ↓                     │
              │  ChromaDB.add()        │
              └────────────┬───────────┘
                           │
              ┌────────────▼───────────┐
              │  Erreur PDF ?          │◄── Fallback: PyPDF2
              └────────┬───────────────┘
                       │ Non
                    ┌──▼──────┐
                    │ Agent 2  │
                    │ Synthèse │
                    └──┬───────┘
                       │
         ┌─────────────▼──────────────┐
         │  Pour chaque thème défini: │
         │  ChromaDB.query(theme, n=10)│
         │  ↓                         │
         │  Build RAG context          │
         │  ↓                         │
         │  Claude Sonnet 4.5:        │
         │  "Synthétise ces chunks"   │
         │  ↓                         │
         │  JSON: {themes, findings,  │
         │         methodologies}      │
         └─────────────┬──────────────┘
                       │
                    ┌──▼──────────┐
                    │   Agent 3   │
                    │ Gap Detection│
                    └──┬───────────┘
                       │
         ┌─────────────▼──────────────┐
         │  Input: synthesis JSON     │
         │  ↓                         │
         │  Claude Sonnet 4.5 CoT:   │
         │  <analyse>raisonnement</a> │
         │  <gaps>JSON structuré</g>  │
         │  ↓                         │
         │  Parse regex → gaps list   │
         │  ↓                         │
         │  Markdown report generated │
         └─────────────┬──────────────┘
                       │
         ┌─────────────▼──────────────┐
         │  Human-in-the-Loop         │
         │  Approuve ? ───Yes──► Export│
         │      │                     │
         │      No                    │
         │      ↓ (error_count < 3)   │
         │  Re-run Agent 3            │
         │      ↓ (error_count >= 3)  │
         │  Force Export              │
         └─────────────┬──────────────┘
                       │
                    ┌──▼──────┐
                    │  Export  │
                    │ rapport  │
                    └──┬───────┘
                       │
                    ┌──▼──┐
                    │ END  │
                    └──────┘
```

### 3.2 Pipeline RAG Détaillé

#### Étape 1 : Extraction (Agent 1)

**Algorithme :** `pdfplumber.open()` → `.extract_text()` page par page

**Gestion du contexte sémantique inter-pages :** Chaque chunk contient le métadonnée `page_number`. L'overlap de 150 tokens entre les chunks consécutifs garantit qu'une phrase commencée en fin d'un chunk se retrouve aussi au début du suivant, préservant la cohérence sémantique à la jonction.

```python
# Extraction avec fallback
try:
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([p.extract_text() or "" for p in pdf.pages])
except Exception:
    # Fallback : PyPDF2 moins précis mais plus robuste
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = "\n".join([p.extract_text() for p in reader.pages])
```

#### Étape 2 : Chunking

**Stratégie :** `RecursiveCharacterTextSplitter`

| Paramètre | Valeur | Justification |
|-----------|--------|---------------|
| `chunk_size` | 800 tokens | ≈ 1 paragraphe scientifique complet |
| `chunk_overlap` | 150 tokens | Préserve le contexte aux jonctions |
| `separators` | `["\n\n", "\n", ". ", " ", ""]` | Suit la structure naturelle des articles |
| `add_start_index` | True | Traçabilité de la position dans le document |

**Pourquoi 800 tokens et non 2000 ?** Le papier "Lost in the Middle" (Liu et al., 2023) démontre que les LLMs utilisent mieux l'information quand elle est dans les premiers ou derniers tokens du contexte. Des chunks de 2000 tokens noient l'information pertinente au milieu, réduisant la précision du RAG.

#### Étape 3 : Embedding

**Modèle :** `all-MiniLM-L6-v2` (sentence-transformers)
- Dimension des vecteurs : 384
- Avantage : local, gratuit, rapide (~10ms/chunk)
- Métrique de similarité : cosinus (`hnsw:space: cosine`)

#### Étape 4 : Stockage ChromaDB

**Configuration :**
```python
client = chromadb.PersistentClient(path="../chroma_db")
collection = client.get_or_create_collection(
    name="literature_review",
    embedding_function=SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2"),
    metadata={"hnsw:space": "cosine"}
)
```

**Vérification d'indexation :** Après ingestion, on exécute une requête de test avec un terme générique du domaine et on vérifie que les distances cosinus sont < 0.5 (haute similarité sémantique).

#### Étape 5 : Requête RAG (Agent 2)

Pour chaque thème de recherche :
1. `collection.query(query_texts=[theme], n_results=10)` → top-10 chunks
2. Construction du contexte RAG : concaténation des 10 chunks avec leurs sources
3. Appel Claude Sonnet 4.5 avec `max_tokens=2048`
4. Parse JSON de la réponse

### 3.3 Description des Agents

#### Agent 1 – Ingestion (Pipeline RAG Builder)

| Attribut | Valeur |
|----------|--------|
| **Rôle** | Transformer les PDFs bruts en une base de connaissance interrogeable |
| **Outils** | pdfplumber, RecursiveCharacterTextSplitter, SentenceTransformer, ChromaDB, MCP Filesystem Server |
| **Input** | Dossier `papers/` contenant des PDFs |
| **Output** | Collection ChromaDB peuplée + `logs/ingestion_log.json` |
| **System Prompt** | N/A (pas de LLM – pipeline déterministe) |
| **Mémoire** | ChromaDB (externe, persistante) |

#### Agent 2 – Synthèse Thématique

| Attribut | Valeur |
|----------|--------|
| **Rôle** | Synthétiser le corpus par thèmes et extraire les tendances |
| **Outils** | ChromaDB (query), Anthropic Claude Sonnet 4.5 |
| **Input** | Requêtes thématiques + chunks RAG |
| **Output** | `logs/synthesis_result.json` (structure: themes, methodologies, findings, temporal_evolution) |
| **System Prompt** | Expert en revue systématique de littérature, produit des synthèses structurées et objectives |
| **Context Window** | Limité à 10 chunks/thème × ~800 tokens = ~8000 tokens de contexte RAG |

**System Prompt Agent 2 :**
```
Tu es un expert en revue systématique de littérature scientifique.
Ta tâche : analyser les extraits fournis et synthétiser ce domaine de recherche.

Pour chaque ensemble d'extraits, tu dois identifier:
1. Les thèmes principaux et sous-thèmes
2. Les méthodologies dominantes avec leurs forces/limites
3. Les principaux résultats et consensus
4. L'évolution temporelle des approches

Réponds UNIQUEMENT en JSON valide avec la structure:
{
  "themes": [...],
  "key_methodologies": [...],
  "main_findings": [...],
  "temporal_evolution": "...",
  "key_authors_concepts": [...]
}
```

#### Agent 3 – Détection de Research Gaps

| Attribut | Valeur |
|----------|--------|
| **Rôle** | Identifier les lacunes non explorées dans la littérature |
| **Outils** | Anthropic Claude Sonnet 4.5 (Chain-of-Thought) |
| **Input** | `logs/synthesis_result.json` |
| **Output** | `logs/gaps_result.json` + `logs/gap_report.md` |
| **System Prompt** | Chercheur expert en analyse critique, identifie les angles morts de la recherche |
| **Technique** | Chain-of-Thought avec balises XML (`<analyse>`, `<gaps>`) |

**Types de gaps détectés :**
- **Gaps méthodologiques** : méthodes non appliquées au domaine
- **Gaps de domaine** : sous-domaines non couverts
- **Gaps temporels** : approches obsolètes non mises à jour
- **Gaps applicatifs** : théorie non transposée en pratique

### 3.4 Logs de Raisonnement

#### Log Agent 1 – Ingestion (Exemple)

```json
{
  "timestamp": "2026-05-15T10:23:41",
  "agent": "Agent Ingestion",
  "status": "completed",
  "papers_processed": 5,
  "total_chunks": 312,
  "collection_count": 312,
  "results": [
    {"paper_id": "attention_is_all_you_need", "chunks_created": 78, "status": "success"},
    {"paper_id": "bert_pre_training", "chunks_created": 64, "status": "success"},
    {"paper_id": "rag_paper_lewis2020", "chunks_created": 71, "status": "success"},
    {"paper_id": "llm_survey_2023", "chunks_created": 89, "status": "success"},
    {"paper_id": "chain_of_thought_wei2022", "chunks_created": 10, "status": "fallback_used",
     "note": "pdfplumber failed – PyPDF2 fallback activated"}
  ]
}
```

#### Log Agent 2 – Synthèse (Exemple extrait)

```json
{
  "timestamp": "2026-05-15T10:26:18",
  "agent": "Agent Synthèse",
  "theme_queried": "automated literature review methods",
  "chunks_retrieved": 10,
  "avg_similarity_score": 0.82,
  "synthesis": {
    "themes": ["Automated summarization", "Citation network analysis", "Semantic search"],
    "key_methodologies": ["Transformer-based extractive summarization", "Graph-based ranking (PageRank)", "RAG with vector databases"],
    "main_findings": ["Transformer models outperform older methods by 23% on ROUGE metrics", "Graph approaches capture citation influence but miss semantic content"],
    "temporal_evolution": "2017-2019: statistical methods → 2020-2022: BERT variants → 2023+: RAG + LLM agents",
    "key_authors_concepts": ["Attention mechanism (Vaswani 2017)", "BERT (Devlin 2019)", "RAG (Lewis 2020)"]
  },
  "tokens_input": 4821,
  "tokens_output": 412,
  "model": "claude-sonnet-4-5"
}
```

#### Log Agent 3 – Gap Detection (Exemple extrait)

```json
{
  "timestamp": "2026-05-15T10:29:05",
  "agent": "Agent Gap Detection",
  "model": "claude-sonnet-4-5",
  "cot_reasoning_tokens": 1847,
  "gaps_identified": 8,
  "research_gaps": [
    {
      "type": "methodological",
      "gap": "Aucune étude ne combine RAG multi-sources avec validation croisée automatique des claims",
      "justification": "Les papers analysés appliquent RAG sur corpus unique. Zero études sur la contradiction inter-sources.",
      "future_direction": "Développer un pipeline RAG avec mécanisme de consensus inter-sources (vote majoritaire des chunks)",
      "impact": "High"
    },
    {
      "type": "domain",
      "gap": "Absence d'évaluation sur des corpus non-anglophones",
      "justification": "100% des benchmarks utilisent des datasets en anglais (PubMed, arXiv).",
      "future_direction": "Benchmarks multilingues pour la revue de littérature automatisée",
      "impact": "High"
    }
  ]
}
```

---

## 4. Gestion de la Context Window

### 4.1 Problème : L'Explosion des Tokens

Dans un pipeline séquentiel naïf, chaque agent reçoit l'intégralité de ce que les agents précédents ont produit, ce qui conduit à une explosion exponentielle de la context window.

**Solution adoptée : Mémoire Externe via Fichiers JSON (MCP Filesystem)**

Plutôt que de faire circuler les données brutes dans le `AgentState` de LangGraph, chaque agent :
1. **Écrit** son résultat complet dans un fichier JSON via le MCP Filesystem Server
2. **Passe** au nœud suivant uniquement un **résumé compact** (≤ 500 tokens)

### 4.2 Stratégie de Compression du Contexte

| Transition | Données brutes | Ce qui circule dans LangGraph | Réduction |
|------------|---------------|-------------------------------|-----------|
| Agent 1 → Agent 2 | 312 chunks (≈ 250K tokens) | Résumé d'ingestion (50 tokens) | 99.98% |
| Agent 2 → Agent 3 | Synthèse complète (≈ 3000 tokens) | JSON synthèse compressé (800 tokens) | 73% |
| Agent 3 → Humain | Rapport complet (≈ 2000 tokens) | Résumé des 3 gaps prioritaires (300 tokens) | 85% |

### 4.3 Implémentation

```python
# Dans chaque nœud LangGraph – pattern standard
def node_synthesis(state: AgentState) -> AgentState:
    # 1. Charger les données via MCP (pas dans le state)
    synthesis = run_synthesis_agent()
    
    # 2. Sauvegarder le résultat complet via MCP
    mcp_server.write_file("logs/synthesis_result.json", json.dumps(synthesis))
    
    # 3. Ne stocker que le résumé dans le state LangGraph
    summary = {
        "themes_count": len(synthesis["themes"]),
        "status": "completed",
        "top_theme": synthesis["themes"][0] if synthesis["themes"] else ""
    }
    
    return {**state, "synthesis_result": summary}
```

---

## 5. Gestion des Fallbacks et Hallucinations

### 5.1 Fallback Agent 1 – Extraction PDF

Si `pdfplumber` échoue (PDF corrompu, PDF scanné sans OCR) :
- **Fallback 1** : Tentative avec `PyPDF2` (plus tolérant aux formats non-standard)
- **Fallback 2** : Si toujours échec, le paper est mis en `quarantine/` avec un log d'erreur et l'ingestion continue pour les autres papers
- **Résultat** : le SMA n'est jamais bloqué par un seul PDF défaillant

### 5.2 Fallback Agent 2 – API Claude

Si l'API Anthropic retourne une erreur (rate limit, timeout) :
- **Retry** : 3 tentatives avec backoff exponentiel (1s, 2s, 4s)
- **Fallback** : Retourner une synthèse partielle avec les chunks bruts (sans traitement LLM)
- Le workflow continue avec une synthèse dégradée plutôt que de s'arrêter

```python
for attempt in range(3):
    try:
        response = client.messages.create(...)
        break
    except anthropic.RateLimitError:
        time.sleep(2 ** attempt)
    except Exception as e:
        if attempt == 2:
            return {"status": "fallback", "raw_chunks": chunks, "error": str(e)}
```

### 5.3 Anti-Hallucination Agent 3 – Chain-of-Thought

**Problème :** En Zero-Shot, Claude produit des gaps génériques non ancrés dans le corpus (ex: *"Plus d'études longitudinales sont nécessaires"* — vrai pour tout domaine).

**Solution : Chain-of-Thought avec Balises XML**

```
Prompt structuré :
"Avant de lister les gaps, écris ton raisonnement complet dans <analyse>...</analyse>.
Dans cette analyse, cite EXPLICITEMENT les papers et méthodes du corpus qui couvrent
chaque aspect. Ce n'est qu'après avoir identifié ce qui EST couvert que tu peux 
identifier ce qui NE L'EST PAS.
Ensuite, liste uniquement les gaps PROUVÉS dans <gaps>...</gaps> en JSON."
```

**Validation côté Python :**
```python
import re
analyse = re.search(r"<analyse>(.*?)</analyse>", response, re.DOTALL)
gaps_json = re.search(r"<gaps>(.*?)</gaps>", response, re.DOTALL)

# Vérification : chaque gap doit mentionner au moins 1 source du corpus
for gap in parsed_gaps:
    if not any(paper in gap["justification"] for paper in known_paper_ids):
        gap["confidence"] = "low"  # marqué comme potentiellement halluciné
```

### 5.4 Self-Correction Loop

Si Claude retourne un JSON invalide (format `<gaps>` malformé) :
- **Détection** : `json.JSONDecodeError` lors du parsing
- **Correction** : Re-prompt automatique avec *"Ta réponse précédente n'était pas un JSON valide. Voici l'erreur : {error}. Réessaie en fournissant UNIQUEMENT du JSON valide dans la balise <gaps>."*
- **Limite** : Maximum 2 re-tentatives (compteur `correction_count`)

---

## 6. Points Techniques

### 6.1 Pourquoi 3 Agents et Non 1 Seul Prompt ?

**Arguments pour 3 agents :**

| Critère | 1 Prompt Massif | 3 Agents Spécialisés |
|---------|-----------------|----------------------|
| **Context Window** | Dépasse facilement 100K tokens | Chaque agent ≤ 10K tokens |
| **Hallucination** | Élevé (trop d'info à traiter) | Réduit (focus sur 1 tâche) |
| **Débogage** | Impossible d'isoler l'erreur | On sait exactement quel agent a échoué |
| **Coût** | 1 gros appel coûteux | 2 × Haiku (Ingestion/résumé) + 1 × Sonnet (gaps) |
| **Évolutivité** | Refactorer tout pour chaque changement | Remplacer 1 agent sans toucher aux autres |
| **Testabilité** | Test unitaire impossible | Chaque agent testable isolément |

**Exemple concret de justification :** Si on donne à un seul prompt la tâche "lis 312 chunks, synthétise et trouve les gaps", Claude reçoit ≈ 250K tokens de contexte. Le paper "Lost in the Middle" démontre que la performance des LLMs chute drastiquement pour les informations situées au milieu d'un long contexte. Les 3 agents permettent de travailler avec des contextes courts et précis à chaque étape.

### 6.2 Preuves d'Autonomie du Tool Usage

**Agent 1 – Tool Usage par Raisonnement :**
L'agent utilise le `MCPFilesystemServer` de manière autonome pour lister les PDFs disponibles :
```python
# L'agent décide seul quels fichiers traiter – pas de hardcoding
pdf_files = mcp_server.list_directory("papers")
for pdf in pdf_files:
    if pdf.endswith(".pdf"):
        ingest_paper(pdf, mcp_server)
```

**Agent 2 – Tool Usage RAG autonome :**
L'agent décide seul quelle query sémantique envoyer à ChromaDB en fonction du thème. Il n'y a pas de requête SQL fixe — c'est une recherche sémantique qui dépend du raisonnement de l'agent sur ce qu'il cherche.

**Agent 3 – Raisonnement propre :**
Le CoT dans `<analyse>` est entièrement généré par le raisonnement du modèle. Le JSON final dans `<gaps>` est une **décision** de l'agent, pas une transformation déterministe d'un template.

**Note d'honnêteté :** L'orchestration séquentielle (Agent 1 → 2 → 3) est forcée par le workflow LangGraph. Cependant, à l'intérieur de chaque agent, l'utilisation des outils (ChromaDB, MCP, formatage JSON) est bien le fruit du raisonnement autonome du LLM.

### 6.3 Analyse de Coût (Token Budget)

**Pour 5 papers (~312 chunks) :**

| Opération | Modèle | Tokens Input | Tokens Output | Coût estimé |
|-----------|--------|-------------|--------------|-------------|
| Agent 1 | Aucun LLM | 0 | 0 | $0 |
| Agent 2 : 5 thèmes × 10 chunks × 800 tokens | claude-sonnet-4-5 | 40 000 | 2 500 | ~$0.16 |
| Agent 3 : Synthèse + CoT | claude-sonnet-4-5 | 3 000 | 2 000 | ~$0.04 |
| Fallback/retry (estimé) | claude-haiku-4-5 | 2 000 | 500 | ~$0.001 |
| **TOTAL** | | **~47 000** | **~5 000** | **~$0.20** |

**Tarifs utilisés :** claude-sonnet-4-5 : $3/M tokens input, $15/M tokens output.

**Optimisation appliquée :** Embeddings `all-MiniLM-L6-v2` en local → $0 (vs $0.02/1000 tokens pour les APIs d'embedding commerciales). Pour 312 chunks, économie ≈ $0.006.

**Stratégie anti-explosion :** Maximum 10 chunks/thème pour Agent 2 (configuré dans `n_results=10`). Sans cette limite, l'agent pourrait recevoir 312 chunks × 800 tokens = 250K tokens → coût ≈ $0.75 au lieu de $0.20.

---

## 7. Réponses aux Questions du Bac à Sable

### Phase 1 : Modélisation Conceptuelle

**Q: Topologie du SMA ?**  
Architecture pipeline séquentielle avec boucle de rétroaction contrôlée. Justification : les dépendances de données imposent la séquence (RAG doit être construit avant d'être interrogé). La boucle Human-in-the-Loop ajoute de la robustesse sans complexifier la topologie principale.

**Q: Single Point of Failure ?**  
L'API Anthropic (Agents 2 et 3). Sécurisé par : retry avec backoff exponentiel + fallback vers résultats partiels + `error_count` limité à 3 dans LangGraph pour éviter les boucles infinies.

**Q: Si on supprime un agent ?**  
Si on supprime Agent 2 (Synthèse), Agent 3 devrait traiter directement les 312 chunks bruts, dépassant la context window et augmentant le risque d'hallucination. La synthèse est l'agent le plus critique à préserver. Agent 1 pourrait être simplifié (ingestion directe dans un fichier texte), mais la perte de qualité RAG serait significative.

### Phase 2 : Pipeline RAG

**Q: Stratégie de chunking ?**  
`RecursiveCharacterTextSplitter`, chunk_size=800, overlap=150. Justification : préserve les paragraphes complets (grain sémantique naturel des articles scientifiques) tout en permettant une recherche précise.

**Q: Perte de contexte sémantique aux jonctions ?**  
Gérée par l'overlap de 150 tokens : chaque chunk partage ses 150 derniers tokens avec le début du chunk suivant. De plus, chaque chunk stocke son `start_index` et son numéro de page, permettant de retrouver le contexte complet si nécessaire.

**Q: Vérification que les données sont indexées ?**  
Post-ingestion : `collection.count()` doit correspondre au nombre de chunks calculé. Test sémantique : requête avec terme générique du domaine, vérification que `distances[0] < 0.5`.

### Phase 3 : Prompt Engineering & Outillage

**Q: Tests unitaires par agent ?**  
Chaque notebook peut être exécuté indépendamment. Agent 2 peut être testé avec une mini-collection ChromaDB de 5 chunks de test. Agent 3 peut être testé avec un fichier `synthesis_result_test.json` fixe.

**Q: Isolation des défaillances ?**  
- Erreur Agent 1 : log JSON avec `status: "fallback_used"` → problème d'extraction PDF
- Erreur Agent 2 : `avg_similarity_score < 0.3` → problème d'indexation ou de requête
- Erreur Agent 3 : gaps avec `confidence: "low"` → hallucination détectée → re-prompt

### Phase 4 : Orchestration et MCP

**Q: Comment l'information circule ?**  
Via l'`AgentState` LangGraph pour les métadonnées légères (statuts, compteurs) et via les fichiers JSON du MCP Filesystem pour les données lourdes (synthèse complète, liste des gaps).

**Q: Intégration MCP ?**  
Classe `MCPFilesystemServer` conforme au standard MCP : méthodes `read_file()`, `write_file()`, `list_directory()`. Cela abstrait complètement le système de fichiers sous-jacent. En production, on pourrait remplacer le backend par un S3, un SharePoint, ou une BDD SQL sans changer une ligne du code agent.

**Q: En quoi MCP améliore la sécurité vs hardcoding ?**  
Sans MCP, les paths de fichiers sont hardcodés dans le code agent — changer l'infrastructure nécessite de modifier le code. Avec MCP, les agents ne connaissent que les méthodes abstraites (`read_file`, `write_file`). Le MCP Server gère la résolution des paths, les permissions, et les logs d'accès. En production, le MCP Server peut ajouter authentification et audit trail sans modifier les agents.

### Phase 5 : Gestion des Erreurs

**Q: Si l'API LLM ne répond pas ?**  
3 retries avec backoff (1s → 2s → 4s). Si toujours échec : retour d'une réponse dégradée (synthèse brute des chunks sans traitement LLM) avec flag `status: "degraded"`.

**Q: Si RAG ne trouve pas l'information ?**  
Si `distances[0] > 0.7` (faible similarité), l'agent retourne `{"status": "no_relevant_chunks", "suggestion": "Augmenter le corpus ou reformuler la requête"}` plutôt que d'halluciner une réponse.

**Q: Self-Correction Loop JSON invalide ?**  
Détection par `json.JSONDecodeError` → re-prompt avec l'erreur exacte → maximum 2 corrections → si toujours invalide : extraction regex manuelle du JSON le plus probable.

---

## 8. Conclusion et Perspectives

Ce projet démontre la viabilité d'une approche multi-agents pour automatiser la revue de littérature scientifique. Les 3 agents spécialisés permettent de décomposer un problème cognitivement complexe en étapes distinctes, testables, et robustes.

**Limites actuelles :**
- La qualité des embeddings dépend du modèle local (`all-MiniLM-L6-v2`) qui n'est pas spécialisé pour les textes scientifiques
- Le Human-in-the-Loop est synchrone (`input()`) — impossible à déployer en production sans modification
- Pas de gestion des références bibliographiques (numéros de citations, DOIs)

**Perspectives d'amélioration :**
1. Intégration de l'API Semantic Scholar pour ingestion automatique de papers par DOI
2. Human-in-the-Loop asynchrone via n8n + Gmail (envoyer le rapport, attendre la réponse email)
3. Génération automatique de la section "Revue de Littérature" au format LaTeX
4. Modèle d'embedding spécialisé scientifique (ex: SciBERT, SPECTER2)

---

## 9. Références

1. Vaswani, A. et al. (2017). *Attention Is All You Need*. NeurIPS.
2. Devlin, J. et al. (2019). *BERT: Pre-training of Deep Bidirectional Transformers*. NAACL.
3. Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS.
4. Wei, J. et al. (2022). *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*. NeurIPS.
5. Liu, N. et al. (2023). *Lost in the Middle: How Language Models Use Long Contexts*. TACL.
6. Yao, S. et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR.
7. LangGraph Documentation. (2024). https://langchain-ai.github.io/langgraph/
8. Anthropic. (2024). *Claude API Documentation*. https://docs.anthropic.com/
9. ChromaDB Documentation. (2024). https://docs.trychroma.com/
10. Model Context Protocol. (2024). https://modelcontextprotocol.io/
11. CHAABI, H. (2024). *C2PCT: A Computational Thinking Framework*. Zenodo. https://zenodo.org/records/12793519
12. n8n Documentation. (2024). https://docs.n8n.io/
