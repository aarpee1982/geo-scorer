"""
Report Builder
Merges deterministic check results and DeepSeek dimension scores
into the final GEO readiness report.
"""

from rules.rubric import DIMENSIONS, DIMENSION_ORDER, compute_geo_readiness


SEVERITY_WEIGHT = {"high": 3, "medium": 2, "low": 1, "ok": 0}


def build_report(
    parsed: dict,
    det_checks: dict,
    dim_scores: dict,
) -> dict:
    """Build the full report object."""

    # Compute GEO readiness
    overall = compute_geo_readiness(dim_scores)

    # Collect all proof items across dimensions
    all_proof = []
    for dim_key in DIMENSION_ORDER:
        ds = dim_scores.get(dim_key, {})
        for p in ds.get("proof", []):
            all_proof.append({**p, "dimension": dim_key, "dimension_label": DIMENSIONS[dim_key]["label"]})

    # Sort proof by severity
    all_proof.sort(key=lambda x: SEVERITY_WEIGHT.get(x.get("severity", "low"), 0), reverse=True)

    # Collect strengths
    all_strengths = []
    for dim_key in DIMENSION_ORDER:
        ds = dim_scores.get(dim_key, {})
        for s in ds.get("strengths", []):
            all_strengths.append({"text": s, "dimension": DIMENSIONS[dim_key]["label"]})

    # Collect improvements
    all_improvements = []
    for dim_key in DIMENSION_ORDER:
        ds = dim_scores.get(dim_key, {})
        for imp in ds.get("improvements", []):
            all_improvements.append({"text": imp, "dimension": DIMENSIONS[dim_key]["label"]})

    # Top failing dimensions
    sorted_dims = sorted(
        [(k, dim_scores.get(k, {}).get("score", 50)) for k in DIMENSION_ORDER],
        key=lambda x: x[1]
    )
    top_weak = sorted_dims[:3]
    top_strong = sorted(sorted_dims, key=lambda x: x[1], reverse=True)[:3]

    # Deterministic summary
    det_failures = {k: v for k, v in det_checks.items() if not v.get("passed", True)}
    det_passes = {k: v for k, v in det_checks.items() if v.get("passed", True)}

    return {
        "overall_score": overall,
        "overall_label": score_label(overall),
        "word_count": parsed.get("word_count", 0),
        "sentence_count": parsed.get("sentence_count", 0),
        "heading_count": parsed.get("heading_count", 0),
        "dimension_scores": dim_scores,
        "dimension_order": DIMENSION_ORDER,
        "all_proof": all_proof[:12],
        "all_strengths": all_strengths[:6],
        "all_improvements": all_improvements[:8],
        "top_weak_dimensions": top_weak,
        "top_strong_dimensions": top_strong,
        "deterministic_failures": det_failures,
        "deterministic_passes": det_passes,
    }


def score_label(score: float) -> str:
    if score >= 85:
        return "GEO-Ready"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Needs Work"
    if score >= 40:
        return "Weak"
    return "Poor"


def report_to_markdown(report: dict, article_title: str = "Article") -> str:
    """Convert report to a clean markdown string for export."""
    lines = []
    lines.append(f"# GEO Readiness Report: {article_title}\n")
    lines.append(f"**Overall GEO Readiness: {report['overall_score']}/100 — {report['overall_label']}**\n")
    lines.append(f"Word count: {report['word_count']} | Sentences: {report['sentence_count']} | Headings: {report['heading_count']}\n")

    lines.append("---\n")
    lines.append("## Dimension Scores\n")
    for dim_key in report["dimension_order"]:
        ds = report["dimension_scores"].get(dim_key, {})
        label = DIMENSIONS[dim_key]["label"]
        score = ds.get("score", "N/A")
        reason = ds.get("reason_summary", "")
        lines.append(f"### {label}: {score}/100")
        lines.append(f"{reason}\n")

    lines.append("---\n")
    lines.append("## Top Issues Found (Evidence)\n")
    for item in report["all_proof"][:8]:
        lines.append(f"**{item.get('dimension_label', '')} | Severity: {item.get('severity', '')}**")
        lines.append(f"> \"{item.get('sentence', '')}\"")
        lines.append(f"Issue: {item.get('issue', '')}")
        lines.append(f"Why it matters: {item.get('why_it_matters', '')}")
        lines.append(f"Fix: {item.get('suggested_fix', '')}\n")

    lines.append("---\n")
    lines.append("## Strengths\n")
    for s in report["all_strengths"]:
        lines.append(f"- [{s['dimension']}] {s['text']}")

    lines.append("\n## Priority Fixes\n")
    for i, imp in enumerate(report["all_improvements"][:6], 1):
        lines.append(f"{i}. [{imp['dimension']}] {imp['text']}")

    return "\n".join(lines)
