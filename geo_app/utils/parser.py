"""
Content Parser + Deterministic Rule Engine
Extracts structure from article text and runs hard measurable checks.
These checks give proof that does not depend on model judgment.
"""

import re
from typing import Optional


def parse_article(text: str) -> dict:
    """Break raw article text into structured components."""
    lines = text.strip().split("\n")
    non_empty = [l.strip() for l in lines if l.strip()]

    headings = []
    paragraphs = []
    faq_blocks = []
    sentences_all = []
    current_para = []

    for line in non_empty:
        # Detect markdown headings
        if re.match(r"^#{1,4}\s+", line):
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
            headings.append(re.sub(r"^#{1,4}\s+", "", line).strip())
        # Detect FAQ-style lines
        elif re.match(r"^(Q:|FAQ|Question\s*\d*:|\d+\.\s+What|\d+\.\s+How|\d+\.\s+Why)", line, re.IGNORECASE):
            faq_blocks.append(line)
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
        else:
            current_para.append(line)

    if current_para:
        paragraphs.append(" ".join(current_para))

    # Extract all sentences
    full_text = " ".join(non_empty)
    raw_sentences = re.split(r"(?<=[.!?])\s+", full_text)
    sentences_all = [s.strip() for s in raw_sentences if len(s.strip()) > 20]

    # Intro = first 3 non-empty lines
    intro = " ".join(non_empty[:5]) if len(non_empty) >= 5 else " ".join(non_empty)

    # Source mentions
    source_pattern = re.compile(
        r"\b(according to|source:|cited in|data from|research by|published in|report by|study by)\b",
        re.IGNORECASE
    )
    source_mentions = [s for s in sentences_all if source_pattern.search(s)]

    return {
        "full_text": full_text,
        "lines": non_empty,
        "headings": headings,
        "paragraphs": paragraphs,
        "faq_blocks": faq_blocks,
        "sentences": sentences_all,
        "intro": intro,
        "source_mentions": source_mentions,
        "word_count": len(full_text.split()),
        "sentence_count": len(sentences_all),
        "heading_count": len(headings),
        "para_count": len(paragraphs),
    }


def run_deterministic_checks(parsed: dict) -> dict:
    """
    Hard measurable checks. These give proof independent of model opinion.
    Returns a dict of check results, each with a label, passed bool, proof, and severity.
    """
    checks = {}
    sentences = parsed["sentences"]
    headings = parsed["headings"]
    intro = parsed["intro"]
    paragraphs = parsed["paragraphs"]

    # --- Check 1: Answer in opening ---
    intro_word_count = len(intro.split())
    checks["intro_length"] = {
        "label": "Opening delivers answer quickly",
        "passed": intro_word_count < 80,
        "proof": f"Opening section is {intro_word_count} words.",
        "severity": "medium" if intro_word_count >= 80 else "ok",
        "detail": intro[:300],
    }

    # --- Check 2: Atomic sentences ---
    CLAUSE_CONNECTORS = ["because", "as", "while", "due to", "driven by", "resulting in",
                         "which", "that", "alongside", "in addition to", "combined with"]
    long_compound = []
    for s in sentences:
        word_count = len(s.split())
        connector_hits = sum(1 for c in CLAUSE_CONNECTORS if c in s.lower())
        comma_count = s.count(",")
        if word_count > 30 and (connector_hits >= 2 or comma_count >= 3):
            long_compound.append({
                "sentence": s,
                "words": word_count,
                "connectors": connector_hits,
                "commas": comma_count,
            })

    checks["compound_sentences"] = {
        "label": "Key claims are atomic (not bundled)",
        "passed": len(long_compound) == 0,
        "proof": f"{len(long_compound)} compound sentences detected out of {len(sentences)} total.",
        "severity": "high" if len(long_compound) > 5 else ("medium" if len(long_compound) > 2 else "ok"),
        "flagged": long_compound[:5],  # cap at 5 for display
    }

    # --- Check 3: Heading structure ---
    checks["heading_structure"] = {
        "label": "Clear heading structure present",
        "passed": len(headings) >= 2,
        "proof": f"{len(headings)} headings detected: {headings[:5]}",
        "severity": "high" if len(headings) == 0 else ("medium" if len(headings) == 1 else "ok"),
        "detail": headings,
    }

    # --- Check 4: FAQ presence ---
    has_faq = len(parsed["faq_blocks"]) > 0 or any(
        re.search(r"\b(FAQ|frequently asked|common questions)\b", h, re.IGNORECASE)
        for h in headings
    )
    checks["faq_presence"] = {
        "label": "FAQ or follow-up questions present",
        "passed": has_faq,
        "proof": f"FAQ blocks detected: {len(parsed['faq_blocks'])}.",
        "severity": "medium" if not has_faq else "ok",
    }

    # --- Check 5: Source mentions ---
    checks["source_mentions"] = {
        "label": "Source-backed claims present",
        "passed": len(parsed["source_mentions"]) >= 1,
        "proof": f"{len(parsed['source_mentions'])} source-attributed sentences found.",
        "severity": "medium" if len(parsed["source_mentions"]) == 0 else "ok",
        "detail": parsed["source_mentions"][:3],
    }

    # --- Check 6: Paragraph density ---
    long_paras = [p for p in paragraphs if len(p.split()) > 120]
    checks["paragraph_density"] = {
        "label": "No wall-of-text paragraphs",
        "passed": len(long_paras) == 0,
        "proof": f"{len(long_paras)} paragraphs exceed 120 words.",
        "severity": "medium" if len(long_paras) > 0 else "ok",
        "flagged": [p[:200] + "..." for p in long_paras[:3]],
    }

    # --- Check 7: Filler/generic language ---
    FILLER_PHRASES = [
        "in today's fast-paced", "in the ever-changing", "it goes without saying",
        "needless to say", "at the end of the day", "game-changer", "leverage",
        "synergies", "holistic approach", "best-in-class", "moving forward",
        "going forward", "circle back", "low-hanging fruit", "paradigm shift",
        "touch base", "bandwidth", "deep dive", "seamless", "robust solution",
    ]
    filler_hits = []
    for phrase in FILLER_PHRASES:
        if phrase in parsed["full_text"].lower():
            filler_hits.append(phrase)

    checks["filler_language"] = {
        "label": "Low generic filler language",
        "passed": len(filler_hits) == 0,
        "proof": f"{len(filler_hits)} generic filler phrases detected: {filler_hits[:8]}",
        "severity": "low" if len(filler_hits) <= 2 else ("medium" if len(filler_hits) <= 5 else "high"),
    }

    # --- Check 8: Average sentence length ---
    avg_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    checks["avg_sentence_length"] = {
        "label": "Average sentence length is reasonable",
        "passed": avg_len < 25,
        "proof": f"Average sentence length: {round(avg_len, 1)} words. Recommended: under 25.",
        "severity": "medium" if avg_len >= 25 else "ok",
    }

    return checks


def extract_text_from_file(uploaded_file) -> Optional[str]:
    """Extract plain text from uploaded .txt, .pdf, or .docx file."""
    filename = uploaded_file.name.lower()

    if filename.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="replace")

    if filename.endswith(".pdf"):
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                return "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
        except Exception as e:
            return f"PDF parse error: {e}"

    if filename.endswith(".docx"):
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(uploaded_file.read()))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            return f"DOCX parse error: {e}"

    return None
