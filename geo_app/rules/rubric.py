"""
GEO Scoring Rubric
Derived from the geo intelligence workbook (Level2_BestPractices).
This is the policy layer. DeepSeek applies the rubric. It does not invent it.
"""

DIMENSIONS = {
    "answer_first": {
        "label": "Answer-First Score",
        "weight": 0.15,
        "description": "Does the article resolve the core query early, clearly, and in a citable form?",
        "rules": [
            "BP-01: Lead paragraph must deliver the core answer within 2-4 lines.",
            "BP-01: Intro should state scope, conclusion, and qualifier before context.",
            "BP-01: Avoid scene-setting, history, or framing before the key takeaway.",
            "BP-01: The opening sentence should stand alone as a citable claim.",
        ],
        "prompt_instruction": """
Score how early and clearly the article delivers its core answer.
Check:
- Is the main answer given in the first 2-4 lines?
- Is the lead paragraph citable on its own?
- Does the intro spend too many sentences on context before the payoff?
- Does the opening resolve scope and conclusion, not just introduce the topic?
A high score means a reader (or AI) gets the core answer immediately and can quote the lead.
A low score means the answer is buried or the intro is mostly scene-setting.
""",
    },
    "atomicity": {
        "label": "Atomicity Score",
        "weight": 0.12,
        "description": "Are important claims short, self-contained, and directly extractable?",
        "rules": [
            "BP-02: Key claims should be written as short, standalone factual sentences.",
            "BP-02: Avoid bundling 3+ distinct ideas into one sentence.",
            "BP-02: Avoid chaining causal connectors: because, as, while, due to, driven by.",
            "BP-02: Each important sentence should be quotable in isolation.",
        ],
        "prompt_instruction": """
Score the atomicity of claims in the article.
Check:
- Are key sentences short and self-contained?
- Are multiple distinct ideas frequently packed into single sentences?
- Count how many critical sentences exceed ~30 words with multiple claim units.
- Can the important claims be quoted cleanly in isolation?
Flag exact problematic sentences. Show why each is non-atomic.
A high score means claims are clean, extractable, and quotable.
A low score means claims are dense, compound, and hard to cite.
""",
    },
    "structural_clarity": {
        "label": "Structural Clarity Score",
        "weight": 0.15,
        "description": "Is the page easy for humans and AI retrieval systems to scan and chunk?",
        "rules": [
            "BP-03: Use clear H2/H3 headings aligned to user intent.",
            "BP-03: Avoid wall-of-text paragraphs without section breaks.",
            "BP-03: Use tables, bullets, and FAQs where appropriate.",
            "BP-03: Sections should have clean topical boundaries.",
        ],
        "prompt_instruction": """
Score the structural clarity of the article.
Check:
- Are there clear H2/H3 sections with meaningful headings?
- Are paragraphs reasonably short (not walls of text)?
- Are tables, bullets, or FAQs used where they would help?
- Do sections have clean beginnings and endings that allow passage-level retrieval?
A high score means the page is scannable and AI-retrievable by section.
A low score means the content is structurally dense and hard to chunk.
""",
    },
    "query_fanout": {
        "label": "Query Fan-Out Score",
        "weight": 0.14,
        "description": "Does the article cover adjacent user intents beyond the main query?",
        "rules": [
            "BP-04: Cover comparisons, objections, follow-up questions, definitions, use cases, caveats.",
            "BP-04: Anticipate what a user would ask next after reading this.",
            "BP-04: Include at least one FAQ or intent-broadening section.",
            "BP-08: Treat content as serving a range of query variants, not one exact keyword.",
        ],
        "prompt_instruction": """
Score how well the article covers adjacent user intents.
Check:
- Does it address comparisons, objections, definitions, caveats, and use cases?
- What follow-up questions are missing?
- Is there a FAQ or equivalent that captures second-order intent?
- Does the article only answer one narrow query and ignore likely derivatives?
A high score means broad intent coverage with explicit sub-question handling.
A low score means narrow topic coverage with obvious gaps.
""",
    },
    "citation_readiness": {
        "label": "Citation Readiness Score",
        "weight": 0.16,
        "description": "How quotable and source-ready is the article for AI answer systems?",
        "rules": [
            "BP-05: State explicit conclusions, not just observations.",
            "BP-05: Source-backed factual claims should be compact and traceable.",
            "BP-05: Reduce promotional language, hedging, and filler.",
            "BP-05: Claims should be attributable without requiring full context.",
        ],
        "prompt_instruction": """
Score how citation-ready the article is for AI answer engines.
Check:
- Does the article contain explicit, quotable conclusions?
- Are factual claims compact and traceable?
- Is promotional language, vague hedging, or generic filler reducing cite-readiness?
- Can individual sentences be lifted cleanly into an answer without needing surrounding context?
A high score means the article is a reliable citation source.
A low score means it reads like promotional content or vague commentary.
""",
    },
    "differentiation": {
        "label": "Differentiation Score",
        "weight": 0.14,
        "description": "Does the article add something beyond commodity search content?",
        "rules": [
            "BP-06: Reject commodity paraphrase content.",
            "BP-06: Original synthesis, frameworks, or interpretation should be present.",
            "BP-06: Non-generic analysis, unique data arrangement, or proprietary framing adds value.",
            "BP-06: Avoid articles that merely summarize known ideas without a distinctive view.",
        ],
        "prompt_instruction": """
Score how differentiated the article is from commodity content.
Check:
- Does it add original synthesis, frameworks, or a distinctive point of view?
- Or is it primarily a paraphrase of commonly available information?
- Is there a unique structure, model, or interpretation that would not be found elsewhere?
- Would a reader get something they cannot find from a generic search result?
A high score means the article is genuinely non-commodity and adds a unique lens.
A low score means it summarizes known ideas without adding interpretive value.
""",
    },
    "evidence_integrity": {
        "label": "Evidence Integrity Score",
        "weight": 0.08,
        "description": "Do claims appear grounded and proportionate to the evidence presented?",
        "rules": [
            "BP-07: Claim-to-evidence ratio should be balanced.",
            "BP-07: Avoid unsupported assertions and overreach.",
            "BP-07: Vague words like 'significant', 'growing', 'major' without data are weak signals.",
            "BP-07: Confidence should not exceed evidence support.",
        ],
        "prompt_instruction": """
Score the evidence integrity of the article.
Check:
- Are important claims supported by evidence, data, or source mentions?
- Are directional claims like "significant growth" backed by numbers?
- Are there assertions where confidence clearly exceeds the evidence?
- Are vague qualifiers used to paper over thin support?
A high score means claims are well-grounded and proportionate.
A low score means the article overreaches with confidence that lacks support.
""",
    },
    "ai_extraction_fitness": {
        "label": "AI Extraction Fitness Score",
        "weight": 0.06,
        "description": "How easily can this article be chunked, retrieved, and included in generated answers?",
        "rules": [
            "BP-03: Passage boundaries should be clean.",
            "BP-01: Lead sentences in each section should be retrievable on their own.",
            "BP-03: Heading semantics should reflect true section content.",
            "BP-06: Low clutter, high signal per sentence.",
        ],
        "prompt_instruction": """
Score how AI-retrieval-friendly the article structure is.
Check:
- Are passage boundaries clean and logically segmented?
- Do section-opening sentences summarize the section in one line?
- Are headings semantically accurate to their content?
- Is signal density high (low filler, high meaningful content per sentence)?
A high score means the article can be chunked by AI and each chunk is meaningful.
A low score means sections bleed into each other or section openers are generic.
""",
    },
}

DIMENSION_ORDER = [
    "answer_first",
    "atomicity",
    "structural_clarity",
    "query_fanout",
    "citation_readiness",
    "differentiation",
    "evidence_integrity",
    "ai_extraction_fitness",
]

def compute_geo_readiness(scores: dict) -> float:
    total = 0.0
    for dim_key, info in DIMENSIONS.items():
        score = scores.get(dim_key, {}).get("score", 50)
        total += score * info["weight"]
    return round(total, 1)
