# GEO Article Scorer

A rule-backed article scoring app for Generative Engine Optimization (GEO).
Scores how well an article is written for AI answer systems like ChatGPT, Perplexity, and Gemini.

**No score without evidence. Every finding is quoted from the article.**

---

## What it does

Paste or upload any article. The app runs two layers of analysis:

**Layer 1: Deterministic checks** (no AI needed)
- Sentence atomicity check (compound/stacked claims)
- Heading structure detection
- FAQ presence
- Source mentions
- Paragraph density
- Filler language detection
- Average sentence length

**Layer 2: DeepSeek judgment** (per dimension, strict JSON output)
- Scores 8 GEO dimensions
- Returns quoted evidence from the article
- Gives specific rewrite instructions

---

## 8 Scoring Dimensions

| Dimension | Weight | What it measures |
|---|---|---|
| Answer-First | 15% | Is the core answer delivered early and clearly? |
| Atomicity | 12% | Are claims short, self-contained, and extractable? |
| Structural Clarity | 15% | Is the page scannable and AI-retrievable? |
| Query Fan-Out | 14% | Does the article cover adjacent user intents? |
| Citation Readiness | 16% | How quotable is it for AI answer engines? |
| Differentiation | 14% | Does it add something beyond commodity content? |
| Evidence Integrity | 8% | Are claims grounded and proportionate? |
| AI Extraction Fitness | 6% | Can it be chunked and retrieved cleanly? |

---

## Setup

```bash
# 1. Clone / unzip the project
cd geo_app

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your DeepSeek API key

# 5. Run the app
streamlit run app/main.py
```

---

## Get a DeepSeek API Key

Go to https://platform.deepseek.com and create an account. Top up balance and copy the API key. Add it to `.env` or paste it directly in the sidebar.

---

## Models used

- **Standard scoring:** `deepseek-chat` (fast, low cost)
- **Deep Audit mode:** `deepseek-reasoner` (slower, more thorough, higher cost)

---

## Architecture

```
app/main.py              Streamlit UI
rules/rubric.py          GEO scoring rubric (policy layer)
utils/parser.py          Article parser + deterministic checks
utils/deepseek_scorer.py DeepSeek API calls, one prompt per dimension
reports/report_builder.py Merges outputs into final report
```

The rubric defines the rules. DeepSeek applies them. It does not invent them.

---

## File support

- `.txt` — direct text
- `.pdf` — via pdfplumber
- `.docx` — via python-docx
- Paste — plain text area

---

## Export

Every scored report can be downloaded as a Markdown file.

---

## Important notes

1. Token costs scale with article length. Long articles are truncated to 6000 chars per scoring call.
2. Deep Audit mode costs more. Use it for final pre-publish audits.
3. The deterministic layer is real but heuristic. It catches visible patterns, not truth.
4. The app does not verify external factual accuracy against live sources.
