import os
import json
import uuid
import tempfile
import streamlit as st

from backend.app.pipeline.pdf_parser import PDFParser
from backend.app.pipeline.fact_extractor import FactExtractionEngine
from backend.app.pipeline.normalizer import FactNormalizer
from backend.app.pipeline.entity_resolution import EntityResolutionEngine
from backend.app.pipeline.candidate_matcher import CandidateFactMatcher
from backend.app.pipeline.relationship_engine import RelationshipEngine
from sample_data import SAMPLE_FACTS, SAMPLE_RELATIONSHIPS

st.set_page_config(
    page_title="Fact Knowledge Layer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark glassmorphism aesthetic
st.markdown(
    """
    <style>
    .main { background-color: #0b0f19; color: #e6edf3; }
    .stApp { background-color: #0b0f19; }
    .css-1d37w0e { background-color: #161b22; }
    .metric-strip { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .metric-box { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem; flex: 1; min-width: 140px; text-align: center; }
    .metric-value { font-size: 1.8rem; font-weight: 700; margin: 0; }
    .metric-label { font-size: 0.85rem; color: #8b949e; margin: 0; }
    .empty-state { text-align: center; padding: 3rem 1rem; background: #161b22; border: 1px solid #30363d; border-radius: 12px; margin-bottom: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "facts" not in st.session_state:
    st.session_state.facts = []
if "relationships" not in st.session_state:
    st.session_state.relationships = []
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False


def run_local_pipeline(uploaded_files, progress_bar=None, status_container=None):
    all_facts = []
    entity_engine = EntityResolutionEngine()
    total_docs = len(uploaded_files)

    if progress_bar and status_container:
        progress_bar.progress(5, text="📁 Preparing local temporary workspace...")
        status_container.info("📁 Initializing local in-memory extraction engine...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        for idx, uf in enumerate(uploaded_files):
            step_pct = int(10 + (idx / total_docs) * 40)
            if progress_bar and status_container:
                progress_bar.progress(step_pct, text=f"📄 Ingesting & parsing {uf.name} ({idx+1}/{total_docs})...")
                status_container.info(f"📄 Parsing layout & text blocks from `{uf.name}`...")

            file_path = os.path.join(tmp_dir, uf.name)
            with open(file_path, "wb") as f:
                f.write(uf.getvalue())

            doc_id = f"DOC-{uuid.uuid4().hex[:6].upper()}"
            page_count, pages_data = PDFParser.parse_pdf(file_path)

            extracted = FactExtractionEngine.extract_facts_from_pages(
                doc_id=doc_id,
                filename=uf.name,
                pages=pages_data
            )
            for fdict in extracted:
                ev = fdict.get("evidence", {})
                fdict["source_doc"] = ev.get("filename", uf.name)
                fdict["statement"] = f"{fdict.get('subject', '')} {fdict.get('predicate', '')} {fdict.get('raw_value', '')}".strip()
                fdict["fact_id"] = fdict.get("id", f"F-{uuid.uuid4().hex[:6].upper()}")
                fdict["verbatim_quote"] = ev.get("source_text", fdict.get("statement", ""))
                all_facts.append(fdict)

    if progress_bar and status_container:
        progress_bar.progress(60, text="🧩 Resolving and clustering cross-document entities...")
        status_container.info(f"🧩 Disambiguating {len(all_facts)} extracted facts across corporate entities...")

    subject_entity_map = entity_engine.resolve_entities(all_facts)

    for f in all_facts:
        norm_ent = entity_engine.get_canonical_name(f.get("subject", f.get("entity", "")))
        f["entity"] = norm_ent
        if "statement" not in f or not f["statement"]:
            f["statement"] = f"{f.get('subject', '')} {f.get('predicate', '')} {f.get('raw_value', '')}".strip()

    if progress_bar and status_container:
        progress_bar.progress(80, text="⚖️ Matching candidate pairs & cross-document reasoning...")
        status_container.info("⚖️ Evaluating cross-document corroborations, contradictions & scope differences...")

    candidate_pairs = CandidateFactMatcher.find_candidate_pairs(all_facts)
    relationships = RelationshipEngine.evaluate_pairs(candidate_pairs)

    if progress_bar and status_container:
        progress_bar.progress(100, text="✨ Analysis completed successfully!")
        status_container.success(f"✅ Finished! Found {len(all_facts)} discrete facts and {len(relationships)} cross-document relationships.")

    return all_facts, relationships



# Sidebar
with st.sidebar:
    st.title("⚖️ Fact Knowledge Layer")
    st.caption("100% Self-Contained Local Processing Engine (Zero External LLM APIs)")

    st.markdown("---")
    st.subheader("1. Document Ingestion")

    uploaded_files = st.file_uploader(
        "Upload PDF Corporate Disclosures",
        type=["pdf"],
        accept_multiple_files=True,
        help="Select multi-page PDFs to run local fact extraction & verification.",
    )

    st.markdown("---")

    run_analysis = st.button("🚀 Run Local Pipeline", type="primary", use_container_width=True)

    if st.button("🗑️ Reset Engine", use_container_width=True):
        st.session_state.facts = []
        st.session_state.relationships = []
        st.session_state.analysis_complete = False
        st.rerun()

# Main Header
st.title("Multi-Document Factual Verification Engine")
st.caption("Page-aware local PDF extraction, metric normalization, entity resolution, candidate matching, and relationship reasoning.")

if run_analysis:
    if not uploaded_files or len(uploaded_files) < 2:
        st.error("Please upload at least 2 PDF documents to run cross-document analysis.")
    else:
        prog_bar = st.progress(0, text="🚀 Starting local pipeline analysis...")
        status_box = st.empty()
        try:
            facts, rels = run_local_pipeline(uploaded_files, progress_bar=prog_bar, status_container=status_box)
            st.session_state.facts = facts
            st.session_state.relationships = rels
            st.session_state.analysis_complete = True
            st.rerun()
        except Exception as exc:
            prog_bar.empty()
            status_box.empty()
            st.error(f"Analysis failed: {exc}")


if not st.session_state.analysis_complete:
    st.markdown(
        """<div class="empty-state">
            <h2 style="color:#ccd6f6; font-weight:600; margin-bottom:0.5rem;">Multi-Document Factual Verification Engine</h2>
            <p style="color:#8892b0; max-width:680px; margin:0 auto 1.8rem auto; font-size:1rem; line-height:1.6;">
                Upload two or more corporate disclosures, research reports, or financial filings to extract atomic verifiable facts and cross-examine them across documents without hallucination.
            </p>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:1rem; margin-bottom:2rem;">
            <div style="background:#161b22; border:1px solid #30363d; border-radius:10px; padding:1.2rem;">
                <span style="font-size:1.5rem;">📄</span>
                <h4 style="color:#f0f6fc; margin:0.5rem 0 0.3rem 0; font-size:1.05rem;">1. Local In-Memory Extraction</h4>
                <p style="color:#8b949e; font-size:0.85rem; line-height:1.5; margin:0;">Parses raw text from multi-page PDFs locally, binding each discrete fact to its source document and exact verbatim quote.</p>
            </div>
            <div style="background:#161b22; border:1px solid #30363d; border-radius:10px; padding:1.2rem;">
                <span style="font-size:1.5rem;">🔬</span>
                <h4 style="color:#f0f6fc; margin:0.5rem 0 0.3rem 0; font-size:1.05rem;">2. Cross-Document Reasoning</h4>
                <p style="color:#8b949e; font-size:0.85rem; line-height:1.5; margin:0;">Examines claims across files to isolate corroborations, detect genuine disputes, and reconcile differences in timeframe or scope.</p>
            </div>
            <div style="background:#161b22; border:1px solid #30363d; border-radius:10px; padding:1.2rem;">
                <span style="font-size:1.5rem;">⚖️</span>
                <h4 style="color:#f0f6fc; margin:0.5rem 0 0.3rem 0; font-size:1.05rem;">3. 4-Case Evidence Review</h4>
                <p style="color:#8b949e; font-size:0.85rem; line-height:1.5; margin:0;">Categorizes relationships into Corroborations, Contradictions, Contextual Reconciliations, and Audit Failures with diagnostic fixes.</p>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("⚡ Load Demo Evaluation Dataset (Zero Setup)", use_container_width=True, type="primary"):
            st.session_state.facts = list(SAMPLE_FACTS)
            st.session_state.relationships = list(SAMPLE_RELATIONSHIPS)
            st.session_state.analysis_complete = True
            st.rerun()

    st.stop()

facts = st.session_state.facts
relationships = st.session_state.relationships

corroborations = [r for r in relationships if r.get("category") in ("Corroboration", "CORROBORATES")]
contradictions = [r for r in relationships if r.get("category") in ("Contradiction", "CONTRADICTS")]
reconciliations = [r for r in relationships if r.get("category") in ("Contextual Reconciliation", "CONTEXTUALIZES", "TEMPORAL_CHANGE")]
failures = [r for r in relationships if r.get("category") in ("Extraction Failure", "UNCERTAIN", "Uncertain")]


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

with tab_corr:
    st.json(corroborations)

with tab_contra:
    st.json(contradictions)

with tab_recon:
    st.json(reconciliations)

with tab_audit:
    st.json(failures)

st.markdown("---")
with st.expander("📊 Full Fact Registry", expanded=False):
    st.json(facts)

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
