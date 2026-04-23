"""
Classifies financial news items using the Gemini API.
Given a news title and summary, returns sentiment (bullish/bearish/neutral) 
with brief reasoning.

Includes retry-with-backoff logic to handle rate limits (429) and transient
service unavailability (503) gracefully.
"""

import os
import json
import re
import time
from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Did you create a .env file with your key?"
    )

client = genai.Client(api_key=api_key)

# Using 2.5 Flash for reasoning quality.
# Free-tier rate limit: 5 requests/minute, 500/day.
MODEL_NAME = "gemini-2.5-flash-lite"

# Retry configuration
MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 2
MAX_BACKOFF_SECONDS = 60


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


def _extract_retry_delay(error_message: str) -> float | None:
    """
    Try to parse a 'Please retry in Xs' hint from a rate-limit error message.
    Returns the suggested wait in seconds, or None if we can't find one.
    """
    match = re.search(r"retry in ([\d.]+)\s*s", error_message, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _call_gemini_with_retry(prompt: str) -> str:
    """
    Call the Gemini API with exponential backoff on rate-limit and transient errors.
    
    Retry policy:
    - 429 (rate limit): honor the server's retry-after hint if provided, 
      otherwise exponential backoff
    - 503 (service unavailable): exponential backoff
    - Other errors: raised immediately (no retry)
    
    Returns the raw text of the response.
    """
    backoff = INITIAL_BACKOFF_SECONDS
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            return response.text
        
        except genai_errors.ClientError as e:
            # 429 = rate limit
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                suggested_wait = _extract_retry_delay(str(e))
                wait = suggested_wait if suggested_wait else backoff
                
                if attempt == MAX_RETRIES:
                    raise  # Give up on the final attempt
                
                print(f"    [retry {attempt}/{MAX_RETRIES}] Rate limited. "
                      f"Waiting {wait:.1f}s before retry...")
                time.sleep(wait + 1)  # +1s buffer to be safe
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                continue
            else:
                # Non-rate-limit client error — don't retry
                raise
        
        except genai_errors.ServerError as e:
            # 503 = service unavailable (their side, not ours)
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt == MAX_RETRIES:
                    raise
                
                print(f"    [retry {attempt}/{MAX_RETRIES}] Service unavailable. "
                      f"Waiting {backoff}s before retry...")
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                continue
            else:
                raise
    
    raise RuntimeError("Exhausted all retries without success")


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
    
    text = _call_gemini_with_retry(prompt).strip()
    
    # Strip markdown code fences if the model added them despite instructions
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