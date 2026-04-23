"""
Generates a human-readable Markdown report from an eval results JSON file.

Usage:
    # Generate report for the most recent eval run
    python eval_report.py
    
    # Generate report for a specific run
    python eval_report.py data/eval_results_20260423_163737.json

The report is written to reports/eval_report_<timestamp>.md
"""

import json
import os
import sys
from datetime import datetime
from collections import Counter


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
REPORTS_DIR = os.path.join(SCRIPT_DIR, "reports")


def find_latest_eval_file() -> str:
    """Return the path to the most recent eval_results_*.json file."""
    candidates = [
        f for f in os.listdir(DATA_DIR)
        if f.startswith("eval_results_") and f.endswith(".json")
    ]
    if not candidates:
        raise FileNotFoundError("No eval_results_*.json files found in data/")
    candidates.sort(reverse=True)
    return os.path.join(DATA_DIR, candidates[0])


def compute_metrics(results: list[dict]) -> dict:
    """Compute summary metrics across a result set."""
    total = len(results)
    if total == 0:
        return {"total": 0}
    
    errors = sum(1 for r in results if r["predicted_sentiment"] == "ERROR")
    valid = total - errors
    
    sentiment_correct = sum(1 for r in results if r["sentiment_correct"])
    relevance_correct = sum(1 for r in results if r["relevance_correct"])
    both_correct = sum(
        1 for r in results 
        if r["sentiment_correct"] and r["relevance_correct"]
    )
    
    return {
        "total": total,
        "valid": valid,
        "errors": errors,
        "sentiment_correct": sentiment_correct,
        "sentiment_accuracy": sentiment_correct / total if total > 0 else 0,
        "relevance_correct": relevance_correct,
        "relevance_accuracy": relevance_correct / total if total > 0 else 0,
        "both_correct": both_correct,
        "both_accuracy": both_correct / total if total > 0 else 0,
    }


def categorize_sentiment_failures(results: list[dict]) -> dict:
    """Group sentiment failures by their error pattern."""
    failures = [
        r for r in results 
        if not r["sentiment_correct"] and r["predicted_sentiment"] != "ERROR"
    ]
    
    over_neutralized = []    # Expected directional, got neutral
    over_directional = []    # Expected neutral, got directional
    wrong_direction = []     # Bullish→Bearish or Bearish→Bullish
    
    for r in failures:
        exp = r["expected_sentiment"].lower()
        pred = r["predicted_sentiment"].lower()
        
        if pred == "neutral" and exp in ("bullish", "bearish"):
            over_neutralized.append(r)
        elif exp == "neutral" and pred in ("bullish", "bearish"):
            over_directional.append(r)
        else:
            wrong_direction.append(r)
    
    return {
        "over_neutralized": over_neutralized,
        "over_directional": over_directional,
        "wrong_direction": wrong_direction,
    }


def sentiment_distribution(results: list[dict]) -> dict:
    """Compare expected vs. predicted sentiment distributions."""
    expected = Counter(r["expected_sentiment"].lower() for r in results)
    predicted = Counter(
        r["predicted_sentiment"].lower() 
        for r in results 
        if r["predicted_sentiment"] != "ERROR"
    )
    return {"expected": dict(expected), "predicted": dict(predicted)}


def generate_report(results_path: str) -> str:
    """Generate a Markdown report from a results file. Returns the report path."""
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
    
    metrics = compute_metrics(results)
    failure_patterns = categorize_sentiment_failures(results)
    distribution = sentiment_distribution(results)
    
    # Extract the timestamp from the filename for the report name
    results_filename = os.path.basename(results_path)
    timestamp = results_filename.replace("eval_results_", "").replace(".json", "")
    
    report_lines = [
        f"# Evaluation Report — {timestamp}",
        "",
        f"Source: `{results_filename}`",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary Metrics",
        "",
        f"- **Total items:** {metrics['total']}",
        f"- **Valid classifications:** {metrics['valid']} "
        f"({metrics['errors']} errors)",
        f"- **Sentiment accuracy:** {metrics['sentiment_correct']}/"
        f"{metrics['total']} ({metrics['sentiment_accuracy']*100:.1f}%)",
        f"- **Relevance accuracy:** {metrics['relevance_correct']}/"
        f"{metrics['total']} ({metrics['relevance_accuracy']*100:.1f}%)",
        f"- **Both correct:** {metrics['both_correct']}/"
        f"{metrics['total']} ({metrics['both_accuracy']*100:.1f}%)",
        "",
        "## Sentiment Distribution",
        "",
        "| Label | Expected (ground truth) | Predicted (model) |",
        "| --- | --- | --- |",
    ]
    
    for label in ["bullish", "bearish", "neutral"]:
        exp = distribution["expected"].get(label, 0)
        pred = distribution["predicted"].get(label, 0)
        report_lines.append(f"| {label} | {exp} | {pred} |")
    
    report_lines.extend([
        "",
        "## Failure Patterns",
        "",
        f"### Over-neutralized ({len(failure_patterns['over_neutralized'])} cases)",
        "",
        "Expected a directional call (bullish/bearish) but model returned neutral. "
        "Suggests the model defaults to neutral on ambiguous wording even when "
        "the signal is clear to a human analyst.",
        "",
    ])
    
    for r in failure_patterns["over_neutralized"]:
        report_lines.append(
            f"- **[{r['ticker']}]** Expected `{r['expected_sentiment']}` → "
            f"_{r['title'][:80]}_"
        )
        report_lines.append(
            f"  - Reasoning given: {r['predicted_reasoning']}"
        )
    
    report_lines.extend([
        "",
        f"### Over-directional ({len(failure_patterns['over_directional'])} cases)",
        "",
        "Expected neutral but model returned bullish or bearish. Often "
        "triggered by preview-style articles or tangential industry news "
        "where the model reads active framing as directional signal.",
        "",
    ])
    
    for r in failure_patterns["over_directional"]:
        report_lines.append(
            f"- **[{r['ticker']}]** Predicted `{r['predicted_sentiment']}` → "
            f"_{r['title'][:80]}_"
        )
        report_lines.append(
            f"  - Reasoning given: {r['predicted_reasoning']}"
        )
    
    if failure_patterns["wrong_direction"]:
        report_lines.extend([
            "",
            f"### Wrong direction ({len(failure_patterns['wrong_direction'])} cases)",
            "",
            "Bullish flipped to bearish or vice versa. These are the most "
            "concerning errors because the model made a confident directional "
            "call in the wrong direction.",
            "",
        ])
        for r in failure_patterns["wrong_direction"]:
            report_lines.append(
                f"- **[{r['ticker']}]** Expected `{r['expected_sentiment']}`, "
                f"got `{r['predicted_sentiment']}` → _{r['title'][:80]}_"
            )
            report_lines.append(
                f"  - Reasoning given: {r['predicted_reasoning']}"
            )
    
    report_lines.extend([
        "",
        "## Interpretation & Next Steps",
        "",
        "(This section should be filled in by hand after each eval run. "
        "Document what changed between this run and the previous one, what "
        "you learned, and what the next intervention should be.)",
        "",
    ])
    
    # Ensure reports directory exists
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    report_path = os.path.join(REPORTS_DIR, f"eval_report_{timestamp}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    return report_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        results_path = sys.argv[1]
    else:
        results_path = find_latest_eval_file()
        print(f"Using latest results file: {os.path.basename(results_path)}")
    
    report_path = generate_report(results_path)
    print(f"\n✓ Report written to: {report_path}")
    print("\nOpen it in VS Code to read, and fill in the 'Interpretation & Next Steps' section.")