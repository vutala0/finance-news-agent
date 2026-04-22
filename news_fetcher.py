"""
Fetches recent news for a given stock ticker from Yahoo Finance.
This module has one job: given a ticker symbol, return a list of news items.
"""

import yfinance as yf


def fetch_news(ticker: str, limit: int = 5) -> list[dict]:
    """
    Fetch recent news articles for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "MSFT")
        limit: Maximum number of news items to return
    
    Returns:
        A list of dictionaries, each representing one news item.
        Each dict contains: title, publisher, link, and summary.
    """
    stock = yf.Ticker(ticker)
    raw_news = stock.news
    
    cleaned_news = []
    for item in raw_news[:limit]:
        content = item.get("content", {})
        
        cleaned_news.append({
            "title": content.get("title", "No title"),
            "publisher": content.get("provider", {}).get("displayName", "Unknown"),
            "link": content.get("canonicalUrl", {}).get("url", ""),
            "summary": content.get("summary", ""),
        })
    
    return cleaned_news


if __name__ == "__main__":
    print("Testing news fetcher with AAPL...")
    news = fetch_news("AAPL", limit=3)
    for i, item in enumerate(news, 1):
        print(f"\n--- Article {i} ---")
        print(f"Title: {item['title']}")
        print(f"Publisher: {item['publisher']}")
        print(f"Summary: {item['summary'][:200]}...")