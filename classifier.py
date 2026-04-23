"""
Classifies financial news items using the Gemini API.
Given a news title and summary, returns sentiment (bullish/bearish/neutral) 
with brief reasoning.
"""

import os
import json
from google import genai
from dotenv import load_dotenv


# Load environment variables from .env file into the environment
load_dotenv()

# Configure the Gemini client with our API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Did you create a .env file with your key?"
    )

# Initialize the client
client = genai.Client(api_key=api_key)

# Using 2.5 Flash (not Flash-Lite) for better quality.
# Tradeoff: same free-tier rate cap but higher quality reasoning.
MODEL_NAME = "gemini-2.5-flash"


# Prompt design notes:
# - Explicit ticker context to prevent abstract reasoning
# - Relevance field to distinguish on-topic vs tangential news
# - Reasoning field for interpretability and failure debugging
# - Explicit guidance on directional calls: don't over-neutralize clear signals
CLASSIFICATION_PROMPT = """You are a financial news analyst. Classify the following news item 
for its likely impact on the stock price of {ticker}.

News Title: {title}
News Summary: {summary}

Respond with ONLY a valid JSON object in this exact format (no markdown, no extra text):
{{
  "sentiment": "bullish" | "bearish" | "neutral",
  "confidence": "high" | "medium" | "low",
  "reasoning": "One sentence explaining your classification specifically for {ticker}.",
  "relevance": "high" | "medium" | "low"
}}

Rules:
- bullish = likely positive impact on {ticker}'s stock price
- bearish = likely negative impact on {ticker}'s stock price
- neutral = only when signals are genuinely mixed, unclear, or the news is not 
  really about {ticker}
- relevance = how directly this news is about {ticker} (high = directly about 
  the company; low = tangential or general industry news)
- If relevance is low, sentiment should usually be neutral
- Major events (CEO departures, regulatory actions, earnings misses, supply 
  disruptions, analyst downgrades) ARE directional signals — do not default 
  to neutral just because the outcome is uncertain. Commit to bullish or bearish 
  when a reasonable investor would.
- "Be conservative with confidence" means using 'medium' or 'low' confidence 
  on unclear cases — it does NOT mean defaulting sentiment to neutral."""


def classify_news(title: str, summary: str, ticker: str) -> dict:
    """
    Send a news item to Gemini and get back a structured sentiment classification.
    
    Args:
        title: The news headline
        summary: Brief description of the news content
        ticker: The stock ticker this news is being analyzed for
    
    Returns:
        A dict with keys: sentiment, confidence, reasoning, relevance
    """
    prompt = CLASSIFICATION_PROMPT.format(
        ticker=ticker.upper(),
        title=title,
        summary=summary
    )
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {
            "sentiment": "neutral",
            "confidence": "low",
            "relevance": "low",
            "reasoning": f"Could not parse response: {text[:100]}"
        }
    
    return result


if __name__ == "__main__":
    print("Testing classifier with a sample headline...")
    result = classify_news(
        title="Apple reports record iPhone sales, beats Wall Street estimates",
        summary="Apple's Q4 earnings exceeded analyst expectations driven by strong iPhone demand in emerging markets.",
        ticker="AAPL"
    )
    print(json.dumps(result, indent=2))