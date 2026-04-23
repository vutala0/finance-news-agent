"""
LLM-based relevance filter for news articles.

Given an article and a target company, asks an LLM whether the article is 
PRIMARILY about that company (as opposed to merely mentioning it).

This is Stage 2 of our news relevance pipeline. Stage 1 (in news_fetcher.py) 
does cheap heuristic filtering — company name appears somewhere. Stage 2 (this 
module) catches the cases where the company is mentioned but isn't the subject.

Design notes:
- Uses the same Gemini model as the main classifier for consistency
- Asks a single binary question to keep latency and cost minimal
- Tolerates API failures gracefully (degrades to "probably relevant" rather 
  than dropping articles incorrectly on transient errors)
"""

import os
from google import genai
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

_client = genai.Client(api_key=api_key)

# Use Flash-Lite for the relevance check — this is a simple yes/no question
# and we want the cheapest model possible to keep the filter fast.
MODEL_NAME = "gemini-2.5-flash-lite"


RELEVANCE_PROMPT = """Is the following article PRIMARILY about {company_name} ({ticker})?

"Primarily about" means {company_name} is the main subject — its earnings, 
products, leadership, strategy, stock, or specific events affecting it.

"NOT primarily about" means {company_name} is only mentioned in passing, 
or the article is mostly about a competitor, a sector trend, or a different 
company that happens to reference {company_name}.

Article Title: {title}
Article Summary: {summary}

Respond with ONLY one word: YES or NO.

YES = the article is primarily about {company_name}
NO = {company_name} is only mentioned, the article is about something else"""


def is_article_about(title: str, summary: str, ticker: str, company_name: str) -> bool:
    """
    Use the LLM to judge whether an article is primarily about the target company.
    
    Args:
        title: Article headline
        summary: Article summary
        ticker: Stock ticker
        company_name: Full or short company name (e.g., "Apple", "JPMorgan Chase")
    
    Returns:
        True if the article is primarily about the company.
        On API failure, returns True (fail-open) — we'd rather show a borderline 
        article than lose articles due to a transient LLM hiccup.
    """
    prompt = RELEVANCE_PROMPT.format(
        company_name=company_name,
        ticker=ticker.upper(),
        title=title,
        summary=summary or "(no summary available)"
    )
    
    try:
        response = _client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        answer = (response.text or "").strip().upper()
        
        # Accept either a leading YES/NO or the word appearing prominently.
        # Defensive parsing — LLMs sometimes add extra whitespace or punctuation.
        if answer.startswith("YES"):
            return True
        if answer.startswith("NO"):
            return False
        
        # Unexpected output — log it and default to keeping the article.
        print(f"  [relevance filter] unexpected response: '{answer[:50]}' — keeping article")
        return True
    
    except Exception as e:
        # Fail-open on any API error — don't drop articles for transient issues
        print(f"  [relevance filter] API error: {e} — keeping article")
        return True


if __name__ == "__main__":
    # Quick test — simulate two cases
    print("Test 1: article genuinely about Apple")
    result1 = is_article_about(
        title="Apple reports record iPhone sales, beats Wall Street estimates",
        summary="Apple's Q4 earnings exceeded analyst expectations...",
        ticker="AAPL",
        company_name="Apple"
    )
    print(f"  is_about Apple: {result1} (expected True)\n")
    
    print("Test 2: article mentions Apple but is really about Nike")
    result2 = is_article_about(
        title="Nike Is Now the Third Highest-Yielding Dividend Stock in the Dow Jones Industrial Average. Should You Follow Apple CEO Tim Cook's Lead and Buy Nike Near a 10-Year Low?",
        summary="Nike stock has fallen sharply. Apple CEO Tim Cook is known for his long-term investing approach...",
        ticker="AAPL",
        company_name="Apple"
    )
    print(f"  is_about Apple: {result2} (expected False)\n")