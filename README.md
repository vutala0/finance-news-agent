# Finance News Intelligence Agent

**Live demo: [finance-news-intelligence.streamlit.app](https://finance-news-intelligence.streamlit.app/)**

An AI-powered financial news classifier grounded in a Retrieval-Augmented Generation (RAG) pipeline. Enter a stock ticker, and the system fetches recent news, filters for substantive coverage through a two-stage relevance pipeline, classifies each article by its likely impact on the stock price, and surfaces the retrieved historical precedents that informed each classification.

Built as a hands-on AI product management portfolio project — the goal was to ship a real, deployable AI product end-to-end while practicing the eval-driven development loop that real AI teams use.

---

## What it does

Given a stock ticker like `AAPL` or `TSLA`, the system:

1. Fetches the last ~14 days of news articles from Finnhub
2. Filters out tangential articles through a two-stage relevance pipeline
3. For each remaining article, retrieves the 3 most similar hand-labeled precedents from a vector database
4. Classifies each article as bullish, bearish, or neutral using Gemini with the retrieved precedents as context
5. Aggregates the results into a market mood indicator and presents each article with its classification, reasoning, and visible precedents

The live UI is a Streamlit app with a Tickertape-inspired aesthetic — dense financial-data typography, a segmented mood bar, and inline-expandable precedent cards.

---

## Architecture

### News ingestion and relevance filtering

News is fetched from the Finnhub API, chosen over Yahoo Finance (via `yfinance`) because Yahoo rate-limits cloud datacenter IPs, making Yahoo-sourced apps unreliable in production environments.

Every article passes through a two-stage relevance filter before classification:

- **Stage 1 (heuristic):** deterministic string matching — does the company's ticker or canonical name appear in the title or summary? Fast, free, catches obvious tangential coverage.
- **Stage 2 (LLM):** a lightweight Gemini Flash-Lite call per candidate, asking whether the article is genuinely useful to someone tracking the company. Catches the cases where the company is mentioned but isn't the subject.

The cost-tiered cascade means the LLM check only runs on articles that survived the cheap heuristic, and the pipeline early-exits once enough relevant articles have been collected. This pattern keeps per-query cost and latency bounded while still catching nuanced edge cases like "Nike is now the highest-yielding dividend stock... Should you follow Apple CEO Tim Cook's lead?" — which mentions Apple but isn't about it.

A small manual alias file (`ticker_aliases.py`) handles cases where a brand name and legal name differ (Google/Alphabet, Meta/Facebook, etc.). A fallback skips the heuristic stage entirely when it rejects every candidate, trusting the source's ticker tagging and letting the LLM do all the filtering.

### RAG pipeline

The retrieval layer is built on three components:

- **Embedding model:** Google `gemini-embedding-001`
- **Vector store:** ChromaDB with local persistent storage
- **Corpus:** 25 hand-labeled historical news items across AAPL, TSLA, JPM, NVDA, and BEN, each tagged with sentiment, relevance, and reasoning notes

At classification time, the query article is embedded, the top-3 most similar past items are retrieved (with self-exclusion to prevent data leakage during evaluation), and those retrieved items are injected into the classifier prompt as reasoning anchors. The LLM sees both the new article and three historical precedents with their correct labels.

### Classification

Each article is classified by a structured Gemini prompt that asks for:

- **sentiment** — bullish, bearish, or neutral
- **confidence** — high, medium, low
- **relevance** — how directly the news is about the target ticker
- **reasoning** — one-sentence explanation grounded in the article and the precedents

Retry-with-backoff logic handles 429 rate limits and 503 transient errors. JSON parsing falls back gracefully when the LLM response is malformed.

### Evaluation harness

The project includes a full offline evaluation loop:

- `data/golden_set.json` — hand-labeled ground truth (25 items)
- `validate_golden_set.py` — schema validator for labels (catches typos like "nutral" → "neutral")
- `eval_runner.py` — runs the classifier against the golden set and writes timestamped results to `data/`
- `eval_report.py` — generates human-readable Markdown reports in `reports/` with failure pattern analysis (over-neutralized, over-directional, wrong-direction)

---

## Evaluation results

The classifier was benchmarked at each major iteration point. The goal was to practice the full eval-driven development loop: baseline, hypothesize, intervene, measure, compare, decide.

| Iteration | Sentiment accuracy | Relevance accuracy |
| --- | --- | --- |
| Zero-shot baseline | 52% | 68% |
| Prompt iteration (ticker context + relevance field) | 56-72%* | 72-80%* |
| Few-shot (unbalanced 5-item pool) | 40% | 60% |
| Few-shot (rebalanced) | 45% | 75% |
| **RAG with semantic retrieval** | **60%** | **76%** |

*Range reflects run-to-run variance on the same test set. LLM evaluations are inherently stochastic — single-run numbers have ±10 point noise.

### Key findings

- **Prompt engineering has a ceiling.** Moving from a bare prompt to a ticker-aware, relevance-tagged prompt improved relevance accuracy significantly (+12 points) but barely moved sentiment accuracy (+4 points). Scoping can be taught through prompts; financial-domain directional judgment cannot.
- **Static few-shot examples regressed accuracy.** A 5-item hand-picked few-shot pool introduced distribution-mismatch bias — the model's priors tilted toward the dominant label mix in the example set, hurting performance on cases unlike the examples. Dynamic retrieval (RAG) sidesteps this.
- **RAG at this corpus size is roughly on par with a well-tuned zero-shot prompt.** With only 25 precedents, retrieval often returns similar-but-also-ambiguous cases for the hardest inputs. RAG's value scales with corpus size and quality, not with pipeline sophistication.
- **Ground-truth quality is the real ceiling.** The labels reflect a single non-expert author's judgment. Bounds on accuracy here reflect bounds on labeling consistency as much as bounds on the model. A future iteration would replace opinion-based labels with objective market-outcome labels (price movement in the N days following publication).

Full eval reports with per-run failure pattern analysis live in `reports/`.

---

## Tech stack

- **Classification & filtering:** Google Gemini (Flash-Lite via `google-genai` SDK)
- **Embeddings:** Google `gemini-embedding-001`
- **Vector store:** ChromaDB with persistent local storage
- **News source:** Finnhub API (free tier, 60 calls/minute)
- **UI:** Streamlit with custom CSS (Manrope + JetBrains Mono typography)
- **Deployment:** Streamlit Cloud
- **Language:** Python 3.11

---

## Running locally

```bash
# Clone the repo
git clone https://github.com/vutala0/finance-news-agent.git
cd finance-news-agent

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env with your API keys
echo "GEMINI_API_KEY=your_gemini_key_here" > .env
echo "FINNHUB_API_KEY=your_finnhub_key_here" >> .env

# Build the vector index (one-time setup)
python build_index.py

# Run the app
streamlit run app.py
```

Get a free Gemini API key at [ai.google.dev](https://ai.google.dev/) and a free Finnhub key at [finnhub.io/register](https://finnhub.io/register).

---

## Running evaluation

```bash
# 1. Run the classifier against the golden set
python eval_runner.py

# 2. Generate a readable Markdown report
python eval_report.py
```

Results are written to `data/eval_results_<timestamp>.json` and `reports/eval_report_<timestamp>.md`. Each report groups failures by error pattern and leaves a section for hand-written interpretation to accumulate learnings run-over-run.

---

## Roadmap

- [x] Walking skeleton — end-to-end pipeline
- [x] Prompt iteration — ticker-aware classification with relevance scoring
- [x] Evaluation harness — hand-labeled test set + automated grading
- [x] Few-shot prompting experiment — regressed, reverted
- [x] RAG pipeline — ChromaDB + semantic retrieval of labeled precedents
- [x] Two-stage relevance filter — heuristic + LLM-based source quality control
- [x] Streamlit UI with RAG visualization
- [x] Public deployment with Finnhub integration
- [ ] Market-outcome ground truth — replace opinion-based labels with objective price-movement labels
- [ ] Corpus expansion — grow golden set to 100+ items for meaningful RAG gains
- [ ] Retrieval instrumentation — measure retrieval quality (precision@k, relevance@k) separately from end-to-end accuracy
- [ ] Near-duplicate detection — cluster and deduplicate articles covering the same event

---

## What this project is not

- It is not investment advice. Classifications are experimental and should not drive trading decisions.
- It is not production-grade at scale. The corpus is small, the labels reflect one author's judgment, and the filtering is tuned for precision over recall.
- It is not a finished product — it is a hands-on portfolio piece designed to practice the full AI product development loop, from walking skeleton through iteration and deployment.

---

## About the build

This project was built end-to-end as a ~2-week AI PM portfolio exercise. The goal was to practice, in sequence: scoping an AI problem, building a walking skeleton, adding evaluation infrastructure before features, iterating on prompts, attempting and diagnosing a failed few-shot experiment, shipping a RAG pipeline, adding production-grade filtering, building a polished UI, and deploying publicly.

Notable decisions and lessons are captured in commit messages and in the eval reports under `reports/`. If you're a recruiter or hiring manager interested in how I think about AI products, the commit log tells the story better than any resume line.

Built by **[Prashanth Vutala](https://www.linkedin.com/in/vutalap/)** — actively exploring AI Product Manager roles.