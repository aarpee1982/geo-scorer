"""
Smoke test. Runs without a DeepSeek API key.
Tests parser and deterministic checks only.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.parser import parse_article, run_deterministic_checks
from rules.rubric import DIMENSIONS, DIMENSION_ORDER, compute_geo_readiness
from reports.report_builder import build_report, report_to_markdown

SAMPLE = """
## Introduction

The global beverage market is expected to experience substantial growth during the forecast period, driven by a combination of urbanization, rising income levels, premiumization trends, shifting consumer preferences, regulatory pressures, and the emergence of new distribution channels across multiple regions.

## Market Drivers

According to a 2023 industry report, premium beverage segments are growing at twice the rate of the overall market.

Growth is supported by urbanization and rising income levels.

## Key Challenges

Regulatory pressure and supply chain disruption remain significant hurdles for manufacturers.

## FAQ

Q: What is driving beverage market growth?
A: Urbanization and premiumization are the primary drivers.

Q: What are the main challenges?
A: Regulatory pressure and supply chain issues.
"""

parsed = parse_article(SAMPLE)
checks = run_deterministic_checks(parsed)

print("=== PARSER OUTPUT ===")
print(f"Words: {parsed['word_count']}")
print(f"Sentences: {parsed['sentence_count']}")
print(f"Headings: {parsed['headings']}")
print(f"FAQs: {parsed['faq_blocks']}")
print(f"Sources: {parsed['source_mentions']}")

print("\n=== DETERMINISTIC CHECKS ===")
for k, v in checks.items():
    status = "PASS" if v["passed"] else "FAIL"
    print(f"[{status}] {v['label']}: {v['proof']}")

# Fake scores for report test
fake_scores = {k: {"score": 65, "confidence": "medium", "reason_summary": "Test.", "proof": [], "strengths": [], "improvements": []} for k in DIMENSION_ORDER}
report = build_report(parsed, checks, fake_scores)
md = report_to_markdown(report, "Test Article")
print(f"\n=== REPORT BUILT ===\nOverall: {report['overall_score']}")
print("Smoke test passed.")
