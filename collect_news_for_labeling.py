"""
Collects news from multiple tickers into a single JSON file for manual labeling.
This generates the STARTING POINT for your golden dataset — you'll open the 
output file, add your labels, and save it as golden_set.json.

Usage:
    python collect_news_for_labeling.py
"""

import json
from news_fetcher import fetch_news

# Mix of tickers that should produce diverse news: tech, finance, auto, consumer
TICKERS_TO_SAMPLE = ["AAPL", "TSLA", "JPM", "NVDA", "BEN"]  # BEN = Franklin Templeton
ITEMS_PER_TICKER = 5

OUTPUT_FILE = "data/news_to_label.json"


def collect():
    all_items = []
    
    for ticker in TICKERS_TO_SAMPLE:
        print(f"Fetching news for {ticker}...")
        news = fetch_news(ticker, limit=ITEMS_PER_TICKER)
        
        for item in news:
            # Each record has the input fields + empty label fields to fill in
            record = {
                "ticker": ticker,
                "title": item["title"],
                "summary": item["summary"],
                "publisher": item["publisher"],
                # These are YOUR labels — fill them in manually
                "expected_sentiment": "FILL_ME_IN",      # bullish | bearish | neutral
                "expected_relevance": "FILL_ME_IN",      # high | medium | low
                "labeling_notes": ""                     # optional: why you chose this label
            }
            all_items.append(record)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Wrote {len(all_items)} items to {OUTPUT_FILE}")
    print("Next step: open that file and fill in expected_sentiment and expected_relevance for each item.")


if __name__ == "__main__":
    collect()