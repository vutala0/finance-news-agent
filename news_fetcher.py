"""
Fetches recent news for a given stock ticker from Yahoo Finance.

Includes a relevance pre-filter: articles that don't mention the target company
(by name or ticker) in the title or summary are dropped before being returned.
This prevents tangential news — articles about competitors, sector trends, or
unrelated topics that Yahoo happens to tag with the ticker — from polluting
downstream classification.
"""

import re
import yfinance as yf
from relevance_filter import is_article_about
from ticker_aliases import get_aliases, get_primary_name_override


def _get_company_identifiers(ticker_obj: yf.Ticker, ticker_symbol: str) -> tuple[set[str], str]:
    """
    Return a tuple of:
      - set of identifier strings (for Stage 1 heuristic filter)
      - primary company name (for Stage 2 LLM relevance check)
    
    Uses yfinance metadata first, then augments with manual aliases from 
    ticker_aliases.py for cases where Yahoo's data is misleading 
    (brand vs. legal name).
    """
    identifiers = set()
    primary_name = ""
    
    try:
        info = ticker_obj.info or {}
    except Exception:
        info = {}
    
    # From Yahoo metadata
    symbol = info.get("symbol", "") or ticker_symbol
    if symbol:
        identifiers.add(symbol.lower())
    
    short_name = info.get("shortName", "")
    if short_name:
        identifiers.add(short_name.lower())
        first_word = short_name.split(",")[0].split(" ")[0].strip()
        if len(first_word) >= 3:
            identifiers.add(first_word.lower())
            primary_name = first_word
    
    long_name = info.get("longName", "")
    if long_name:
        identifiers.add(long_name.lower())
        first_word = long_name.split(",")[0].split(" ")[0].strip()
        if len(first_word) >= 3:
            identifiers.add(first_word.lower())
            if not primary_name:
                primary_name = first_word
    
    # Augment with manual aliases (brand names, common synonyms)
    for alias in get_aliases(ticker_symbol):
        identifiers.add(alias.lower())
    
    # Override primary name if we have a manual one (better for LLM prompt)
    override = get_primary_name_override(ticker_symbol)
    if override:
        primary_name = override
    elif not primary_name:
        primary_name = symbol or "the company"
    
    return identifiers, primary_name


def _is_relevant(article: dict, identifiers: set[str]) -> bool:
    """
    Check whether an article is actually about the target company.
    
    Returns True if any identifier (ticker symbol or company name/brand) 
    appears in the title or summary. Case-insensitive.
    """
    searchable = f"{article['title']} {article['summary']}".lower()
    
    for ident in identifiers:
        if not ident:
            continue
        # Use word boundary matching for the ticker symbol to avoid 
        # matching AAPL inside "apples" or TSLA inside "crystalake"
        if len(ident) <= 5 and ident.isalpha():
            if re.search(rf"\b{re.escape(ident)}\b", searchable):
                return True
        else:
            # For longer strings (company names), substring match is fine
            if ident in searchable:
                return True
    return False


def fetch_news(ticker: str, limit: int = 5) -> list[dict]:
    """
    Fetch recent news articles for a given ticker, with two-stage filtering:
    
    Stage 1 (heuristic): company identifiers appear in title/summary.
    Stage 2 (LLM): article is genuinely useful to someone tracking the company.
    
    Fallback: if stage 1 rejects everything, skip stage 1 and rely on stage 2 
    alone. Handles cases where yfinance returns ticker-tagged articles whose 
    text doesn't explicitly name the company (rare but real).
    """
    stock = yf.Ticker(ticker)
    raw_news = stock.news or []
    identifiers, primary_name = _get_company_identifiers(stock, ticker)
    
    # Extract all candidates
    candidates = []
    for item in raw_news:
        content = item.get("content", {})
        candidates.append({
            "title": content.get("title", "No title"),
            "publisher": content.get("provider", {}).get("displayName", "Unknown"),
            "link": content.get("canonicalUrl", {}).get("url", ""),
            "summary": content.get("summary", ""),
        })
    
    # --- Stage 1: Heuristic filter ---
    stage1 = [a for a in candidates if _is_relevant(a, identifiers)]
    
    # Fallback: if heuristic rejected everything, let the LLM do all the work
    used_fallback = False
    if len(stage1) == 0 and len(candidates) > 0:
        stage1 = candidates
        used_fallback = True
    
    fallback_note = " (FALLBACK: heuristic found nothing, trusting yfinance tagging)" if used_fallback else ""
    print(f"  Filtering news for {ticker}: "
          f"{len(candidates)} raw → {len(stage1)} after stage 1{fallback_note}...")
    
    # --- Stage 2: LLM relevance check ---
    stage2 = []
    for article in stage1:
        if is_article_about(
            title=article["title"],
            summary=article["summary"],
            ticker=ticker,
            company_name=primary_name
        ):
            stage2.append(article)
        if len(stage2) >= limit:
            break
    
    print(f"  → {len(stage2)} after stage 2 (LLM relevance check)")
    
    return stage2[:limit]