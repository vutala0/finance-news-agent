# Finance News Intelligence Agent

**Live demo: [finance-news-intelligence.streamlit.app](https://finance-news-intelligence.streamlit.app/)**

An AI-powered financial news classifier grounded in a Retrieval-Augmented Generation (RAG) pipeline. Enter a stock ticker, and the system fetches recent news, filters for substantive coverage through a two-stage relevance pipeline, and classifies each article by its likely impact on the stock — with retrieved historical precedents visible for every classification.

## Stack

- **Classification:** Google Gemini (Flash-Lite)
- **Embeddings:** Google `gemini-embedding-001`
- **Vector store:** ChromaDB (local persistence)
- **News source:** Finnhub API
- **UI:** Streamlit (deployed on Streamlit Cloud)

## Why This Project

Exploring the product–engineering tradeoffs of applying LLMs to financial information workflows — specifically:

- Structured output design with JSON schemas and fallback handling
- Prompt engineering for domain-specific classification tasks
- Separating retrieval quality from classification quality in evaluation

## Architecture

```
User input (ticker)
    ↓
news_fetcher.py  →  Yahoo Finance API
    ↓
classifier.py    →  Gemini API (structured JSON output)
    ↓
main.py          →  Orchestration + summary
```

### News Ingestion and Filtering

News is fetched from Yahoo Finance (via yfinance), then passed through a two-stage relevance filter:

1. **Stage 1 (heuristic):** company identifiers (ticker + canonical name) must appear in title or summary
2. **Stage 2 (LLM):** a Gemini Flash-Lite call per candidate article asks whether the article is primarily about the target company, not merely mentioning it

The cost-tiered cascade means LLM calls only run on articles that survived the heuristic, and we early-exit once we've collected enough relevant results. This pattern keeps the pipeline fast and cheap while catching the cases where simple string-matching fails (e.g., "Nike... Apple CEO Tim Cook" mentions Apple but isn't about Apple).

## Running Locally

```bash
# 1. Clone and enter the repo
git clone https://github.com/vutala0/finance-news-agent.git
cd finance-news-agent

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate    # Mac/Linux

# 3. Install dependencies
pip install google-generativeai yfinance python-dotenv

# 4. Add your Gemini API key
# Create a .env file in the project root with:
# GEMINI_API_KEY=your_key_here

# 5. Run
python main.py
```

## Design Notes

**Why Gemini 2.5 Flash-Lite?** For a classification task with clear criteria, a smaller/faster model is cost-optimal. Flagship models are reserved for genuinely ambiguous, multi-step reasoning.

**Why structured JSON output?** The LLM isn't just generating prose — it's functioning as a parser. Structured output allows downstream aggregation, summarization, and future evaluation.

**Why a `relevance` field?** Yahoo's ticker-tagged news often includes tangential items (competitor news, sector trends). The relevance score lets the pipeline distinguish "this is about the target company" from "this mentions the sector."

## Roadmap

- [x] Walking skeleton — end-to-end pipeline
- [x] Prompt iteration — ticker-aware classification with relevance scoring
- [x] Evaluation harness — hand-labeled test set + automated grading
- [x] Few-shot prompting experiment — regressed, reverted
- [x] RAG pipeline — ChromaDB + semantic retrieval of labeled precedents
- [x] Two-stage relevance filter — heuristic + LLM-based source quality control
- [x] Streamlit UI with RAG visualization
- [ ] Public deployment (Streamlit Cloud)
- [ ] Corpus expansion — grow golden set to 100+ items for meaningful RAG gains
- [ ] Market-outcome ground truth — objective price-based labels

## Evaluation

This project includes a full evaluation harness: a hand-labeled golden set of 25 real news items across 5 tickers (AAPL, TSLA, JPM, NVDA, BEN), a runner that benchmarks the classifier against ground truth, and an automatic report generator that surfaces failure patterns.

### Few-shot Experiment (Reverted)

Attempted to improve calibration by adding 5 labeled in-context examples. Two variants tested:

| Approach | Sentiment | Relevance |
| --- | --- | --- |
| Zero-shot baseline | 56% | 80% |
| Few-shot v1 (unbalanced) | 40% | 60% |
| Few-shot v2 (rebalanced) | 45% | 75% |

**Finding:** A small hand-curated example set (5 items) introduced more bias than it corrected. Distribution mismatches between the few-shot pool and the test set pushed the model's priors toward the examples' dominant labels. Concluded that with this small a test corpus, dynamic retrieval (RAG) is a better fit than static few-shot examples. See `reports/` for detailed analysis.

### Current Baseline

| Metric | Baseline | After prompt iteration |
| --- | --- | --- |
| Sentiment accuracy | 52% | **56%** (+4 pts) |
| Relevance accuracy | 68% | **80%** (+12 pts) |
| Both correct | 48% | **52%** (+4 pts) |

### Key Finding

Prompt iteration moved relevance accuracy significantly but barely moved sentiment accuracy. The failure modes are rooted in financial-domain calibration, not prompt wording — suggesting the next productive intervention is few-shot examples or retrieval of analogous historical cases, rather than further prompt tweaking.

Full reports are written to `/reports/` after each eval run.

### Running Evaluation

```bash
# 1. Run classifier against the golden set (writes to data/eval_results_*.json)
python eval_runner.py

# 2. Generate a readable Markdown report (writes to reports/eval_report_*.md)
python eval_report.py
```

### RAG Pipeline (Week 3)

Implemented full RAG pipeline: embedding with Google's gemini-embedding-001, storage in ChromaDB, semantic retrieval of top-3 similar precedents per query, with self-exclusion to prevent data leakage.

| Approach | Sentiment | Relevance |
| --- | --- | --- |
| Zero-shot baseline | 52-72% | 68-80% |
| Few-shot (static) | 35-45% | 60-75% |
| **RAG (dynamic retrieval)** | **60%** | **76%** |

**Key finding:** At this corpus size (25 items), RAG is statistically indistinguishable from a well-tuned zero-shot prompt. The failures are structural — they require financial-domain judgment no retrieval precedent can inject. RAG's value scales with corpus quality and size, not with pipeline sophistication.

See full RAG architecture in `build_index.py`, `retrieval.py`, and the retrieval-aware prompt in `classifier.py`.

## Built With

- Python 3.13
- Google Gemini API (2.5 Flash-Lite)
- yfinance for news ingestion
- python-dotenv for secrets management