"""
GEO Article Scorer
Streamlit UI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.parser import parse_article, run_deterministic_checks, extract_text_from_file
from utils.deepseek_scorer import score_all_dimensions
from reports.report_builder import build_report, report_to_markdown, score_label
from rules.rubric import DIMENSIONS, DIMENSION_ORDER

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GEO Article Scorer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #f7f6f2;
    color: #1a1a1a;
}

.main { background: #f7f6f2; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; }

h1, h2, h3 { font-family: 'DM Sans', sans-serif; font-weight: 600; letter-spacing: -0.3px; color: #111; }

.score-card {
    background: #ffffff;
    border: 1px solid #e4e2db;
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.score-card:hover { border-color: #2563eb; transition: border-color 0.2s; }

.score-number {
    font-family: 'DM Mono', monospace;
    font-size: 2.4rem;
    font-weight: 500;
    line-height: 1;
}

.score-green { color: #16a34a; }
.score-yellow { color: #ca8a04; }
.score-orange { color: #ea580c; }
.score-red { color: #dc2626; }

.dim-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #999;
    margin-bottom: 4px;
    font-weight: 500;
}

.proof-block {
    background: #fff8f8;
    border-left: 3px solid #dc2626;
    padding: 12px 16px;
    margin: 10px 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.88rem;
}

.proof-block.medium { border-left-color: #ea580c; background: #fff9f5; }
.proof-block.low { border-left-color: #ca8a04; background: #fffdf0; }

.proof-sentence {
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    color: #555;
    background: #f5f4f0;
    padding: 8px 12px;
    border-radius: 4px;
    margin: 8px 0;
    white-space: pre-wrap;
    word-break: break-word;
    border: 1px solid #e8e6e0;
}

.tag {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    padding: 2px 8px;
    border-radius: 3px;
    margin-right: 6px;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 500;
}

.tag-high { background: #fee2e2; color: #dc2626; }
.tag-medium { background: #ffedd5; color: #ea580c; }
.tag-low { background: #fef9c3; color: #ca8a04; }

.strength-item {
    padding: 7px 0;
    border-bottom: 1px solid #f0ede6;
    font-size: 0.9rem;
    color: #16a34a;
}

.improvement-item {
    padding: 7px 0;
    border-bottom: 1px solid #f0ede6;
    font-size: 0.9rem;
    color: #1a1a1a;
}

.overall-score-box {
    background: #ffffff;
    border: 2px solid #2563eb;
    border-radius: 10px;
    padding: 28px 32px;
    text-align: center;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(37,99,235,0.08);
}

.det-check-pass { color: #16a34a; font-size: 0.85rem; }
.det-check-fail { color: #dc2626; font-size: 0.85rem; }

.sidebar-section {
    background: #ffffff;
    border: 1px solid #e4e2db;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# ─── Helpers ────────────────────────────────────────────────────────────────
def color_class(score):
    if score >= 80: return "score-green"
    if score >= 65: return "score-yellow"
    if score >= 50: return "score-orange"
    return "score-red"


def severity_class(s):
    return {"high": "tag-high", "medium": "tag-medium", "low": "tag-low"}.get(s, "tag-low")


def render_score_card(dim_key, dim_score_data):
    score = dim_score_data.get("score", 0)
    label = DIMENSIONS[dim_key]["label"]
    reason = dim_score_data.get("reason_summary", "")
    confidence = dim_score_data.get("confidence", "")
    cc = color_class(score)

    st.markdown(f"""
    <div class="score-card">
        <div class="dim-label">{label}</div>
        <div class="score-number {cc}">{score}<span style="font-size:1rem;color:#555">/100</span></div>
        <div style="font-size:0.85rem;color:#888;margin-top:8px;">{reason}</div>
        <div style="font-size:0.72rem;color:#444;margin-top:4px;">Confidence: {confidence}</div>
    </div>
    """, unsafe_allow_html=True)


def render_proof_item(item):
    sev = item.get("severity", "low")
    sev_class = severity_class(sev)
    sentence = item.get("sentence", "")
    issue = item.get("issue", "")
    why = item.get("why_it_matters", "")
    fix = item.get("suggested_fix", "")
    dim_label = item.get("dimension_label", "")

    st.markdown(f"""
    <div class="proof-block {sev}">
        <span class="tag {sev_class}">{sev}</span>
        <span style="font-size:0.75rem;color:#555;">{dim_label}</span>
        <div class="proof-sentence">"{sentence}"</div>
        <div style="font-size:0.83rem;color:#ccc;"><strong>Issue:</strong> {issue}</div>
        <div style="font-size:0.83rem;color:#999;margin-top:4px;"><strong>Why it matters:</strong> {why}</div>
        <div style="font-size:0.83rem;color:#2563eb;margin-top:4px;"><strong>Fix:</strong> {fix}</div>
    </div>
    """, unsafe_allow_html=True)


# ─── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# ◈ GEO Scorer")
    st.markdown("<div style='font-size:0.8rem;color:#555;margin-bottom:16px;'>Generative Engine Optimization</div>", unsafe_allow_html=True)

    # Pull key from Streamlit secrets (cloud) or .env (local)
    _secret_key = ""
    try:
        _secret_key = st.secrets.get("DEEPSEEK_API_KEY", "")
    except Exception:
        pass
    _stored_key = _secret_key or os.getenv("DEEPSEEK_API_KEY", "")

    if _stored_key:
        api_key = _stored_key
        st.markdown("<div style='font-size:0.78rem;color:#16a34a;padding:6px 0;'>✓ API key configured</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            value="",
            help="Get your key from platform.deepseek.com",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    deep_mode = st.toggle("Deep Audit Mode", value=False, help="Uses deepseek-reasoner. Slower and costs more. Use for final audits.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size:0.75rem;color:#444;margin-top:24px;line-height:1.6;'>
    <strong style='color:#666'>8 scoring dimensions</strong><br>
    Answer-First · Atomicity · Structure · Fan-Out · Citation · Differentiation · Evidence · Extraction<br><br>
    <strong style='color:#666'>Two-layer scoring</strong><br>
    Deterministic rule engine + DeepSeek judgment<br><br>
    No score without evidence.
    </div>
    """, unsafe_allow_html=True)


# ─── Main ────────────────────────────────────────────────────────────────────
st.markdown("# GEO Article Scorer")
st.markdown("<div style='color:#555;font-size:0.9rem;margin-bottom:24px;'>Scores how well an article is written for generative AI answer systems. No score without evidence.</div>", unsafe_allow_html=True)

# Input method
input_tab, upload_tab = st.tabs(["Paste Text", "Upload File"])

article_text = ""

with input_tab:
    pasted = st.text_area(
        "Paste your article here",
        height=280,
        placeholder="Paste the full article text. Headings with ## or ### are recognized.",
    )
    if pasted:
        article_text = pasted

with upload_tab:
    uploaded_file = st.file_uploader("Upload .txt, .pdf, or .docx", type=["txt", "pdf", "docx"])
    if uploaded_file:
        extracted = extract_text_from_file(uploaded_file)
        if extracted and not extracted.startswith("PDF parse error") and not extracted.startswith("DOCX parse error"):
            article_text = extracted
            st.success(f"Extracted {len(article_text.split())} words from {uploaded_file.name}")
        elif extracted:
            st.error(extracted)

# Run button
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
col_btn, col_note = st.columns([1, 3])
with col_btn:
    run_clicked = st.button("▶ Score Article", type="primary", use_container_width=True)
with col_note:
    if deep_mode:
        st.markdown("<div style='font-size:0.8rem;color:#f59842;padding-top:8px;'>Deep Audit mode active. Uses deepseek-reasoner. Slower.</div>", unsafe_allow_html=True)

# ─── Scoring ────────────────────────────────────────────────────────────────
if run_clicked:
    if not article_text.strip():
        st.error("No article text found. Paste text or upload a file.")
        st.stop()

    if not api_key:
        st.error("DeepSeek API key is required. Enter it in the sidebar.")
        st.stop()

    if len(article_text.split()) < 50:
        st.warning("Article seems very short (under 50 words). Results may be limited.")

    # Parse
    with st.spinner("Parsing article structure..."):
        parsed = parse_article(article_text)
        det_checks = run_deterministic_checks(parsed)

    # Score dimensions
    progress_placeholder = st.empty()
    progress_bar = st.progress(0)
    dim_scores = {}

    def on_progress(i, dim_key):
        label = DIMENSIONS[dim_key]["label"]
        progress_placeholder.markdown(f"<div style='font-size:0.85rem;color:#555;'>Scoring: {label}...</div>", unsafe_allow_html=True)
        progress_bar.progress(i / len(DIMENSION_ORDER))

    with st.spinner("Running DeepSeek scoring..."):
        dim_scores = score_all_dimensions(article_text, api_key, deep_mode, on_progress)

    progress_bar.progress(1.0)
    progress_placeholder.empty()
    progress_bar.empty()

    # Build report
    report = build_report(parsed, det_checks, dim_scores)
    overall = report["overall_score"]
    label = report["overall_label"]
    cc = color_class(overall)

    # ─── Overall Score ───────────────────────────────────────────────────────
    st.markdown("---")
    col_ov, col_meta = st.columns([1, 2])
    with col_ov:
        st.markdown(f"""
        <div class="overall-score-box">
            <div class="dim-label">Overall GEO Readiness</div>
            <div class="score-number {cc}" style="font-size:4rem;">{overall}</div>
            <div style="font-size:0.9rem;color:#888;margin-top:6px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_meta:
        st.markdown(f"""
        <div class="score-card" style="margin-top:0">
            <div class="dim-label">Article Stats</div>
            <div style="font-size:0.9rem;margin-top:8px;">
                <span style="color:#666">Words</span> <strong>{report['word_count']}</strong> &nbsp;&nbsp;
                <span style="color:#666">Sentences</span> <strong>{report['sentence_count']}</strong> &nbsp;&nbsp;
                <span style="color:#666">Headings</span> <strong>{report['heading_count']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Top weak
        st.markdown("<div class='dim-label' style='margin-top:16px;'>Lowest Scores</div>", unsafe_allow_html=True)
        for dk, sc in report["top_weak_dimensions"]:
            cc2 = color_class(sc)
            st.markdown(f"<span class='score-number {cc2}' style='font-size:1.3rem;'>{sc}</span> <span style='font-size:0.85rem;color:#666;'>{DIMENSIONS[dk]['label']}</span>", unsafe_allow_html=True)

    # ─── Dimension Scores ────────────────────────────────────────────────────
    st.markdown("### Dimension Scores")
    cols = st.columns(4)
    for i, dim_key in enumerate(DIMENSION_ORDER):
        with cols[i % 4]:
            render_score_card(dim_key, dim_scores.get(dim_key, {}))

    # ─── Evidence / Proof ────────────────────────────────────────────────────
    st.markdown("### Evidence — What Was Found")
    st.markdown("<div style='font-size:0.82rem;color:#555;margin-bottom:12px;'>Every issue below is quoted directly from the article.</div>", unsafe_allow_html=True)

    if report["all_proof"]:
        for item in report["all_proof"]:
            render_proof_item(item)
    else:
        st.markdown("<div style='color:#555;font-size:0.9rem;'>No major issues flagged.</div>", unsafe_allow_html=True)

    # ─── Deterministic Checks ────────────────────────────────────────────────
    with st.expander("Deterministic Rule Checks (hard measurable checks)"):
        col_p, col_f = st.columns(2)
        with col_p:
            st.markdown("**Passed**")
            for k, v in report["deterministic_passes"].items():
                st.markdown(f"<div class='det-check-pass'>✓ {v['label']}<br><span style='color:#333;font-size:0.75rem;'>{v['proof']}</span></div>", unsafe_allow_html=True)
        with col_f:
            st.markdown("**Failed**")
            if report["deterministic_failures"]:
                for k, v in report["deterministic_failures"].items():
                    st.markdown(f"<div class='det-check-fail'>✗ {v['label']}<br><span style='color:#555;font-size:0.75rem;'>{v['proof']}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#555;font-size:0.9rem;'>All checks passed.</div>", unsafe_allow_html=True)

    # ─── Strengths & Improvements ────────────────────────────────────────────
    col_s, col_i = st.columns(2)
    with col_s:
        st.markdown("### Strengths")
        for s in report["all_strengths"]:
            st.markdown(f"<div class='strength-item'>✓ {s['text']}<br><span style='font-size:0.72rem;color:#555;'>{s['dimension']}</span></div>", unsafe_allow_html=True)

    with col_i:
        st.markdown("### Priority Fixes")
        for imp in report["all_improvements"]:
            st.markdown(f"<div class='improvement-item'>→ {imp['text']}<br><span style='font-size:0.72rem;color:#555;'>{imp['dimension']}</span></div>", unsafe_allow_html=True)

    # ─── Export ──────────────────────────────────────────────────────────────
    st.markdown("---")
    md_report = report_to_markdown(report, article_title="Scored Article")
    st.download_button(
        label="Download Report (Markdown)",
        data=md_report,
        file_name="geo_report.md",
        mime="text/markdown",
    )
