"""
Pipeline SMA - Revue de Litterature
Agents : Ingestion -> Synthese -> Detection de Gaps -> Rapport

Usage :
    cd Source
    python run.py
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import chromadb
import pdfplumber
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter

import llm_adapter as anthropic
from llm_adapter import GeminiEmbeddingFunction

# Chemins
BASE_DIR       = Path(__file__).parent
PAPERS_DIR     = BASE_DIR / "papers"
CHROMA_DB_PATH = str(BASE_DIR.parent / "chroma_db")
LOGS_DIR       = BASE_DIR.parent / "logs"
RAPPORT_DIR    = BASE_DIR.parent / "Rapport"

COLLECTION_NAME = "literature_review"
CHUNK_SIZE      = 800
CHUNK_OVERLAP   = 150
BATCH_SIZE      = 50
LLM_MODEL       = "claude-sonnet-4-5"
N_RESULTS       = 10

RESEARCH_THEMES = [
    "automated literature review methods",
    "research gap detection",
    "NLP for scientific text",
    "knowledge extraction from papers",
    "multi-agent systems for research",
]

SYNTHESIS_PROMPT = (
    "You are a scientific literature analyst. Analyze the provided excerpts and synthesize them. "
    "Return ONLY valid JSON with keys: themes, key_methodologies, main_findings, "
    "temporal_evolution, key_authors_concepts."
)

GAP_PROMPT = (
    "You are an expert researcher identifying research gaps. "
    "Reason step-by-step inside <analysis> tags, then output JSON inside <gaps> tags with keys: "
    "research_gaps (list: gap_id, gap_type, title, description, evidence, justification, "
    "suggested_research_direction, estimated_impact, feasibility, related_themes), "
    "priority_ranking, cross_cutting_observations, recommended_next_steps."
)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init():
    load_dotenv(BASE_DIR / ".env")
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        print("[ERREUR] GEMINI_API_KEY manquante dans Source/.env")
        sys.exit(1)

    client       = anthropic.Anthropic(api_key=key)
    embedding_fn = GeminiEmbeddingFunction(api_key=key)
    chroma       = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection   = chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"description": "Chunks d articles scientifiques"},
    )
    return client, collection


# ---------------------------------------------------------------------------
# Agent 1 - Ingestion
# ---------------------------------------------------------------------------

def extract_pdf(pdf_path: Path) -> str:
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages.append(f"[Page {i+1}]\n{text.replace(chr(0), '').strip()}")
    except Exception as e:
        print(f"    Extraction echouee : {e}")
    return "\n\n".join(pages)


def chunk_text(text: str, filename: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    raw = splitter.split_text(text)
    return [
        {"text": c.strip(), "metadata": {"filename": filename, "chunk_index": i}}
        for i, c in enumerate(raw)
        if len(c.strip()) >= 50
    ]


def run_ingestion(collection) -> dict:
    print("Agent 1 - Ingestion")
    print("-" * 40)

    existing = collection.count()
    if existing > 0:
        print(f"  Base deja remplie ({existing} chunks). Ingestion ignoree.")
        return {"status": "skipped", "total_chunks": existing}

    pdfs = list(PAPERS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"  Aucun PDF dans {PAPERS_DIR}")
        return {"status": "no_papers", "total_chunks": 0}

    print(f"  {len(pdfs)} PDFs trouves")
    total_chunks = 0

    for pdf_path in pdfs:
        paper_id = pdf_path.stem.lower().replace(" ", "_").replace("-", "_")
        text = extract_pdf(pdf_path)
        if not text.strip():
            print(f"  {pdf_path.name} -> vide (ignore)")
            continue

        chunks = chunk_text(text, pdf_path.name)
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            collection.upsert(
                ids=[f"{paper_id}_chunk_{c['metadata']['chunk_index']}" for c in batch],
                documents=[c["text"] for c in batch],
                metadatas=[
                    {k: (str(v) if not isinstance(v, (str, int, float, bool)) else v)
                     for k, v in c["metadata"].items()}
                    for c in batch
                ],
            )
        print(f"  {pdf_path.name} -> {len(chunks)} chunks")
        total_chunks += len(chunks)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    result = {"status": "completed", "total_chunks": total_chunks,
              "completed_at": datetime.now().isoformat()}
    (LOGS_DIR / "ingestion_log.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  Total : {total_chunks} chunks")
    return result


# ---------------------------------------------------------------------------
# Agent 2 - Synthese
# ---------------------------------------------------------------------------

def query_collection(collection, query: str, n: int = N_RESULTS) -> list:
    total = collection.count()
    if total == 0:
        return []
    try:
        res = collection.query(
            query_texts=[query],
            n_results=min(n, total),
            include=["documents", "metadatas"],
        )
        return [
            {"text": d, "metadata": m}
            for d, m in zip(res["documents"][0], res["metadatas"][0])
        ]
    except Exception as e:
        print(f"    Erreur requete ChromaDB : {e}")
        return []


def synthesize_theme(client, collection, theme: str) -> dict:
    chunks = query_collection(collection, theme)
    if not chunks:
        return {"theme": theme, "status": "no_data", "themes": [],
                "key_methodologies": [], "main_findings": [],
                "temporal_evolution": {}, "key_authors_concepts": []}

    context = "\n\n".join([
        f"Extrait {i+1} ({c['metadata'].get('filename','?')}):\n{c['text']}"
        for i, c in enumerate(chunks)
    ])

    try:
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=2048,
            system=SYNTHESIS_PROMPT,
            messages=[{"role": "user", "content": f"Theme: {theme}\n\n{context}"}],
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?", "", raw).rstrip("`").strip()
        result = json.loads(raw)
        result.update({"theme": theme, "status": "success",
                       "input_tokens": resp.usage.input_tokens,
                       "output_tokens": resp.usage.output_tokens})
        print(f"    OK ({resp.usage.input_tokens} in, {resp.usage.output_tokens} out)")
        return result
    except Exception as e:
        print(f"    Erreur : {e}")
        return {"theme": theme, "status": "error", "error": str(e),
                "themes": [], "key_methodologies": [], "main_findings": [],
                "temporal_evolution": {}, "key_authors_concepts": []}


def run_synthesis(client, collection) -> dict:
    print("\nAgent 2 - Synthese thematique")
    print("-" * 40)

    syntheses = []
    for i, theme in enumerate(RESEARCH_THEMES):
        print(f"  [{i+1}/{len(RESEARCH_THEMES)}] {theme}")
        syntheses.append(synthesize_theme(client, collection, theme))
        if i < len(RESEARCH_THEMES) - 1:
            time.sleep(3)

    ok = sum(1 for s in syntheses if s.get("status") == "success")
    result = {
        "status": "completed",
        "themes_analyzed": RESEARCH_THEMES,
        "theme_syntheses": syntheses,
        "usage_stats": {
            "successful_syntheses": ok,
            "total_themes": len(RESEARCH_THEMES),
            "total_input_tokens":  sum(s.get("input_tokens",  0) for s in syntheses),
            "total_output_tokens": sum(s.get("output_tokens", 0) for s in syntheses),
        },
        "completed_at": datetime.now().isoformat(),
    }

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    (LOGS_DIR / "synthesis_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  {ok}/{len(RESEARCH_THEMES)} syntheses reussies")
    return result


# ---------------------------------------------------------------------------
# Agent 3 - Detection de Research Gaps
# ---------------------------------------------------------------------------

def build_synthesis_text(synthesis_data: dict) -> str:
    parts = ["Domain: " + ", ".join(synthesis_data.get("themes_analyzed", [])) + "\n"]
    for s in synthesis_data.get("theme_syntheses", []):
        if s.get("status") != "success":
            continue
        parts.append(f"\n### {s.get('theme')}")
        for f_item in s.get("main_findings", []):
            parts.append(f"- {f_item.get('finding', '')}")
        temporal = s.get("temporal_evolution", {})
        if isinstance(temporal, dict) and temporal.get("trend"):
            parts.append(f"  Trend: {temporal['trend']}")
    text = "\n".join(parts).strip()
    if len(text) < 50:
        text = "Domain: automated literature review and research gap detection in NLP."
    return text


def run_gap_detection(client, synthesis_data: dict) -> dict:
    print("\nAgent 3 - Detection des Research Gaps")
    print("-" * 40)

    synthesis_text = build_synthesis_text(synthesis_data)
    print(f"  Synthese : {len(synthesis_text)} caracteres")

    try:
        resp = client.messages.create(
            model=LLM_MODEL,
            max_tokens=4096,
            system=GAP_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Analyze:\n\n{synthesis_text}\n\nBegin step-by-step analysis:"
            }],
        )
        raw = resp.content[0].text

        analysis_m = re.search(r"<analysis>(.*?)</analysis>", raw, re.DOTALL)
        reasoning  = analysis_m.group(1).strip() if analysis_m else ""

        gaps_m = re.search(r"<gaps>(.*?)</gaps>", raw, re.DOTALL)
        if gaps_m:
            gaps_text = re.sub(r"^```(?:json)?", "", gaps_m.group(1).strip()).rstrip("`").strip()
            gaps_data = json.loads(gaps_text)
        else:
            json_m = re.search(r'\{[\s\S]*"research_gaps"[\s\S]*\}', raw)
            gaps_data = json.loads(json_m.group(0)) if json_m else {"research_gaps": []}

        n = len(gaps_data.get("research_gaps", []))
        print(f"  {n} gaps identifies ({resp.usage.input_tokens} in, {resp.usage.output_tokens} out)")

        result = {
            "status": "success",
            "gaps": gaps_data,
            "reasoning_excerpt": reasoning[:500],
            "metadata": {
                "input_tokens":  resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
            },
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        print(f"  Erreur : {e}")
        result = {
            "status": "error",
            "error": str(e),
            "gaps": {"research_gaps": [], "priority_ranking": [],
                     "cross_cutting_observations": "", "recommended_next_steps": ""},
            "metadata": {},
            "generated_at": datetime.now().isoformat(),
        }

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    (LOGS_DIR / "gaps_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result


# ---------------------------------------------------------------------------
# Rapport Final
# ---------------------------------------------------------------------------

def generate_report(ingestion: dict, synthesis: dict, gaps: dict) -> str:
    now           = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    research_gaps = gaps.get("gaps", {}).get("research_gaps", [])
    themes        = synthesis.get("themes_analyzed", [])

    lines = [
        "# Rapport Final - Revue de Litterature et Detection de Research Gaps",
        "",
        f"**Date** : {now}",
        f"**Chunks indexes** : {ingestion.get('total_chunks', 0)}",
        f"**Themes analyses** : {len(themes)}",
        f"**Gaps detectes** : {len(research_gaps)}",
        "",
        "---",
        "",
        "## 1. Themes Analyses",
        "",
    ]
    for i, t in enumerate(themes, 1):
        lines.append(f"{i}. {t}")

    lines += ["", "---", "", "## 2. Syntheses Thematiques", ""]
    for s in synthesis.get("theme_syntheses", []):
        if s.get("status") != "success":
            continue
        lines.append(f"### {s.get('theme')}")
        for f_item in s.get("main_findings", [])[:3]:
            lines.append(f"- {f_item.get('finding', '')}")
        temporal = s.get("temporal_evolution", {})
        if isinstance(temporal, dict) and temporal.get("trend"):
            lines.append(f"\nTendance : {temporal['trend'][:200]}")
        lines.append("")

    lines += ["---", "", "## 3. Research Gaps", ""]
    priority = gaps.get("gaps", {}).get("priority_ranking", [])
    if priority:
        lines.append("Priorite : " + " -> ".join(priority[:5]))
        lines.append("")

    for gap in research_gaps:
        lines += [
            f"### {gap.get('gap_id')} - {gap.get('title')}",
            f"**Type** : {gap.get('gap_type')} | **Impact** : {gap.get('estimated_impact')} "
            f"| **Faisabilite** : {gap.get('feasibility')}",
            "",
            gap.get("description", ""),
            "",
            f"Direction : {gap.get('suggested_research_direction', '')}",
            "",
        ]

    next_steps = gaps.get("gaps", {}).get("recommended_next_steps", "")
    if next_steps:
        lines += ["---", "", "## 4. Recommandations", "", next_steps]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("SMA Revue de Litterature - Pipeline complet")
    print(f"Debut : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    client, collection = init()

    ingestion = run_ingestion(collection)
    synthesis = run_synthesis(client, collection)
    gaps      = run_gap_detection(client, synthesis)

    print("\nGeneration du rapport...")
    report = generate_report(ingestion, synthesis, gaps)
    RAPPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RAPPORT_DIR / "rapport_final.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"Rapport : {report_path}")
    print()
    print("=" * 60)
    print("Pipeline termine")
    ok_s = synthesis.get("usage_stats", {}).get("successful_syntheses", 0)
    ok_g = len(gaps.get("gaps", {}).get("research_gaps", []))
    print(f"  Chunks     : {ingestion.get('total_chunks', 0)}")
    print(f"  Syntheses  : {ok_s}/{len(RESEARCH_THEMES)}")
    print(f"  Gaps       : {ok_g}")
    print("=" * 60)
