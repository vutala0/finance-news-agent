"""
Manual brand-name aliases for common tickers where Yahoo Finance's metadata 
is misleading or incomplete.

Yahoo typically returns the legal name (e.g., "Alphabet Inc.") for the 
'shortName' and 'longName' fields. News articles, however, overwhelmingly 
use the brand name (e.g., "Google"). Without these aliases, articles would 
fail our stage-1 heuristic filter.

This mapping is deliberately hand-curated — it reflects domain knowledge about 
brand vs. legal name differences that no automated system reliably handles.
"""

# Maps ticker symbol → list of additional identifier strings to add to the 
# matching set. All values will be lowercased for case-insensitive matching.
TICKER_ALIASES = {
    "GOOG": ["google", "alphabet"],
    "GOOGL": ["google", "alphabet"],
    "META": ["meta", "facebook", "instagram", "whatsapp"],
    "FB": ["facebook", "meta"],
    "BRK.A": ["berkshire", "buffett"],
    "BRK.B": ["berkshire", "buffett"],
    "SQ": ["block", "square"],
    "TWTR": ["twitter", "x corp"],
    "JPM": ["jpmorgan", "jpm", "chase", "j.p. morgan"],
    "BAC": ["bank of america"],
    "WFC": ["wells fargo"],
    "MS": ["morgan stanley"],
    "GS": ["goldman sachs", "goldman"],
    "BEN": ["franklin resources", "franklin templeton", "franklin"],
    "BLK": ["blackrock"],
    "AAPL": ["apple"],
    "TSLA": ["tesla"],
    "NVDA": ["nvidia"],
    "AMZN": ["amazon"],
    "MSFT": ["microsoft"],
    "NFLX": ["netflix"],
    "DIS": ["disney", "walt disney"],
    "COST": ["costco"],
    "WMT": ["walmart"],
    # Also a primary brand name for the LLM prompt when Yahoo's name is bad
}

# Override the "primary name" for the LLM relevance prompt for certain tickers.
# Used when Yahoo's returned name would confuse the LLM — e.g., "Alphabet" is 
# technically correct but news rarely uses it.
PRIMARY_NAME_OVERRIDES = {
    "GOOG": "Google",
    "GOOGL": "Google",
    "META": "Meta",
    "FB": "Meta (Facebook)",
    "BRK.A": "Berkshire Hathaway",
    "BRK.B": "Berkshire Hathaway",
    "SQ": "Block (formerly Square)",
    "JPM": "JPMorgan Chase",
    "BEN": "Franklin Resources (Franklin Templeton)",
    "BLK": "BlackRock",
    "GS": "Goldman Sachs",
}


def get_aliases(ticker: str) -> list[str]:
    """Return additional identifier strings for a ticker, or empty list."""
    return TICKER_ALIASES.get(ticker.upper(), [])


def get_primary_name_override(ticker: str) -> str | None:
    """Return an override for the LLM primary_name, or None to use yfinance's."""
    return PRIMARY_NAME_OVERRIDES.get(ticker.upper())