import os
import sys
import html
from pathlib import Path

# Register root directory in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

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
    page_title="Fact Knowledge Layer | Document Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Dark Glassmorphic Design System
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 15% 15%, rgba(14, 25, 45, 0.95) 0%, rgba(7, 11, 20, 1) 100%);
        color: #f1f5f9;
    }

    /* Sidebar Glassmorphism */
    section[data-testid="stSidebar"] {
        background: rgba(13, 19, 33, 0.75) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Custom Header Badges */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.45) 0%, rgba(15, 23, 42, 0.6) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 16px;
        padding: 1.8rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        line-height: 1.6;
        margin: 0 0 1rem 0;
    }
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
        background: rgba(56, 189, 248, 0.12);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.25);
        margin-right: 8px;
    }

    /* Metric Counters */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: rgba(19, 27, 46, 0.55);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.35);
        box-shadow: 0 10px 25px rgba(56, 189, 248, 0.12);
    }
    .metric-num {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-top: 0.3rem;
    }

    /* Relationship Glass Cards */
    .rel-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(14px);
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
        transition: all 0.2s ease-in-out;
    }
    .rel-card:hover {
        border-color: rgba(255, 255, 255, 0.16);
    }
    .rel-card-corr { border-left: 4px solid #10b981; }
    .rel-card-contra { border-left: 4px solid #ef4444; }
    .rel-card-recon { border-left: 4px solid #38bdf8; }
    .rel-card-audit { border-left: 4px solid #f59e0b; }

    .claim-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 0.85rem;
        margin-top: 0.75rem;
    }
    .claim-box {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 0.85rem 1rem;
    }
    .doc-tag {
        font-size: 0.72rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        color: #94a3b8;
        display: inline-block;
        margin-bottom: 0.3rem;
    }
    .quote-text {
        font-size: 0.88rem;
        color: #cbd5e1;
        font-style: italic;
        line-height: 1.5;
    }
    .reasoning-box {
        background: rgba(15, 23, 42, 0.5);
        border-left: 2px solid rgba(148, 163, 184, 0.3);
        padding: 0.75rem 1rem;
        margin-top: 0.8rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #e2e8f0;
        line-height: 1.55;
    }
    .diagnostic-fix {
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.25);
        color: #fbbf24;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-top: 0.8rem;
        font-size: 0.85rem;
    }

    /* Fact Table Cards */
    .fact-card {
        background: rgba(20, 29, 49, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .fact-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 700;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
        padding: 2px 6px;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Auto-initialize with benchmark evaluation data so outputs are immediately visible on load
if "facts" not in st.session_state or not st.session_state.facts:
    st.session_state.facts = list(SAMPLE_FACTS)
    st.session_state.relationships = list(SAMPLE_RELATIONSHIPS)
    st.session_state.dataset_label = "Demo Benchmark Dataset (7 Disclosures)"


def run_local_pipeline(uploaded_files, progress_bar=None, status_container=None):
    all_facts = []
    entity_engine = EntityResolutionEngine()
    total_docs = len(uploaded_files)

    if progress_bar and status_container:
        progress_bar.progress(5, text="📁 Preparing in-memory workspace...")
        status_container.info("📁 Initializing local PyMuPDF extraction engine...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        for idx, uf in enumerate(uploaded_files):
            step_pct = int(10 + (idx / total_docs) * 45)
            if progress_bar and status_container:
                progress_bar.progress(step_pct, text=f"📄 Ingesting & parsing {uf.name} ({idx+1}/{total_docs})...")
                status_container.info(f"📄 Parsing layout blocks & bounding boxes from `{uf.name}`...")

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
        progress_bar.progress(65, text="🧩 Resolving cross-document entity clusters...")
        status_container.info(f"🧩 Disambiguating {len(all_facts)} extracted claims across legal entities...")

    subject_entity_map = entity_engine.resolve_entities(all_facts)

    for f in all_facts:
        norm_ent = entity_engine.get_canonical_name(f.get("subject", f.get("entity", "")))
        f["entity"] = norm_ent
        if "statement" not in f or not f["statement"]:
            f["statement"] = f"{f.get('subject', '')} {f.get('predicate', '')} {f.get('raw_value', '')}".strip()

    if progress_bar and status_container:
        progress_bar.progress(85, text="⚖️ Multi-dimensional cross-document reasoning...")
        status_container.info("⚖️ Evaluating corroborations, numerical disputes & accounting reconciliations...")

    candidate_pairs = CandidateFactMatcher.find_candidate_pairs(all_facts)
    relationships = RelationshipEngine.evaluate_pairs(candidate_pairs)

    if progress_bar and status_container:
        progress_bar.progress(100, text="✨ Analysis completed successfully!")
        status_container.success(f"✅ Extracted {len(all_facts)} discrete facts and {len(relationships)} cross-document relationships.")

    return all_facts, relationships


# Sidebar Navigation & Upload
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:1rem;">
            <span style="font-size:1.8rem;">⚖️</span>
            <div>
                <h3 style="margin:0; font-size:1.15rem; color:#f8fafc; font-weight:700;">Fact Knowledge Layer</h3>
                <span style="font-size:0.75rem; color:#38bdf8; font-weight:600;">100% Local Intelligence</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption("Self-contained verification engine with zero external LLM dependencies.")
    st.markdown("---")
    
    st.subheader("📁 Ingest Custom PDFs")
    uploaded_files = st.file_uploader(
        "Upload Corporate PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload 2 or more PDFs (Earnings releases, ESG reports, 10-Ks, strategy memos) to verify.",
    )

    run_analysis = st.button("🚀 Analyze Uploaded PDFs", type="primary", use_container_width=True)

    if st.button("⚡ Reset to Benchmark Demo Data", use_container_width=True):
        st.session_state.facts = list(SAMPLE_FACTS)
        st.session_state.relationships = list(SAMPLE_RELATIONSHIPS)
        st.session_state.dataset_label = "Demo Benchmark Dataset (7 Disclosures)"
        st.rerun()

    st.markdown("---")
    st.markdown(
        """
        <div style="padding:0.8rem; background:rgba(255,255,255,0.03); border-radius:8px; font-size:0.75rem; color:#94a3b8; line-height:1.5;">
            🔒 <strong>Zero Data Leakage</strong><br>
            All PDF vector ingestion, regex tokenization, and reconciliation execute strictly in-memory.
        </div>
        """,
        unsafe_allow_html=True
    )

# Main Hero Header
st.markdown(
    """
    <div class="hero-container">
        <h1 class="hero-title">Multi-Document Factual Verification Engine</h1>
        <p class="hero-subtitle">
            Extracts discrete, verifiable facts from multi-page PDFs with exact bounding-box quotes. Disambiguates corporate entities, aligns accounting definitions, and flags genuine numerical contradictions.
        </p>
        <div>
            <span class="badge-pill">⚡ 100% In-Memory</span>
            <span class="badge-pill">🛡️ Zero LLM Hallucination</span>
            <span class="badge-pill">🔬 Evidence Grounded</span>
            <span class="badge-pill">📐 Deterministic Logic</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if run_analysis:
    if not uploaded_files or len(uploaded_files) < 2:
        st.warning("⚠️ Please select and upload at least 2 PDF documents in the sidebar to perform cross-document factual reconciliation.")
    else:
        prog_bar = st.progress(0, text="🚀 Starting local pipeline analysis...")
        status_box = st.empty()
        try:
            extracted_facts, extracted_rels = run_local_pipeline(uploaded_files, progress_bar=prog_bar, status_container=status_box)
            if not extracted_facts:
                prog_bar.empty()
                status_box.empty()
                st.warning("⚠️ No verifiable factual claims could be extracted from the uploaded PDFs. "
                           "This engine works best with corporate disclosures containing numerical metrics "
                           "(revenue, margins, headcount, growth rates). Try uploading earnings releases, "
                           "10-K filings, or investor presentations.")
            else:
                st.session_state.facts = extracted_facts
                st.session_state.relationships = extracted_rels
                st.session_state.dataset_label = f"Custom Upload ({len(uploaded_files)} PDFs)"
                st.rerun()
        except Exception as exc:
            prog_bar.empty()
            status_box.empty()
            st.error(f"Analysis failed: {exc}")


# Current Active Facts & Relationships
facts = st.session_state.facts
relationships = st.session_state.relationships

corroborations = [r for r in relationships if r.get("category") in ("Corroboration", "CORROBORATES")]
contradictions = [r for r in relationships if r.get("category") in ("Contradiction", "CONTRADICTS")]
reconciliations = [r for r in relationships if r.get("category") in ("Contextual Reconciliation", "CONTEXTUALIZES", "TEMPORAL_CHANGE")]
failures = [r for r in relationships if r.get("category") in ("Extraction Failure", "UNCERTAIN", "Uncertain")]
source_docs = set(f.get("source_doc", "") for f in facts)

# Dataset Badge
st.markdown(
    f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
        <span style="font-size:0.85rem; color:#94a3b8; font-weight:600;">Active Dataset: <strong style="color:#38bdf8;">{html.escape(str(st.session_state.get('dataset_label', 'Active Analysis')))}</strong></span>
        <span style="font-size:0.8rem; color:#64748b;">Grounding: In-Memory PyMuPDF + spaCy</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Metric Summary Strip
st.markdown(
    f"""
    <div class="metric-grid">
        <div class="metric-card">
            <p class="metric-num" style="color:#38bdf8;">{len(facts)}</p>
            <p class="metric-label">Facts Extracted</p>
        </div>
        <div class="metric-card">
            <p class="metric-num" style="color:#818cf8;">{len(source_docs)}</p>
            <p class="metric-label">Source Documents</p>
        </div>
        <div class="metric-card">
            <p class="metric-num" style="color:#10b981;">{len(corroborations)}</p>
            <p class="metric-label">Corroborations</p>
        </div>
        <div class="metric-card">
            <p class="metric-num" style="color:#ef4444;">{len(contradictions)}</p>
            <p class="metric-label">Contradictions</p>
        </div>
        <div class="metric-card">
            <p class="metric-num" style="color:#06b6d4;">{len(reconciliations)}</p>
            <p class="metric-label">Reconciliations</p>
        </div>
        <div class="metric-card">
            <p class="metric-num" style="color:#f59e0b;">{len(failures)}</p>
            <p class="metric-label">Audit Flags</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Relationship Explorer Tabs
tab_corr, tab_contra, tab_recon, tab_audit, tab_facts = st.tabs([
    f"✅ Corroborated Evidence ({len(corroborations)})",
    f"⚔️ Genuine Contradictions ({len(contradictions)})",
    f"🔄 Contextual Reconciliations ({len(reconciliations)})",
    f"🔍 Audit & Failures ({len(failures)})",
    f"📊 Fact Registry ({len(facts)})"
])


def render_relationship_cards(items, card_type="corr"):
    if not items:
        st.info("No relationships found in this category.")
        return

    for item in items:
        rel_id = html.escape(str(item.get("relationship_id") or item.get("id", "R-001")))
        category = html.escape(str(item.get("category", "Analysis")))
        reasoning = html.escape(str(item.get("reasoning", "")))
        diagnostic = html.escape(str(item.get("diagnostic_fix") or "")) if item.get("diagnostic_fix") else ""
        claims = item.get("competing_claims", [])
        quotes = item.get("source_quotes", [])
        docs = item.get("source_docs", [])
        conf_val = item.get('confidence', 0.95)
        conf_pct = conf_val * 100 if isinstance(conf_val, (int, float)) else 95

        claims_html = []
        claim_count = max(len(claims), len(docs), 1)
        for idx in range(claim_count):
            doc_name = html.escape(str(docs[idx])) if idx < len(docs) else "Document"
            claim_text = html.escape(str(claims[idx])) if idx < len(claims) else "Extracted claim"
            quote_text = html.escape(str(quotes[idx])) if idx < len(quotes) else ""
            quote_markup = f'<div class="quote-text">"{quote_text}"</div>' if quote_text else ""

            claims_html.append(f"""
                <div class="claim-box">
                    <span class="doc-tag">📄 {doc_name}</span>
                    <div style="font-weight:600; font-size:0.92rem; color:#f1f5f9; margin-bottom:0.4rem;">{claim_text}</div>
                    {quote_markup}
                </div>
            """)

        claims_joined = "".join(claims_html)
        diagnostic_markup = f'<div class="diagnostic-fix"><strong>⚠️ Diagnostic Fix Action:</strong> {diagnostic}</div>' if diagnostic else ""

        card_html = f"""
        <div class="rel-card rel-card-{card_type}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <div>
                    <span class="fact-id">{rel_id}</span>
                    <strong style="margin-left:8px; font-size:1rem; color:#f8fafc;">{category}</strong>
                </div>
                <span style="font-size:0.75rem; color:#94a3b8; font-weight:600;">Confidence: {conf_pct:.0f}%</span>
            </div>
            <div class="claim-grid">
                {claims_joined}
            </div>
            <div class="reasoning-box">
                <strong>💡 Reconciliation Reasoning:</strong> {reasoning}
            </div>
            {diagnostic_markup}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)


with tab_corr:
    st.caption("Multi-source claims that independently corroborate identical metrics, timeframes, and entities.")
    render_relationship_cards(corroborations, card_type="corr")

with tab_contra:
    st.caption("Direct numerical or factual disputes across official corporate disclosures without scope justification.")
    render_relationship_cards(contradictions, card_type="contra")

with tab_recon:
    st.caption("Apparent variances fully reconciled by accounting standards (e.g. GAAP vs Non-GAAP) or timeframe differences.")
    render_relationship_cards(reconciliations, card_type="recon")

with tab_audit:
    st.caption("Ambiguous claims flagged for human audit (unnamed legal entities, relative timeframes, missing denominators).")
    render_relationship_cards(failures, card_type="audit")

with tab_facts:
    st.caption("Discrete, atomic extracted facts normalized into structured key-value entities.")
    for f in facts:
        fid = html.escape(str(f.get("fact_id") or f.get("id", "F-001")))
        subj = html.escape(str(f.get("subject", f.get("entity", "Corporate Entity"))))
        metric = html.escape(str(f.get("raw_value") or f.get("metric_or_value", "")))
        pred = html.escape(str(f.get("predicate", "statement")))
        src = html.escape(str(f.get("source_doc", "")))
        quote = html.escape(str(f.get("verbatim_quote") or f.get("evidence", {}).get("source_text", "")))
        temp = html.escape(str(f.get("temporal_period", ""))) if f.get("temporal_period") else ""
        temp_badge = f'<span class="badge-pill" style="margin-left:6px;">{temp}</span>' if temp else ''
        quote_markup = f'"{quote}"' if quote else ""

        st.markdown(
            f"""
            <div class="fact-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span class="fact-id">{fid}</span>
                        <strong style="margin-left:8px; color:#f8fafc; font-size:0.95rem;">{subj}</strong>
                        <span style="color:#94a3b8; font-size:0.85rem; margin-left:6px;">— {pred}</span>
                    </div>
                    <div>
                        <span style="font-weight:700; color:#38bdf8; font-size:1.05rem;">{metric}</span>
                        {temp_badge}
                    </div>
                </div>
                <div style="margin-top:0.5rem; display:flex; justify-content:space-between; align-items:flex-end;">
                    <div style="color:#94a3b8; font-size:0.82rem; font-style:italic; max-width:80%;">
                        {quote_markup}
                    </div>
                    <span class="doc-tag">📄 {src}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# Raw JSON Export Section
st.markdown("---")
with st.expander("🧾 Export Evaluation Artifacts (JSON)", expanded=False):
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.download_button(
            "📥 Download Fact Knowledge Registry (JSON)",
            data=json.dumps(facts, indent=2),
            file_name="extracted_facts.json",
            mime="application/json",
            use_container_width=True,
        )
    with export_col2:
        st.download_button(
            "📥 Download Cross-References (JSON)",
            data=json.dumps(relationships, indent=2),
            file_name="cross_references.json",
            mime="application/json",
            use_container_width=True,
        )
