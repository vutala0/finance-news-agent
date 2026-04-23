"""
Evaluation runner for the financial news classifier.

Loads the hand-labeled golden set, runs each item through the classifier,
saves detailed results, and prints a quick summary.

Usage:
    python eval_runner.py

Output:
    - Detailed JSON results saved to data/eval_results_<timestamp>.json
    - Summary printed to terminal
"""

import json
import os
import time
from datetime import datetime

from classifier import classify_news


# Resolve paths relative to this script's location (more robust)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GOLDEN_SET_PATH = os.path.join(SCRIPT_DIR, "data", "golden_set.json")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "data")


def load_golden_set() -> list[dict]:
    """Load the hand-labeled ground truth dataset."""
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    # Filter out any items that weren't actually labeled
    labeled_items = [
        item for item in items
        if item.get("expected_sentiment") not in ("FILL_ME_IN", "", None)
        and item.get("expected_relevance") not in ("FILL_ME_IN", "", None)
    ]
    
    skipped = len(items) - len(labeled_items)
    if skipped > 0:
        print(f"Note: Skipped {skipped} unlabeled items from the golden set.\n")
    
    return labeled_items


def run_eval(golden_items: list[dict]) -> list[dict]:
    """
    Run the classifier against every item in the golden set.
    
    Returns a list of result records, each containing:
      - the original item
      - what the classifier predicted
      - whether each prediction matched ground truth
    """
    results = []
    
    for i, item in enumerate(golden_items, 1):
        print(f"[{i}/{len(golden_items)}] Evaluating: {item['title'][:70]}...")
        
        
        try:
            prediction = classify_news(
                title=item["title"],
                summary=item["summary"],
                ticker=item["ticker"]
            )
        except Exception as e:
            print(f"  ✗ Error classifying item {i}: {e}")
            prediction = {
                "sentiment": "ERROR",
                "confidence": "ERROR",
                "relevance": "ERROR",
                "reasoning": f"Classifier threw exception: {e}"
            }
        
        # Compare prediction to ground truth
        sentiment_match = (
            prediction["sentiment"].lower() == item["expected_sentiment"].lower()
        )
        relevance_match = (
            prediction.get("relevance", "").lower() == item["expected_relevance"].lower()
        )
        
        result = {
            "ticker": item["ticker"],
            "title": item["title"],
            "summary": item["summary"],
            "expected_sentiment": item["expected_sentiment"],
            "expected_relevance": item["expected_relevance"],
            "predicted_sentiment": prediction["sentiment"],
            "predicted_confidence": prediction["confidence"],
            "predicted_relevance": prediction.get("relevance", "missing"),
            "predicted_reasoning": prediction["reasoning"],
            "sentiment_correct": sentiment_match,
            "relevance_correct": relevance_match,
            "labeling_notes": item.get("labeling_notes", "")
        }
        
        results.append(result)
    
    return results


def print_summary(results: list[dict]) -> None:
    """Print a high-level summary of eval performance."""
    total = len(results)
    if total == 0:
        print("No results to summarize.")
        return
    
    sentiment_correct = sum(1 for r in results if r["sentiment_correct"])
    relevance_correct = sum(1 for r in results if r["relevance_correct"])
    both_correct = sum(
        1 for r in results 
        if r["sentiment_correct"] and r["relevance_correct"]
    )
    
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total items evaluated: {total}")
    print(f"Sentiment accuracy:  {sentiment_correct}/{total} "
          f"({sentiment_correct/total*100:.1f}%)")
    print(f"Relevance accuracy:  {relevance_correct}/{total} "
          f"({relevance_correct/total*100:.1f}%)")
    print(f"Both correct:        {both_correct}/{total} "
          f"({both_correct/total*100:.1f}%)")
    
    # Breakdown of sentiment errors
    sentiment_failures = [r for r in results if not r["sentiment_correct"]]
    if sentiment_failures:
        print(f"\n--- Sentiment Failures ({len(sentiment_failures)}) ---")
        for r in sentiment_failures:
            print(f"  [{r['ticker']}] Expected: {r['expected_sentiment']:<8} "
                  f"Predicted: {r['predicted_sentiment']:<8} "
                  f"| {r['title'][:60]}")
    
    print()


def save_results(results: list[dict]) -> str:
    """Save full eval results to a timestamped file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"eval_results_{timestamp}.json"
    filepath = os.path.join(RESULTS_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return filepath


if __name__ == "__main__":
    print("Loading golden set...")
    golden_items = load_golden_set()
    print(f"Loaded {len(golden_items)} labeled items.\n")
    
    if len(golden_items) == 0:
        print("No labeled items found. Did you fill in the labels in golden_set.json?")
        exit(1)
    
    print("Running eval... (this will take a bit due to rate limits)\n")
    results = run_eval(golden_items)
    
    output_path = save_results(results)
    print(f"Full results saved to: {output_path}")
    
    print_summary(results)