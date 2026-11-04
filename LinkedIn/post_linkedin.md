# Post LinkedIn – SMA Revue de Littérature

---

## Texte du Post

**Titre suggéré :**  
J'ai construit un SMA Agentic qui lit des dizaines de papers scientifiques et trouve les lacunes de recherche en automatique – voici comment.

---

**Corps du post :**

La revue de littérature est l'une des étapes les plus chronophages de la recherche. Un doctorant passe en moyenne **3 à 6 mois** à lire, croiser et synthétiser des centaines d'articles avant même d'écrire sa première ligne de thèse.

Et si un Système Multi-Agents (SMA) pouvait faire ce travail en **quelques minutes** ?

C'est ce que nous avons construit dans le cadre de notre module **SMA – Agentic AI** à l'EMSI.

---

**Le problème réel :**
La revue de littérature n'est pas un résumé. C'est une **enquête scientifique** : identifier ce qui a été fait, comment, pourquoi ça a marché (ou pas), et surtout **ce qui n'a pas encore été exploré** — les fameux *Research Gaps*.

---

**Notre solution – 3 Agents, 4 Couches :**

**Agent 1 – Ingestion**  
Extrait et indexe automatiquement des papers PDF dans une base vectorielle **ChromaDB** via un pipeline RAG (chunking 800 tokens, overlap 150, embeddings `all-MiniLM-L6-v2`).

**Agent 2 – Synthèse**  
Interroge la base sémantiquement et utilise **Gemini** pour synthétiser le corpus par thèmes : méthodologies clés, résultats principaux, évolution temporelle.

**Agent 3 – Détection de Gaps**  
Applique un raisonnement **Chain-of-Thought** structuré pour identifier 4 types de lacunes : méthodologiques, domaine, temporelles, applicatives — chacune justifiée par des preuves du corpus.

---

**Stack technique :**
- **n8n** pour l'orchestration visuelle du workflow (Couche 1)
- **LangGraph** pour la state machine multi-agents avec Human-in-the-Loop (Couche 2)
- **ChromaDB + sentence-transformers** pour la base de connaissance vectorielle (Couche 3)
- **MCP Filesystem Server** pour l'accès standardisé aux fichiers (Couche 4)
- Fallback loops et gestion d'erreurs à chaque étape

---

**Ce que j'ai appris grâce à l'approche C2PCT :**

Deux bugs m'ont le plus appris :

1. **Boucle infinie LangGraph** : Mon agent critique rejetait toujours le rapport → boucle infinie. Solution : `recursion_limit=15` + condition d'arrêt basée sur `error_count >= 3`. Pattern reconnu : boucle `while(true)` sans `break` — exactement ce qu'on voit en algorithmique de base.

2. **Hallucination de gaps** : En Zero-Shot, le modèle produisait des gaps génériques valides pour n'importe quel domaine. Solution : Chain-of-Thought avec balises XML (`<analyse>...</analyse>`) pour forcer le raisonnement ancré dans le corpus réel.

La méthode **C2PCT** — documenter non pas ce que j'ai fait, mais **pourquoi** et **comment j'ai raisonné** — a transformé chaque bug en vraie leçon d'ingénierie.

---

**Résultats :**
- Corpus de 5 papers → synthèse en **3 minutes**
- **8 Research Gaps** identifiés, tous justifiés par des citations du corpus
- Rapport markdown généré automatiquement, prêt à intégrer dans une thèse

---

Ce n'est que le début. La prochaine étape : connecter le système à **Semantic Scholar API** pour ingérer automatiquement les 50 derniers papers d'un domaine.

Merci à nos professeurs **Pr. Hasnâa CHAABI** et **Pr. Nadia IDRISSI Zouggari** pour ce projet qui nous a forcés à construire de l'IA **vraiment autonome**.

---

[Captures d'écran : workflow n8n / graphe LangGraph / rapport de gaps généré]

---

**Hashtags :**
`#AI` `#AgenticAI` `#n8n` `#MCP` `#C2PCT` `#Engineering` `#EMSI` `#EngineersGiveBack` `#LangGraph` `#RAG` `#MultiAgentSystems` `#ResearchAI` `#Anthropic` `#Claude`
