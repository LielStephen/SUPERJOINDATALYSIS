import os
import json
import hashlib
import traceback
from typing import Optional

import streamlit as st
from pypdf import PdfReader
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from sample_data import SAMPLE_FACTS, SAMPLE_RELATIONSHIPS


class ExtractedFact(BaseModel):
    fact_id: str = Field(description="Unique identifier for this fact, e.g. F-001")
    statement: str = Field(description="A concise factual claim extracted from the document")
    metric_or_value: str = Field(description="The specific number, date, percentage, or measurable value associated with the fact. Use 'N/A' if qualitative.")
    source_doc: str = Field(description="Exact filename of the source PDF document")
    verbatim_quote: str = Field(description="An exact substring copied from the PDF text that supports this fact")


class ExtractionResult(BaseModel):
    facts: list[ExtractedFact]


class CrossReference(BaseModel):
    relationship_id: str = Field(description="Unique identifier, e.g. R-001")
    category: str = Field(description="Exactly one of: Corroboration, Contradiction, Contextual Reconciliation, Extraction Failure")
    fact_ids: list[str] = Field(description="The fact_ids being compared")
    competing_claims: list[str] = Field(description="The statement text of each competing or corroborating claim")
    source_quotes: list[str] = Field(description="The verbatim_quote from each relevant fact")
    source_docs: list[str] = Field(description="The source_doc for each claim")
    reasoning: str = Field(description="Detailed explanation of why this relationship was classified this way, grounded only in the document text")
    diagnostic_fix: Optional[str] = Field(default=None, description="For Extraction Failure only: what was ambiguous and how the source text could be clarified")


class CrossReferenceResult(BaseModel):
    relationships: list[CrossReference]


def extract_text_from_pdf(uploaded_file) -> tuple[str, str]:
    filename = uploaded_file.name
    try:
        reader = PdfReader(uploaded_file)
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                pages.append(f"[Page {i}]\n{text}")
        full_text = "\n\n".join(pages)
        if not full_text.strip():
            raise ValueError(f"No extractable text found in '{filename}'. The file may be image-based or empty.")
        return filename, full_text
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Failed to parse '{filename}': {exc}") from exc


def build_corpus(uploaded_files: list) -> dict[str, str]:
    corpus: dict[str, str] = {}
    errors: list[str] = []
    for uf in uploaded_files:
        try:
            name, text = extract_text_from_pdf(uf)
            corpus[name] = text
        except (ValueError, RuntimeError) as exc:
            errors.append(str(exc))
    if errors:
        for err in errors:
            st.error(err)
    return corpus


EXTRACTION_SYSTEM_PROMPT = """You are a strict, evidence-based factual extraction engine.
You will receive the full text of one or more PDF documents, each clearly delimited by a header line showing the source filename.

Your ONLY job is to extract discrete, verifiable facts from the provided text.

Rules you MUST follow:
- NEVER use outside knowledge. Every fact must come directly from the provided text.
- The `verbatim_quote` field must be an EXACT substring of the source document text — do not paraphrase, re-order words, or truncate.
- The `source_doc` must be the exact filename shown in the document header.
- If a fact is qualitative (no number/date), set `metric_or_value` to "N/A".
- Assign sequential fact IDs starting from F-001.
- Extract ALL substantive facts: financial figures, dates, percentages, named entities, causal claims, strategic statements, and quantitative metrics.
- Do NOT summarize or editorialize. Extract raw facts only."""

CROSS_REFERENCE_SYSTEM_PROMPT = """You are a meticulous cross-reference analyst.
You will receive a JSON array of extracted facts, each with a fact_id, statement, metric_or_value, source_doc, and verbatim_quote.

Your job is to compare facts across documents and classify every meaningful relationship into EXACTLY one of these categories:

1. **Corroboration**: Two or more facts from DIFFERENT documents confirm the same claim with consistent values/meanings.
2. **Contradiction**: Two or more facts from DIFFERENT documents make conflicting claims about the same subject.
3. **Contextual Reconciliation**: Facts that APPEAR to conflict but are actually consistent when accounting for differences in timeframe, scope, definition, entity naming, or rounding. You MUST explain the reconciling context.
4. **Extraction Failure**: A fact whose wording in the source is ambiguous, incomplete, or lacks sufficient context to be reliably compared. Provide a `diagnostic_fix` explaining the ambiguity and suggesting what additional context would resolve it.

Rules:
- NEVER use outside knowledge. Base every judgment solely on the provided facts and their verbatim quotes.
- Be sensitive to subtle differences: same metric but different fiscal years, same entity with differently formatted names, currency differences, rounded vs. precise figures.
- The `reasoning` field must explicitly cite the verbatim quotes and source documents.
- For Extraction Failure, always populate the `diagnostic_fix` field.
- Assign sequential relationship IDs starting from R-001.
- Every fact should appear in at least one relationship. If a fact has no cross-document relationship, check if it could be an Extraction Failure candidate due to missing context."""


def get_gemini_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def run_extraction(client: genai.Client, model: str, corpus: dict[str, str]) -> list[dict]:
    doc_blocks = []
    for filename, text in corpus.items():
        doc_blocks.append(f"===== DOCUMENT: {filename} =====\n{text}\n===== END OF {filename} =====")

    combined = "\n\n".join(doc_blocks)

    try:
        response = client.models.generate_content(
            model=model,
            contents=combined,
            config=types.GenerateContentConfig(
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ExtractionResult,
                temperature=0.0,
            ),
        )
        parsed = json.loads(response.text)
        return parsed.get("facts", [])
    except json.JSONDecodeError as exc:
        st.error(f"Gemini returned malformed JSON during extraction: {exc}")
        st.code(response.text[:2000], language="json")
        return []
    except Exception as exc:
        error_str = str(exc).lower()
        if "429" in error_str or "rate" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
            st.error(f"🚦 Rate limit / quota exceeded. Wait a moment and retry.\n\nDetails: {exc}")
        elif "400" in error_str or "invalid" in error_str:
            st.error(f"⚠️ Invalid request sent to Gemini. Check your API key and model name.\n\nDetails: {exc}")
        else:
            st.error(f"Gemini extraction failed: {exc}")
            st.code(traceback.format_exc(), language="text")
        return []


def run_cross_reference(client: genai.Client, model: str, facts: list[dict]) -> list[dict]:
    facts_json = json.dumps(facts, indent=2)

    try:
        response = client.models.generate_content(
            model=model,
            contents=f"Here are the extracted facts to cross-reference:\n\n{facts_json}",
            config=types.GenerateContentConfig(
                system_instruction=CROSS_REFERENCE_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=CrossReferenceResult,
                temperature=0.0,
            ),
        )
        parsed = json.loads(response.text)
        return parsed.get("relationships", [])
    except json.JSONDecodeError as exc:
        st.error(f"Gemini returned malformed JSON during cross-referencing: {exc}")
        st.code(response.text[:2000], language="json")
        return []
    except Exception as exc:
        error_str = str(exc).lower()
        if "429" in error_str or "rate" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
            st.error(f"🚦 Rate limit / quota exceeded during cross-referencing. Wait a moment and retry.\n\nDetails: {exc}")
        elif "400" in error_str or "invalid" in error_str:
            st.error(f"⚠️ Invalid request during cross-referencing.\n\nDetails: {exc}")
        else:
            st.error(f"Gemini cross-referencing failed: {exc}")
            st.code(traceback.format_exc(), language="text")
        return []


def render_fact_card(fact: dict, idx: int):
    with st.container():
        st.markdown(
            f"""<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #0f3460; border-radius: 12px; padding: 1.2rem; margin-bottom: 0.8rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                <span style="background:#e94560; color:white; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600;">{fact.get('fact_id', f'F-{idx:03d}')}</span>
                <span style="color:#8892b0; font-size:0.75rem;">📄 {fact.get('source_doc', 'Unknown')}</span>
            </div>
            <p style="color:#ccd6f6; font-size:0.95rem; margin:0 0 0.5rem 0;">{fact.get('statement', '')}</p>
            <div style="background:#0a192f; border-left:3px solid #64ffda; padding:0.5rem 0.8rem; border-radius:4px; margin-top:0.4rem;">
                <span style="color:#64ffda; font-size:0.7rem; text-transform:uppercase; letter-spacing:1px;">Metric/Value</span>
                <p style="color:#e6f1ff; font-size:0.9rem; margin:0.2rem 0 0 0; font-weight:500;">{fact.get('metric_or_value', 'N/A')}</p>
            </div>
            <div style="background:#0a192f; border-left:3px solid #8892b0; padding:0.5rem 0.8rem; border-radius:4px; margin-top:0.5rem;">
                <span style="color:#8892b0; font-size:0.7rem; text-transform:uppercase; letter-spacing:1px;">Verbatim Quote</span>
                <p style="color:#a8b2d1; font-size:0.85rem; font-style:italic; margin:0.2rem 0 0 0;">"{fact.get('verbatim_quote', '')}"</p>
            </div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_relationship_card(rel: dict, accent_color: str, icon: str):
    quotes_html = ""
    for i, quote in enumerate(rel.get("source_quotes", [])):
        doc = rel.get("source_docs", [""])[i] if i < len(rel.get("source_docs", [])) else "?"
        quotes_html += f"""
        <div style="background:#0a192f; border-left:3px solid {accent_color}; padding:0.6rem 0.8rem; border-radius:4px;">
            <span style="color:{accent_color}; font-size:0.7rem; text-transform:uppercase; letter-spacing:1px;">📄 {doc}</span>
            <p style="color:#a8b2d1; font-size:0.85rem; font-style:italic; margin:0.2rem 0 0 0;">"{quote}"</p>
        </div>"""

    claims_html = ""
    for claim in rel.get("competing_claims", []):
        claims_html += f'<li style="color:#ccd6f6; font-size:0.9rem; margin-bottom:0.3rem;">{claim}</li>'

    diagnostic_html = ""
    if rel.get("diagnostic_fix"):
        diagnostic_html = f"""
        <div style="background:#1a1a0e; border:1px solid #e6a817; border-radius:8px; padding:0.6rem 0.8rem; margin-top:0.6rem;">
            <span style="color:#e6a817; font-size:0.75rem; font-weight:600;">🔧 DIAGNOSTIC FIX</span>
            <p style="color:#ccd6f6; font-size:0.85rem; margin:0.3rem 0 0 0;">{rel.get('diagnostic_fix')}</p>
        </div>"""

    st.markdown(
        f"""<div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
            <span style="font-size:1.1rem; font-weight:600; color:#ccd6f6;">{icon} {rel.get('relationship_id', '')}</span>
            <span style="background:{accent_color}; color:#0a192f; padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:700;">{rel.get('category', '')}</span>
        </div>
        <div style="margin-bottom:0.6rem;">
            <span style="color:#8892b0; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px;">Fact IDs: {', '.join(rel.get('fact_ids', []))}</span>
        </div>
        <ul style="padding-left:1.2rem; margin:0 0 0.6rem 0;">{claims_html}</ul>
        <div style="margin-bottom:0.6rem;">
            <span style="color:#8892b0; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px;">Side-by-Side Source Quotes</span>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:0.6rem; margin-top:0.3rem;">
                {quotes_html}
            </div>
        </div>
        <div style="background:#0a192f; border-radius:8px; padding:0.6rem 0.8rem; margin-top:0.4rem;">
            <span style="color:#64ffda; font-size:0.75rem; font-weight:600;">REASONING</span>
            <p style="color:#a8b2d1; font-size:0.88rem; margin:0.3rem 0 0 0;">{rel.get('reasoning', '')}</p>
        </div>
        {diagnostic_html}
        </div>""",
        unsafe_allow_html=True,
    )


AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

st.set_page_config(
    page_title="Fact Knowledge Layer — Multi-Document Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(180deg, #0a0a1a 0%, #0d1117 50%, #0a0a1a 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid #21262d;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown label {
        color: #8b949e;
    }

    .main-title {
        background: linear-gradient(135deg, #64ffda 0%, #48b1bf 50%, #e94560 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 0;
    }

    .subtitle {
        color: #8892b0;
        font-size: 1.05rem;
        font-weight: 300;
        margin-top: 0.2rem;
        margin-bottom: 2rem;
    }

    div[data-testid="stTabs"] button {
        color: #8892b0 !important;
        font-weight: 500;
        border-bottom: 2px solid transparent;
        transition: all 0.2s ease;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #64ffda !important;
        border-bottom: 2px solid #64ffda;
    }

    .metric-strip {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .metric-box {
        flex: 1;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        text-align: center;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }

    .metric-label {
        color: #8892b0;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 0.2rem 0 0 0;
    }

    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #8892b0;
    }

    .empty-state .icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

env_api_key = os.environ.get("GEMINI_API_KEY", "")
try:
    if not env_api_key and "GEMINI_API_KEY" in st.secrets:
        env_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

with st.sidebar:
    st.markdown("### 🔐 Configuration")
    api_key = st.text_input(
        "Gemini API Key",
        value=env_api_key,
        type="password",
        help="Your Google AI Studio API key",
    )
    selected_model = st.selectbox("Model", AVAILABLE_MODELS, index=0)
    ingestion_mode = st.radio(
        "Ingestion Mode",
        ["Replace Knowledge Layer", "Incremental (Append New PDFs)"],
        index=0,
        help="Incremental mode appends newly extracted facts to existing knowledge without rebuilding.",
    )
    st.markdown("---")
    st.markdown("### 📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Drop your PDFs here",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload 2 or more PDF documents for cross-referencing",
    )
    st.markdown("---")
    run_analysis = st.button("🚀 Run Analysis", use_container_width=True, type="primary", disabled=not api_key or not uploaded_files)

    if st.button("⚡ Load Demo Dataset", use_container_width=True, help="Load precomputed dataset demonstrating all 4 challenge cases"):
        st.session_state.facts = list(SAMPLE_FACTS)
        st.session_state.relationships = list(SAMPLE_RELATIONSHIPS)
        st.session_state.analysis_complete = True
        st.session_state.corpus_hash = "sample-eval"
        st.rerun()

    if st.session_state.get("analysis_complete", False):
        if st.button("🔄 Reset Analysis", use_container_width=True):
            st.session_state.facts = []
            st.session_state.relationships = []
            st.session_state.analysis_complete = False
            st.session_state.corpus_hash = None
            st.rerun()

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)}** document(s) staged")
        for uf in uploaded_files:
            size_kb = len(uf.getvalue()) / 1024
            st.caption(f"📄 {uf.name} — {size_kb:.1f} KB")

st.markdown('<h1 class="main-title">Fact Knowledge Layer</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Evidence-based multi-document analysis powered by Gemini structured outputs</p>', unsafe_allow_html=True)

if "facts" not in st.session_state:
    st.session_state.facts = []
if "relationships" not in st.session_state:
    st.session_state.relationships = []
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "corpus_hash" not in st.session_state:
    st.session_state.corpus_hash = None

if run_analysis:
    if len(uploaded_files) < 2 and ingestion_mode == "Replace Knowledge Layer":
        st.warning("Upload at least 2 PDF documents for meaningful cross-referencing.")
    else:
        file_bytes = b"".join(uf.getvalue() for uf in uploaded_files)
        current_hash = hashlib.md5(file_bytes).hexdigest()

        with st.spinner("📖 Extracting text from PDFs…"):
            for uf in uploaded_files:
                uf.seek(0)
            corpus = build_corpus(uploaded_files)

        if not corpus:
            st.error("No text could be extracted from any of the uploaded documents.")
            st.stop()

        client = get_gemini_client(api_key)

        with st.spinner("🔬 Stage 1 — Strict fact extraction via Gemini…"):
            new_facts = run_extraction(client, selected_model, corpus)

        if not new_facts:
            st.error("Extraction returned zero facts. Check the documents and API key.")
            st.stop()

        if ingestion_mode == "Incremental (Append New PDFs)" and st.session_state.facts:
            existing_count = len(st.session_state.facts)
            for i, f in enumerate(new_facts):
                f["fact_id"] = f"F-{existing_count + i + 1:03d}"
            cumulative_facts = st.session_state.facts + new_facts
        else:
            cumulative_facts = new_facts

        with st.spinner("🔗 Stage 2 — Cross-referencing facts across documents…"):
            relationships = run_cross_reference(client, selected_model, cumulative_facts)

        st.session_state.facts = cumulative_facts
        st.session_state.relationships = relationships
        st.session_state.analysis_complete = True
        st.session_state.corpus_hash = current_hash
        st.rerun()

if not st.session_state.analysis_complete:
    st.markdown(
        """<div class="empty-state">
            <div class="icon">📂</div>
            <h3 style="color:#ccd6f6; font-weight:500;">No active analysis</h3>
            <p>Upload PDF documents in the sidebar to run live extraction with Gemini, or load the precomputed evaluation dataset showcasing all four required challenge cases.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("⚡ Load Demo Evaluation Dataset (Zero Setup)", use_container_width=True, type="secondary"):
            st.session_state.facts = list(SAMPLE_FACTS)
            st.session_state.relationships = list(SAMPLE_RELATIONSHIPS)
            st.session_state.analysis_complete = True
            st.session_state.corpus_hash = "sample-eval"
            st.rerun()
    st.stop()

facts = st.session_state.facts
relationships = st.session_state.relationships

corroborations = [r for r in relationships if r.get("category") == "Corroboration"]
contradictions = [r for r in relationships if r.get("category") == "Contradiction"]
reconciliations = [r for r in relationships if r.get("category") == "Contextual Reconciliation"]
failures = [r for r in relationships if r.get("category") == "Extraction Failure"]

source_docs = set(f.get("source_doc", "") for f in facts)

st.markdown(
    f"""<div class="metric-strip">
        <div class="metric-box">
            <p class="metric-value" style="color:#64ffda;">{len(facts)}</p>
            <p class="metric-label">Facts Extracted</p>
        </div>
        <div class="metric-box">
            <p class="metric-value" style="color:#48b1bf;">{len(source_docs)}</p>
            <p class="metric-label">Source Documents</p>
        </div>
        <div class="metric-box">
            <p class="metric-value" style="color:#4ade80;">{len(corroborations)}</p>
            <p class="metric-label">Corroborations</p>
        </div>
        <div class="metric-box">
            <p class="metric-value" style="color:#e94560;">{len(contradictions)}</p>
            <p class="metric-label">Contradictions</p>
        </div>
        <div class="metric-box">
            <p class="metric-value" style="color:#48b1bf;">{len(reconciliations)}</p>
            <p class="metric-label">Reconciliations</p>
        </div>
        <div class="metric-box">
            <p class="metric-value" style="color:#e6a817;">{len(failures)}</p>
            <p class="metric-label">Audit Flags</p>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

tab_corr, tab_contra, tab_recon, tab_audit = st.tabs([
    f"✅ Corroborated Evidence ({len(corroborations)})",
    f"⚔️ Genuine Contradictions ({len(contradictions)})",
    f"🔄 Contextual Reconciliations ({len(reconciliations)})",
    f"🔍 Audit & Failures ({len(failures)})",
])

fact_lookup = {f.get("fact_id"): f for f in facts}

with tab_corr:
    if not corroborations:
        st.info("No corroborated facts found across the uploaded documents.")
    for rel in corroborations:
        render_relationship_card(rel, "#4ade80", "✅")
        with st.expander("View underlying facts"):
            cols = st.columns(len(rel.get("fact_ids", [])))
            for i, fid in enumerate(rel.get("fact_ids", [])):
                with cols[i % len(cols)]:
                    fact = fact_lookup.get(fid, {"fact_id": fid, "statement": "Fact not found"})
                    render_fact_card(fact, i)

with tab_contra:
    if not contradictions:
        st.info("No genuine contradictions detected across the uploaded documents.")
    for rel in contradictions:
        render_relationship_card(rel, "#e94560", "⚔️")
        with st.expander("View underlying facts"):
            cols = st.columns(len(rel.get("fact_ids", [])))
            for i, fid in enumerate(rel.get("fact_ids", [])):
                with cols[i % len(cols)]:
                    fact = fact_lookup.get(fid, {"fact_id": fid, "statement": "Fact not found"})
                    render_fact_card(fact, i)

with tab_recon:
    if not reconciliations:
        st.info("No contextual reconciliations identified.")
    for rel in reconciliations:
        render_relationship_card(rel, "#48b1bf", "🔄")
        with st.expander("View underlying facts"):
            cols = st.columns(len(rel.get("fact_ids", [])))
            for i, fid in enumerate(rel.get("fact_ids", [])):
                with cols[i % len(cols)]:
                    fact = fact_lookup.get(fid, {"fact_id": fid, "statement": "Fact not found"})
                    render_fact_card(fact, i)

with tab_audit:
    if not failures:
        st.info("No extraction failures or audit flags raised — all facts extracted cleanly.")
    for rel in failures:
        render_relationship_card(rel, "#e6a817", "🔍")
        with st.expander("View underlying facts"):
            for fid in rel.get("fact_ids", []):
                fact = fact_lookup.get(fid, {"fact_id": fid, "statement": "Fact not found"})
                render_fact_card(fact, 0)

st.markdown("---")
with st.expander("📊 Full Fact Registry", expanded=False):
    for i, fact in enumerate(facts):
        render_fact_card(fact, i)

with st.expander("🧾 Raw JSON Output & Export", expanded=False):
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.download_button(
            "📥 Download Facts JSON",
            data=json.dumps(facts, indent=2),
            file_name="extracted_facts.json",
            mime="application/json",
            use_container_width=True,
        )
    with export_col2:
        st.download_button(
            "📥 Download Cross-References JSON",
            data=json.dumps(relationships, indent=2),
            file_name="cross_references.json",
            mime="application/json",
            use_container_width=True,
        )
    raw_tab1, raw_tab2 = st.tabs(["Extracted Facts", "Cross-References"])
    with raw_tab1:
        st.json(facts)
    with raw_tab2:
        st.json(relationships)
