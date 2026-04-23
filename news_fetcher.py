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


def _get_company_identifiers(ticker_obj: yf.Ticker) -> tuple[set[str], str]:
    """
    Return a tuple of:
      - set of identifier strings (for Stage 1 heuristic filter)
      - primary company name (for Stage 2 LLM relevance check)
    
    Example for TSLA: ({"tsla", "tesla, inc.", "tesla"}, "Tesla")
    """
    identifiers = set()
    primary_name = ""
    
    try:
        info = ticker_obj.info or {}
    except Exception:
        info = {}
    
    symbol = info.get("symbol", "")
    if symbol:
        identifiers.add(symbol.lower())
    
    short_name = info.get("shortName", "")
    if short_name:
        identifiers.add(short_name.lower())
        first_word = short_name.split(",")[0].split(" ")[0].strip()
        if len(first_word) >= 3:
            identifiers.add(first_word.lower())
            primary_name = first_word  # e.g., "Tesla" from "Tesla, Inc."
    
    long_name = info.get("longName", "")
    if long_name:
        identifiers.add(long_name.lower())
        first_word = long_name.split(",")[0].split(" ")[0].strip()
        if len(first_word) >= 3:
            identifiers.add(first_word.lower())
            if not primary_name:
                primary_name = first_word
    
    # Fallback: use the ticker if we somehow got no name
    if not primary_name:
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
    
    Stage 1 (heuristic): company name or ticker appears in title/summary.
    Stage 2 (LLM): article is primarily about the company, not just mentioning it.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")
        limit: Maximum number of RELEVANT news items to return
    
    Returns:
        List of dicts with title, publisher, link, summary.
    """
    stock = yf.Ticker(ticker)
    raw_news = stock.news or []
    identifiers, primary_name = _get_company_identifiers(stock)
    
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
    # Must mention the company somewhere in title or summary
    stage1 = [a for a in candidates if _is_relevant(a, identifiers)]
    
    # --- Stage 2: LLM relevance check ---
    # Ask the LLM whether the article is primarily about the company
    # We only run this on articles that passed stage 1, since stage 1 is ~free
    # and this step has a small LLM cost per call.
    print(f"  Filtering news for {ticker}: "
          f"{len(candidates)} raw → {len(stage1)} after stage 1...")
    
    stage2 = []
    for article in stage1:
        if is_article_about(
            title=article["title"],
            summary=article["summary"],
            ticker=ticker,
            company_name=primary_name
        ):
            stage2.append(article)
        # Early exit — if we have enough, stop making LLM calls
        if len(stage2) >= limit:
            break
    
    print(f"  → {len(stage2)} after stage 2 (LLM relevance check)")
    
    return stage2[:limit]


if __name__ == "__main__":
    print("Testing news fetcher with TSLA...\n")
    news = fetch_news("TSLA", limit=5)
    print(f"Returned {len(news)} relevant articles (after filtering):\n")
    for i, item in enumerate(news, 1):
        print(f"--- Article {i} ---")
        print(f"Title: {item['title']}")
        print(f"Publisher: {item['publisher']}")
        print(f"Summary preview: {item['summary'][:150]}...")
        print()