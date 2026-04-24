"""
Fetches recent news for a given stock ticker from Finnhub.

Includes a two-stage relevance filter:
  Stage 1 (heuristic): company identifiers appear in title or summary
  Stage 2 (LLM): article is genuinely useful to someone tracking the company

Finnhub is used instead of yfinance because Yahoo Finance rate-limits 
datacenter IPs, making yfinance unreliable in cloud-hosted environments.
Finnhub provides a proper free-tier API (60 calls/minute) that works 
reliably from any IP.
"""

import re
from datetime import datetime, timedelta
from typing import Any

import requests

from config import get_finnhub_api_key
from relevance_filter import is_article_about
from ticker_aliases import get_aliases, get_primary_name_override


FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/company-news"
FINNHUB_PROFILE_URL = "https://finnhub.io/api/v1/stock/profile2"

# Cache company profiles for the duration of one process
# (avoids hitting the profile endpoint repeatedly for the same ticker)
_profile_cache: dict[str, dict] = {}


def _get_company_profile(ticker: str) -> dict:
    """
    Fetch company metadata (name, ticker, etc.) from Finnhub.
    Cached per-process for efficiency.
    """
    if ticker in _profile_cache:
        return _profile_cache[ticker]
    
    try:
        response = requests.get(
            FINNHUB_PROFILE_URL,
            params={"symbol": ticker, "token": get_finnhub_api_key()},
            timeout=10
        )
        response.raise_for_status()
        profile = response.json() or {}
    except Exception as e:
        print(f"  [profile] could not fetch profile for {ticker}: {e}")
        profile = {}
    
    _profile_cache[ticker] = profile
    return profile


def _get_company_identifiers(ticker: str) -> tuple[set[str], str]:
    """
    Return a tuple of:
      - set of identifier strings (for Stage 1 heuristic filter)
      - primary company name (for Stage 2 LLM relevance check)
    """
    identifiers = set()
    primary_name = ""
    
    profile = _get_company_profile(ticker)
    
    # Ticker symbol itself
    identifiers.add(ticker.lower())
    
    # Company name from Finnhub
    name = profile.get("name", "")
    if name:
        identifiers.add(name.lower())
        first_word = name.split(",")[0].split(" ")[0].strip()
        if len(first_word) >= 3:
            identifiers.add(first_word.lower())
            primary_name = first_word
    
    # Augment with manual aliases (brand names, common synonyms)
    for alias in get_aliases(ticker):
        identifiers.add(alias.lower())
    
    # Override primary name for the LLM prompt if we have a better one
    override = get_primary_name_override(ticker)
    if override:
        primary_name = override
    elif not primary_name:
        primary_name = ticker
    
    return identifiers, primary_name


def _is_relevant(article: dict, identifiers: set[str]) -> bool:
    """
    Stage 1 heuristic check: does any identifier appear in title or summary?
    """
    searchable = f"{article['title']} {article['summary']}".lower()
    for ident in identifiers:
        if not ident:
            continue
        if len(ident) <= 5 and ident.isalpha():
            # Word boundary match for short ticker symbols (avoid matching 
            # AAPL in "apples")
            if re.search(rf"\b{re.escape(ident)}\b", searchable):
                return True
        else:
            # Substring match for longer company names
            if ident in searchable:
                return True
    return False


def _fetch_raw_news(ticker: str, days_back: int = 7) -> list[dict]:
    """
    Fetch raw news articles from Finnhub for the given ticker.
    Returns a list of article dicts (pre-filter).
    """
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=days_back)
    
    try:
        response = requests.get(
            FINNHUB_NEWS_URL,
            params={
                "symbol": ticker,
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "token": get_finnhub_api_key()
            },
            timeout=15
        )
        response.raise_for_status()
        raw_items = response.json() or []
    except requests.exceptions.RequestException as e:
        print(f"  [finnhub] request failed for {ticker}: {e}")
        return []
    except Exception as e:
        print(f"  [finnhub] unexpected error for {ticker}: {e}")
        return []
    
    # Normalize Finnhub's shape to our internal schema
    articles = []
    for item in raw_items:
        articles.append({
            "title": item.get("headline", "No title"),
            "publisher": item.get("source", "Unknown"),
            "link": item.get("url", ""),
            "summary": item.get("summary", ""),
        })
    
    return articles


def fetch_news(ticker: str, limit: int = 5) -> list[dict]:
    """
    Fetch recent news articles for a given ticker, with two-stage filtering.
    
    Stage 1 (heuristic): company identifiers appear in title or summary.
    Stage 2 (LLM): article is genuinely useful to someone tracking the company.
    
    Fallback: if stage 1 rejects everything, skip stage 1 and rely on 
    stage 2 alone. Handles cases where the source tagged the article to the 
    ticker but didn't use the company name in title or summary.
    """
    identifiers, primary_name = _get_company_identifiers(ticker)
    
    # Pull up to ~50 recent articles so we have headroom for filtering
    candidates = _fetch_raw_news(ticker, days_back=14)
    
    # Sort by... Finnhub returns recent-first by default, which is what we want.
    # Limit the candidate pool to keep LLM filter cost bounded.
    candidates = candidates[:50]
    
    # --- Stage 1: Heuristic filter ---
    stage1 = [a for a in candidates if _is_relevant(a, identifiers)]
    
    # Fallback: if heuristic rejected everything, let the LLM do all the work
    used_fallback = False
    if len(stage1) == 0 and len(candidates) > 0:
        stage1 = candidates
        used_fallback = True
    
    fallback_note = " (FALLBACK)" if used_fallback else ""
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


if __name__ == "__main__":
    print("Testing Finnhub news fetcher with TSLA...\n")
    news = fetch_news("TSLA", limit=5)
    print(f"\nReturned {len(news)} relevant articles:\n")
    for i, item in enumerate(news, 1):
        print(f"--- Article {i} ---")
        print(f"Title: {item['title']}")
        print(f"Publisher: {item['publisher']}")
        print(f"Summary: {item['summary'][:150]}...")
        print()