"""
Validates the golden set labels to catch typos and schema drift.
Run this whenever you edit golden_set.json.

Usage:
    python validate_golden_set.py
"""

import json
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GOLDEN_SET_PATH = os.path.join(SCRIPT_DIR, "data", "golden_set.json")

VALID_SENTIMENTS = {"bullish", "bearish", "neutral"}
VALID_RELEVANCE = {"high", "medium", "low"}
REQUIRED_FIELDS = {"ticker", "title", "summary", "expected_sentiment", "expected_relevance"}


def validate():
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    errors = []
    
    for i, item in enumerate(items, 1):
        # Check required fields exist
        for field in REQUIRED_FIELDS:
            if field not in item:
                errors.append(f"Item {i}: missing field '{field}'")
        
        # Check sentiment is valid
        sentiment = item.get("expected_sentiment", "")
        if sentiment in ("FILL_ME_IN", "", None):
            # Unlabeled is fine, just note it
            continue
        if sentiment.lower() not in VALID_SENTIMENTS:
            errors.append(
                f"Item {i} [{item.get('ticker')}]: invalid sentiment '{sentiment}' "
                f"(must be one of {VALID_SENTIMENTS})"
            )
        
        # Check relevance is valid
        relevance = item.get("expected_relevance", "")
        if relevance in ("FILL_ME_IN", "", None):
            continue
        if relevance.lower() not in VALID_RELEVANCE:
            errors.append(
                f"Item {i} [{item.get('ticker')}]: invalid relevance '{relevance}' "
                f"(must be one of {VALID_RELEVANCE})"
            )
    
    if errors:
        print(f"✗ Found {len(errors)} validation errors:\n")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        labeled = sum(
            1 for item in items 
            if item.get("expected_sentiment") not in ("FILL_ME_IN", "", None)
        )
        print(f"✓ Golden set is valid. {labeled}/{len(items)} items labeled.")


if __name__ == "__main__":
    validate()