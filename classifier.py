"""
Classifies financial news items using the Gemini API.
Given a news title and summary, returns sentiment (bullish/bearish/neutral) 
with brief reasoning.
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv


# Load environment variables from .env file into the environment
load_dotenv()

# Configure the Gemini client with our API key
# os.getenv reads the variable we set in .env
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Did you create a .env file with your key?"
    )

genai.configure(api_key=api_key)

# Initialize the model — we're using Flash-Lite as it's fast and free-tier friendly
model = genai.GenerativeModel("gemini-2.5-flash-lite")


# The prompt is arguably the most important piece of code in this file.
# It's plain English, but it's ENGINEERING — every word matters.
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
- neutral = unclear or mixed signals
- relevance = how directly this news is about {ticker} (high = directly about the company; low = tangential or general industry news)
- If relevance is low, sentiment should usually be neutral
- Be conservative with "high" confidence — reserve it for very clear cases"""


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
    # Fill in the prompt template with the actual news content
    prompt = CLASSIFICATION_PROMPT.format(
    ticker=ticker.upper(),
    title=title,
    summary=summary
)
    
    # Send it to Gemini
    response = model.generate_content(prompt)
    
    # Gemini returns text. We asked for JSON — now we parse it.
    # Sometimes models wrap JSON in markdown code fences despite our prompt.
    # This strip handles that gracefully.
    text = response.text.strip()
    if text.startswith("```"):
        # Remove markdown fences if they slipped in
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # If Gemini gave us garbage, return a safe fallback
        result = {
            "sentiment": "neutral",
            "confidence": "low",
            "reasoning": f"Could not parse response: {text[:100]}"
        }
    
    return result


# Quick test when run directly
if __name__ == "__main__":
    print("Testing classifier with a sample headline...")
    result = classify_news(
        title="Apple reports record iPhone sales, beats Wall Street estimates",
        summary="Apple's Q4 earnings exceeded analyst expectations driven by strong iPhone demand in emerging markets.",
        ticker="AAPL"
    )
    print(json.dumps(result, indent=2))