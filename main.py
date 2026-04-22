"""
Main entry point for the Financial News Intelligence Agent.
Takes a ticker, fetches news, classifies each item, and prints a summary.
"""

from news_fetcher import fetch_news
from classifier import classify_news


# ANSI color codes — makes the terminal output more readable
# Don't worry about memorizing these
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def sentiment_color(sentiment: str) -> str:
    """Return the ANSI color code for a given sentiment label."""
    return {
        "bullish": GREEN,
        "bearish": RED,
        "neutral": YELLOW,
    }.get(sentiment.lower(), RESET)


def analyze_ticker(ticker: str, num_articles: int = 5) -> None:
    """
    Full pipeline: fetch news for a ticker, classify each item, print results.
    
    Args:
        ticker: Stock ticker symbol
        num_articles: How many recent news items to analyze
    """
    print(f"\n{BOLD}Analyzing {ticker.upper()}...{RESET}")
    print(f"Fetching {num_articles} recent news items...\n")
    
    news_items = fetch_news(ticker, limit=num_articles)
    
    if not news_items:
        print("No news found for this ticker.")
        return
    
    # Track summary stats
    sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
    
    for i, item in enumerate(news_items, 1):
        print(f"{BOLD}--- Article {i} ---{RESET}")
        print(f"Title: {item['title']}")
        print(f"Publisher: {item['publisher']}")
        
        # Classify this news item
        result = classify_news(item["title"], item["summary"], ticker)
        
        # Color-code the sentiment for readability
        color = sentiment_color(result["sentiment"])
        print(f"Sentiment: {color}{result['sentiment'].upper()}{RESET} "
      f"(confidence: {result['confidence']}, relevance: {result['relevance']})")
        print(f"Reasoning: {result['reasoning']}")
        print()
        
        # Count it
        sentiment = result["sentiment"].lower()
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
    
    # Print summary
    print(f"{BOLD}=== Summary for {ticker.upper()} ==={RESET}")
    print(f"{GREEN}Bullish: {sentiment_counts['bullish']}{RESET}")
    print(f"{RED}Bearish: {sentiment_counts['bearish']}{RESET}")
    print(f"{YELLOW}Neutral: {sentiment_counts['neutral']}{RESET}")


if __name__ == "__main__":
    # Simple CLI: ask the user for a ticker
    ticker_input = input("Enter a stock ticker (e.g., AAPL, MSFT, TSLA): ").strip()
    
    if not ticker_input:
        print("No ticker provided. Exiting.")
    else:
        analyze_ticker(ticker_input, num_articles=5)