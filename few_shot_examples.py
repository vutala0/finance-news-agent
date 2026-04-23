"""
Loads few-shot examples from the golden set and formats them for inclusion
in the classification prompt.

The examples are chosen to cover the main failure patterns we saw in baseline eval:
- Over-neutralization on clear directional events
- Over-directional calls on tangential news
- Distinguishing "about the company" from "tagged as about the company"
"""

import json
import os


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GOLDEN_SET_PATH = os.path.join(SCRIPT_DIR, "data", "golden_set.json")

# Titles of the items we're using as few-shot examples.
# These are matched against the golden set by title prefix.
# These items will be EXCLUDED from the eval test set to prevent data leakage.
FEW_SHOT_TITLE_PREFIXES = [
    "Why Tesla Stock Is at a Crossroads",
    "3 Reasons BEN is Risky",
    "Meta to track employee keystrokes",
    "Tesla Q1 earnings preview",
    "What to watch as Nvidia, AMD, and Broadcom",
]


def load_few_shot_examples() -> list[dict]:
    """
    Returns the list of few-shot example records from the golden set.
    Each record has: ticker, title, summary, expected_sentiment, 
    expected_relevance, labeling_notes.
    """
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        all_items = json.load(f)
    
    examples = []
    for prefix in FEW_SHOT_TITLE_PREFIXES:
        matches = [
            item for item in all_items 
            if item["title"].startswith(prefix)
        ]
        if not matches:
            raise ValueError(
                f"No golden set item found with title prefix: '{prefix}'. "
                f"Did the golden set change?"
            )
        if len(matches) > 1:
            raise ValueError(
                f"Multiple golden set items match prefix: '{prefix}'. "
                f"Use a more specific prefix."
            )
        examples.append(matches[0])
    
    return examples


def format_examples_for_prompt(examples: list[dict]) -> str:
    """
    Format the examples as a string block suitable for inclusion in the prompt.
    """
    formatted = []
    for i, ex in enumerate(examples, 1):
        reasoning = ex.get("labeling_notes") or f"Labeled by analyst as {ex['expected_sentiment']}."
        
        formatted.append(
            f"Example {i}:\n"
            f"Ticker: {ex['ticker']}\n"
            f"Title: {ex['title']}\n"
            f"Summary: {ex['summary']}\n"
            f"Correct classification:\n"
            f'  "sentiment": "{ex["expected_sentiment"]}",\n'
            f'  "relevance": "{ex["expected_relevance"]}",\n'
            f'  "reasoning": "{reasoning}"\n'
        )
    
    return "\n".join(formatted)


def get_held_out_items(all_items: list[dict]) -> list[dict]:
    """
    Returns the items from the golden set that are NOT in the few-shot pool.
    These are the items safe to use for evaluation.
    """
    few_shot_prefixes = FEW_SHOT_TITLE_PREFIXES
    held_out = [
        item for item in all_items
        if not any(item["title"].startswith(p) for p in few_shot_prefixes)
    ]
    return held_out


if __name__ == "__main__":
    # Quick test — print the examples
    examples = load_few_shot_examples()
    print(f"Loaded {len(examples)} few-shot examples:\n")
    print(format_examples_for_prompt(examples))