# Finance News Intelligence Agent

An AI-powered tool that analyzes recent financial news for a given stock ticker and classifies each article by its likely impact on the stock price.

## What It Does

Given a stock ticker (e.g., `AAPL`, `TSLA`), the agent:

1. Fetches the most recent news articles from Yahoo Finance
2. Sends each article to Google Gemini for classification
3. Returns a structured sentiment (bullish / bearish / neutral) with confidence, relevance, and reasoning
4. Summarizes sentiment distribution across recent news

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
- [ ] Few-shot examples — inject calibration anchors into the prompt
- [ ] Retrieval improvements — semantic search over broader news corpus
- [ ] Agentic synthesis — multi-source reasoning across filings, news, and market data
- [ ] Web UI (Streamlit)
- [ ] Public deployment

## Evaluation

This project includes a full evaluation harness: a hand-labeled golden set of 25 real news items across 5 tickers (AAPL, TSLA, JPM, NVDA, BEN), a runner that benchmarks the classifier against ground truth, and an automatic report generator that surfaces failure patterns.

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

## Built With

- Python 3.13
- Google Gemini API (2.5 Flash-Lite)
- yfinance for news ingestion
- python-dotenv for secrets management