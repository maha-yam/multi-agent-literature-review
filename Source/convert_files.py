"""
Script de conversion des fichiers du projet :
  - learning_log.md  →  Learning Log/learning_log.xlsx
  - rapport_complet.md → Rapport/rapport_complet.docx
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────
# 1. LEARNING LOG  →  Excel (.xlsx)
# ─────────────────────────────────────────────

def build_learning_log_excel():
    try:
        import openpyxl
        from openpyxl.styles import (
            PatternFill, Font, Alignment, Border, Side
        )
    except ImportError:
        print("openpyxl manquant – installe avec : pip install openpyxl")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Learning Log"

    # Couleurs
    DARK_BLUE   = "1F3864"
    MID_BLUE    = "2E75B6"
    LIGHT_BLUE  = "BDD7EE"
    LIGHT_GREEN = "E2EFDA"
    YELLOW      = "FFF2CC"
    ORANGE      = "FCE4D6"
    WHITE       = "FFFFFF"
    GREY        = "F2F2F2"

    def fill(hex_color):
        return PatternFill("solid", fgColor=hex_color)

    def border():
        thin = Side(style="thin", color="000000")
        return Border(left=thin, right=thin, top=thin, bottom=thin)

    def header_font(color="FFFFFF", bold=True, size=11):
        return Font(bold=bold, color=color, size=size)

    def cell_font(bold=False, size=10):
        return Font(bold=bold, size=size)

    def wrap():
        return Alignment(wrap_text=True, vertical="top")

    # Largeurs de colonnes
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 80

    # ── Titre principal ──
    ws.merge_cells("A1:B1")
    ws["A1"] = "Learning Log – SMA : Revue de Littérature & Détection de Research Gaps"
    ws["A1"].fill = fill(DARK_BLUE)
    ws["A1"].font = Font(bold=True, color="FFFFFF", size=14)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 40

    ws.merge_cells("A2:B2")
    ws["A2"] = "Méthode C²PCT  |  Pr. Hasnâa CHAABI  |  Module SMA – Agentic AI  |  4AISDR"
    ws["A2"].fill = fill(MID_BLUE)
    ws["A2"].font = Font(bold=True, color="FFFFFF", size=11)
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    entries = [
        {
            "title": "Entrée 1 – Architecture du Système Multi-Agents",
            "color": LIGHT_BLUE,
            "rows": [
                ("(C) 1. Apprentissage exploré",
                 "Conception d'une architecture SMA à 4 couches pour la revue de littérature automatisée. "
                 "Choix entre architecture hiérarchique (Manager → Workers) vs séquentielle (pipeline A → B → C)."),
                ("(C) 2. Difficulté / Point aveugle",
                 "Je ne savais pas quelle topologie choisir. Une architecture hiérarchique créait un Single Point of Failure : "
                 "si le manager plante, tout le système s'arrête. L'architecture séquentielle semblait 'trop simple' pour un SMA."),
                ("(P) Décomposition",
                 "1) Définir le rôle de chaque agent indépendamment.\n"
                 "2) Identifier les données qui passent d'un agent à l'autre.\n"
                 "3) Choisir la topologie en fonction des dépendances de données."),
                ("(P) Patterns",
                 "Pattern 'Pipeline de traitement ETL' (Extract-Transform-Load). "
                 "Chaque étape produit un artefact consommé par la suivante."),
                ("(P) Abstraction",
                 "Le bruit : les débats philosophiques sur le meilleur SMA. "
                 "La donnée utile : l'ingestion doit précéder la synthèse qui doit précéder la détection."),
                ("(CT) 3. Hypothèse",
                 "Une architecture séquentielle pipeline (A → B → C) est la plus adaptée parce que chaque agent "
                 "a besoin du résultat de l'agent précédent. Simple à déboguer et à tester agent par agent."),
                ("(CT) 4. Stratégie adoptée",
                 "Architecture séquentielle avec LangGraph comme orchestrateur. "
                 "LangGraph permet de définir un graphe orienté avec conditional edges pour le fallback et Human-in-the-Loop."),
                ("(CT) 5. Amélioration adoptée",
                 "Première version : nœud Manager qui appelait les 3 agents (accumulation du contexte = 3× les tokens).\n"
                 "Solution : chaque agent écrit son résultat dans un fichier JSON externe (MCP Filesystem) → résout l'explosion de la Context Window."),
                ("(C) 6. Références",
                 "• LangGraph Docs : https://langchain-ai.github.io/langgraph/\n"
                 "• ReAct (Yao et al., 2023)\n"
                 "• MCP Standard : https://modelcontextprotocol.io/"),
                ("(C) 7. Questions restantes",
                 "Si le système doit traiter 500 papers au lieu de 10, l'ingestion devient un goulot d'étranglement. "
                 "Comment LangGraph gère-t-il les nœuds parallèles (Send API) ?"),
            ],
        },
        {
            "title": "Entrée 2 – Pipeline RAG : Stratégie de Chunking",
            "color": LIGHT_GREEN,
            "rows": [
                ("(C) 1. Apprentissage exploré",
                 "Construction du pipeline RAG : extraction → chunking → embedding → stockage ChromaDB."),
                ("(C) 2. Difficulté / Point aveugle",
                 "chunk_size=2000 → résultats trop longs, peu précis. chunk_size=200 → perte de contexte, phrases coupées."),
                ("(P) Décomposition",
                 "1) Choisir la taille de chunk.\n2) Choisir l'overlap.\n3) Choisir les séparateurs.\n4) Valider la cohérence des embeddings."),
                ("(P) Patterns",
                 "'Granularity tradeoff' en indexation BDD : trop large = peu précis, trop petit = perte de contexte."),
                ("(P) Abstraction",
                 "La donnée utile : un paragraphe scientifique complet ≈ 4-6 phrases ≈ 600-1000 tokens."),
                ("(CT) 3. Hypothèse",
                 "chunk_size=800 avec chunk_overlap=150 et séparateurs [\"\\n\\n\", \"\\n\", \". \"] devrait préserver les paragraphes complets."),
                ("(CT) 4. Stratégie adoptée",
                 "RecursiveCharacterTextSplitter (LangChain) : chunk_size=800, chunk_overlap=150.\n"
                 "Découpage récursif respectant la structure naturelle des articles scientifiques."),
                ("(CT) 5. Amélioration adoptée",
                 "Ajout de add_start_index=True pour traçabilité.\n"
                 "Métadonnées : numéro de page + nom du paper dans chaque chunk."),
                ("(C) 6. Références",
                 "• LangChain Text Splitters : https://python.langchain.com/docs/how_to/recursive_text_splitter/\n"
                 "• 'Lost in the Middle' (Liu et al., 2023)\n"
                 "• ChromaDB Best Practices : https://docs.trychroma.com/"),
                ("(C) 7. Questions restantes",
                 "Le modèle all-MiniLM-L6-v2 (384d) est-il suffisant pour des textes scientifiques spécialisés ? "
                 "Un modèle comme voyage-3 d'Anthropic serait-il plus précis ?"),
            ],
        },
        {
            "title": "Entrée 3 – LangGraph : Résoudre la Boucle Infinie",
            "color": YELLOW,
            "rows": [
                ("(C) 1. Apprentissage exploré",
                 "Implémentation du nœud Human-in-the-Loop dans LangGraph. "
                 "Objectif : validation humaine avant l'export + re-run si rejet."),
                ("(C) 2. Difficulté / Point aveugle",
                 "Erreur : GraphRecursionError: Recursion limit of 25 reached.\n"
                 "L'humain rejetait → système relançait → rapport similaire → rejet → boucle infinie."),
                ("(P) Décomposition",
                 "1) La génération du rapport.\n2) L'évaluation par l'humain.\n3) La condition d'arrêt."),
                ("(P) Patterns",
                 "Identique à une boucle while(true) sans break. L'agent critique ne sait pas quand s'arrêter."),
                ("(P) Abstraction",
                 "Donnée utile : (human_approved: bool, error_count: int). Condition d'arrêt = error_count >= 3."),
                ("(CT) 3. Hypothèse",
                 "Feedback structuré (approuver/rejeter + raison) + arrêt forcé après 3 rejets avec export partiel."),
                ("(CT) 4. Stratégie adoptée",
                 "Conditional edge LangGraph :\n"
                 "if human_approved → 'export'\n"
                 "elif error_count >= 3 → END\n"
                 "else → 'gap_detection'\n"
                 "+ recursion_limit=15 dans workflow.compile()"),
                ("(CT) 5. Amélioration adoptée",
                 "recursion_limit=10 bloquait les cas normaux (3 nœuds = 3 steps déjà).\n"
                 "Ajusté à recursion_limit=15 + log clair : '⚠️ Limite d'itérations atteinte – export du meilleur résultat disponible'."),
                ("(C) 6. Références",
                 "• LangGraph Conditional Edges\n• LangGraph Human-in-the-Loop\n• recursion_limit dans CompiledGraph.invoke()"),
                ("(C) 7. Questions restantes",
                 "En production, comment implémenter un HITL asynchrone avec n8n ?\n"
                 "(envoyer un email via Gmail, attendre la réponse, reprendre le workflow)"),
            ],
        },
        {
            "title": "Entrée 4 – Prompt Engineering : Chain-of-Thought pour la Détection de Gaps",
            "color": ORANGE,
            "rows": [
                ("(C) 1. Apprentissage exploré",
                 "Rédaction du system prompt de l'Agent Gap Detection.\n"
                 "Objectif : forcer Claude à raisonner méthodiquement avant de produire une liste de gaps."),
                ("(C) 2. Difficulté / Point aveugle",
                 "Avec un prompt Zero-Shot simple, Claude produisait des gaps vagues :\n"
                 "'Il manque des études longitudinales' → vrai pour n'importe quel domaine, aucune valeur spécifique."),
                ("(P) Décomposition",
                 "1) Forcer l'identification des travaux existants.\n"
                 "2) Forcer la comparaison avec ce qui manque.\n"
                 "3) Forcer la justification avec des références du corpus.\n"
                 "4) Forcer un format structuré."),
                ("(P) Patterns",
                 "Le LLM 'prédit' une réponse plausible sans vraiment raisonner.\n"
                 "Solution : Chain-of-Thought avec balises XML pour forcer le raisonnement intermédiaire."),
                ("(P) Abstraction",
                 "Donnée utile = gaps spécifiques au corpus, justifiés par des citations.\n"
                 "Bruit = tout ce que Claude peut 'inventer' sans ancrage dans le corpus."),
                ("(CT) 3. Hypothèse",
                 "En forçant Claude à écrire dans <analyse>...</analyse> avant <gaps>...</gaps>, "
                 "les tokens générés servent de 'mémoire de travail' et ancrent la réponse finale."),
                ("(CT) 4. Stratégie adoptée",
                 "System prompt en 4 étapes :\n"
                 "① Lire la synthèse → identifier les domaines couverts\n"
                 "② Pour chaque type de gap → chercher des preuves dans la synthèse\n"
                 "③ Raisonnement complet dans <analyse>\n"
                 "④ Gaps prouvés en JSON dans <gaps>"),
                ("(CT) 5. Amélioration adoptée",
                 "Problème : <analyse> parfois si longue que Claude 'oubliait' le format JSON.\n"
                 "Solution : instruction explicite + parsing regex côté Python pour extraire les deux sections indépendamment."),
                ("(C) 6. Références",
                 "• Wei et al. (2022) – Chain-of-Thought Prompting. NeurIPS.\n"
                 "• Anthropic Prompt Engineering Guide\n"
                 "• XML Tags in Claude prompts"),
                ("(C) 7. Questions restantes",
                 "Le CoT dans <analyse> coûte ~2000 tokens supplémentaires par appel.\n"
                 "Vaut-il mieux utiliser le mode Extended Thinking de Claude ?"),
            ],
        },
    ]

    current_row = 3

    for entry in entries:
        # Titre de l'entrée
        ws.merge_cells(f"A{current_row}:B{current_row}")
        ws[f"A{current_row}"] = entry["title"]
        ws[f"A{current_row}"].fill = fill(MID_BLUE)
        ws[f"A{current_row}"].font = Font(bold=True, color="FFFFFF", size=11)
        ws[f"A{current_row}"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.row_dimensions[current_row].height = 22
        current_row += 1

        # En-têtes des colonnes
        for col, label in [("A", "Section C²PCT"), ("B", "Contenu")]:
            ws[f"{col}{current_row}"] = label
            ws[f"{col}{current_row}"].fill = fill(DARK_BLUE)
            ws[f"{col}{current_row}"].font = header_font()
            ws[f"{col}{current_row}"].alignment = Alignment(horizontal="center", vertical="center")
            ws[f"{col}{current_row}"].border = border()
        ws.row_dimensions[current_row].height = 18
        current_row += 1

        # Lignes de données
        for i, (section, content) in enumerate(entry["rows"]):
            bg = entry["color"] if i % 2 == 0 else GREY
            for col, val in [("A", section), ("B", content)]:
                c = ws[f"{col}{current_row}"]
                c.value = val
                c.fill = fill(bg)
                c.font = cell_font(bold=(col == "A"))
                c.alignment = wrap()
                c.border = border()
            line_count = max(content.count("\n") + 1, 2)
            ws.row_dimensions[current_row].height = max(30, line_count * 15 + 10)
            current_row += 1

        # Séparateur
        current_row += 1

    # Citation finale
    ws.merge_cells(f"A{current_row}:B{current_row}")
    ws[f"A{current_row}"] = (
        '"Ce n\'est pas l\'activité qui fait apprendre, mais la réflexion sur l\'activité."'
        "  — Dr. Hasnâa CHAABI"
    )
    ws[f"A{current_row}"].fill = fill(DARK_BLUE)
    ws[f"A{current_row}"].font = Font(italic=True, bold=True, color="FFFFFF", size=10)
    ws[f"A{current_row}"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[current_row].height = 30

    out_path = os.path.join(BASE, "Learning Log", "learning_log.xlsx")
    wb.save(out_path)
    print(f"✓ Excel créé : {out_path}")


# ─────────────────────────────────────────────
# 2. RAPPORT  →  Word (.docx)
# ─────────────────────────────────────────────

def build_rapport_docx():
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        print("python-docx manquant – installe avec : pip install python-docx")
        print("Puis relance : python Source/convert_files.py")
        return

    md_path = os.path.join(BASE, "Rapport", "rapport_complet.md")
    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    doc = Document()

    # Marges
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3)
        section.right_margin  = Cm(2.5)

    # Couleur principale
    BLUE = RGBColor(0x1F, 0x38, 0x64)

    in_code_block = False
    code_lines = []

    def flush_code(code_lines):
        code_text = "".join(code_lines).strip()
        if not code_text:
            return
        p = doc.add_paragraph()
        p.style = doc.styles["No Spacing"]
        run = p.add_run(code_text)
        run.font.name = "Courier New"
        run.font.size = Pt(8)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        # Fond gris simulé via indentation
        p.paragraph_format.left_indent = Cm(0.5)

    for raw in lines:
        line = raw.rstrip("\n")

        # Blocs de code
        if line.startswith("```"):
            if in_code_block:
                flush_code(code_lines)
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(raw)
            continue

        # Séparateurs horizontaux
        if line.strip() in ("---", "==="):
            doc.add_paragraph("─" * 60)
            continue

        # Titres
        if line.startswith("#### "):
            p = doc.add_heading(line[5:], level=4)
        elif line.startswith("### "):
            p = doc.add_heading(line[4:], level=3)
        elif line.startswith("## "):
            p = doc.add_heading(line[3:], level=2)
        elif line.startswith("# "):
            p = doc.add_heading(line[2:], level=1)
            for run in p.runs:
                run.font.color.rgb = BLUE

        # Lignes de tableau (simplifié)
        elif line.startswith("|") and not line.startswith("|---") and not line.startswith("|:--"):
            cells = [c.strip() for c in line.split("|") if c.strip()]
            p = doc.add_paragraph("  |  ".join(cells))
            p.style = doc.styles["No Spacing"]
            p.paragraph_format.left_indent = Cm(0.5)

        # Listes
        elif line.startswith("- "):
            p = doc.add_paragraph(line[2:], style="List Bullet")
        elif line.startswith("* "):
            p = doc.add_paragraph(line[2:], style="List Bullet")
        elif len(line) > 2 and line[0].isdigit() and line[1] in (". ", ") "):
            p = doc.add_paragraph(line[3:], style="List Number")

        # Ligne vide
        elif line.strip() == "":
            doc.add_paragraph("")

        # Paragraphe normal (gestion bold/italic basique)
        else:
            p = doc.add_paragraph()
            text = line.strip()
            # Nettoyage simple des marqueurs markdown inline
            import re
            parts = re.split(r"(\*\*.*?\*\*|\*.*?\*|`.*?`)", text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = p.add_run(part[2:-2])
                    run.bold = True
                elif part.startswith("*") and part.endswith("*"):
                    run = p.add_run(part[1:-1])
                    run.italic = True
                elif part.startswith("`") and part.endswith("`"):
                    run = p.add_run(part[1:-1])
                    run.font.name = "Courier New"
                    run.font.size = Pt(9)
                else:
                    p.add_run(part)

    out_path = os.path.join(BASE, "Rapport", "rapport_complet.docx")
    doc.save(out_path)
    print(f"✓ Word créé : {out_path}")


# ─────────────────────────────────────────────
if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=== Conversion des fichiers du projet ===\n")
    print("1. Learning Log -> Excel...")
    build_learning_log_excel()
    print("\n2. Rapport -> Word (.docx)...")
    build_rapport_docx()
    print("\n=== Termine ===")
