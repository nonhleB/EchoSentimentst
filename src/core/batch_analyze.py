"""
batch_analyze.py — EchoMind Batch CSV Runner
Reads data/reviews.csv and writes:
  output/results.csv    — per-row enriched analysis
  output/summary.json   — aggregate statistics
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.analyzer import EchoAnalyzer

DATA_PATH   = os.path.join(BASE_DIR, "data", "reviews.csv")
OUT_CSV     = os.path.join(BASE_DIR, "output", "results.csv")
OUT_JSON    = os.path.join(BASE_DIR, "output", "summary.json")
OUT_DIR     = os.path.join(BASE_DIR, "output")


def run():
    print("\n  ✦ EchoMind — Batch Analysis Runner\n")
    ea = EchoAnalyzer()
    print(f"  Backend  : {ea.backend}")
    print(f"  Input    : {DATA_PATH}\n")

    if not os.path.exists(DATA_PATH):
        print(f"  ✗  Data file not found: {DATA_PATH}")
        sys.exit(1)

    results = ea.analyse_csv(DATA_PATH, text_col="text", category_col="category", out_path=OUT_CSV)
    summary = ea.summarise(results)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"  Results  → {OUT_CSV}")
    print(f"  Summary  → {OUT_JSON}\n")
    print(f"  Total      : {summary['total']}")
    print(f"  Positive   : {summary['positive']}  ({summary['positive_pct']}%)")
    print(f"  Neutral    : {summary['neutral']}   ({summary['neutral_pct']}%)")
    print(f"  Negative   : {summary['negative']}  ({summary['negative_pct']}%)")
    print(f"  Overall    : {summary['overall_sentiment']}")
    print(f"  Health     : {summary['sentiment_health']}")
    print(f"  Dom. Emotion: {summary['dominant_emotion']}")
    print(f"\n  Open http://localhost:5000 after running server.py to view results.\n")


if __name__ == "__main__":
    run()
