"""
DeepSeek Scorer
One prompt per dimension. Strict JSON output.
DeepSeek is the judgment layer. The rubric is the policy layer.
"""

import json
import os
from openai import OpenAI
from rules.rubric import DIMENSIONS


def get_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )


SCORE_JSON_SCHEMA = """
{
  "dimension": "<dimension_key>",
  "score": <integer 0-100>,
  "confidence": "<low|medium|high>",
  "reason_summary": "<2-3 sentence explanation of the score>",
  "proof": [
    {
      "section": "<section name or 'General'>",
      "sentence": "<exact sentence from the article>",
      "issue": "<short issue label>",
      "why_it_matters": "<why this hurts GEO score>",
      "severity": "<low|medium|high>",
      "suggested_fix": "<one concrete rewrite instruction>"
    }
  ],
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<action 1>", "<action 2>", "<action 3>"]
}
"""


def score_dimension(
    dimension_key: str,
    article_text: str,
    api_key: str,
    deep_mode: bool = False,
    max_chars: int = 6000,
) -> dict:
    """Score one dimension using DeepSeek. Returns parsed JSON dict."""
    dim = DIMENSIONS[dimension_key]
    model = (
        os.getenv("DEEPSEEK_REASONER_MODEL", "deepseek-reasoner")
        if deep_mode
        else os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    )

    truncated_text = article_text[:max_chars]
    if len(article_text) > max_chars:
        truncated_text += "\n\n[Article truncated for scoring. Above is the first 6000 chars.]"

    rules_block = "\n".join(f"- {r}" for r in dim["rules"])

    system_prompt = f"""You are a precise GEO (Generative Engine Optimization) article auditor.
Your job is to score articles on specific dimensions using a strict rubric.
You always return valid JSON only. No prose, no markdown fences, no commentary outside JSON.
The JSON schema you must follow exactly is:
{SCORE_JSON_SCHEMA}

Rules for this dimension:
{rules_block}

Scoring scale:
0-39: Poor. Major violations, the article fails this dimension clearly.
40-59: Below average. Significant issues but some passing elements.
60-74: Average. Mixed. Some good, clear weaknesses.
75-89: Good. Above average with minor issues.
90-100: Excellent. Strong execution, minimal or no issues.

Important instructions:
- Quote exact sentences from the article for proof. Do not paraphrase them.
- Only flag real issues. Do not invent problems.
- Be direct. Flattery reduces the value of the audit.
- Provide 1-4 proof items. More than 4 dilutes focus.
- Strengths and improvements must be specific to this article, not generic advice.
"""

    user_prompt = f"""Score the following article on this dimension: {dim['label']}

Dimension description: {dim['description']}

Scoring instructions:
{dim['prompt_instruction']}

Article text:
---
{truncated_text}
---

Return only the JSON object. No other text."""

    client = get_client(api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=1500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.choices[0].message.content
        result = json.loads(raw)
        result["dimension"] = dimension_key
        return result

    except json.JSONDecodeError as e:
        return {
            "dimension": dimension_key,
            "score": 50,
            "confidence": "low",
            "reason_summary": f"JSON parse error from model: {e}",
            "proof": [],
            "strengths": [],
            "improvements": ["Re-run scoring for this dimension."],
            "error": True,
        }
    except Exception as e:
        return {
            "dimension": dimension_key,
            "score": 50,
            "confidence": "low",
            "reason_summary": f"API error: {e}",
            "proof": [],
            "strengths": [],
            "improvements": [],
            "error": True,
        }


def score_all_dimensions(
    article_text: str,
    api_key: str,
    deep_mode: bool = False,
    progress_callback=None,
) -> dict:
    """Score all 8 dimensions. Returns dict keyed by dimension name."""
    from rules.rubric import DIMENSION_ORDER
    results = {}
    for i, dim_key in enumerate(DIMENSION_ORDER):
        if progress_callback:
            progress_callback(i, dim_key)
        results[dim_key] = score_dimension(dim_key, article_text, api_key, deep_mode)
    return results
