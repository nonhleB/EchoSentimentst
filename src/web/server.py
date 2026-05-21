"""
server.py — EchoMind Web Server
Flask application serving:
  GET  /              → Interactive dashboard
  GET  /report        → Insights report
  GET  /api/health    → Engine status
  POST /api/analyse   → Single text analysis
  POST /api/batch     → Batch analysis
  GET  /api/summary   → Pre-generated summary stats
  GET  /api/results   → Pre-generated per-row results
"""

import os
import json
import sys

# Ensure project root on path — works locally AND on Render
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from src.core.analyzer import EchoAnalyzer

# ── Paths ─────────────────────────────────────────────────────────────────────
WEB_DIR     = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(PROJECT_ROOT, "output")
DATA_DIR    = os.path.join(PROJECT_ROOT, "data")

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=WEB_DIR, static_url_path="")
CORS(app)

ea = EchoAnalyzer()


# ── Static pages ──────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return app.send_static_file("index.html")

@app.route("/report")
def report():
    # Original code expected a /report page — serve index.html (single page)
    return app.send_static_file("index.html")


# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({
        "status":  "ok",
        "engine":  "EchoMind v1.0.0",
        "backend": ea.backend,
        "tagline": "Hear what your data is really saying",
    })

@app.route("/api/analyse", methods=["POST"])
def analyse():
    data     = request.get_json(force=True, silent=True) or {}
    text     = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    category = data.get("category")
    result   = ea.analyse(text, category=category)
    return jsonify(result)

@app.route("/api/batch", methods=["POST"])
def batch():
    data       = request.get_json(force=True, silent=True) or {}
    texts      = data.get("texts", [])
    categories = data.get("categories")
    if not texts:
        return jsonify({"error": "No texts provided"}), 400
    results = ea.analyse_batch(texts, categories=categories)
    summary = ea.summarise(results)
    return jsonify({"results": results, "summary": summary})

@app.route("/api/summary")
def summary():
    path = os.path.join(OUTPUT_DIR, "summary.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return jsonify(json.load(f))
    # Fall back: run on bundled reviews.csv
    reviews = os.path.join(DATA_DIR, "reviews.csv")
    if os.path.exists(reviews):
        results = ea.analyse_csv(reviews, text_col="text", category_col="category")
        s = ea.summarise(results)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
        return jsonify(s)
    return jsonify({"error": "No pre-generated summary. Run batch_analyze.py first."}), 404

@app.route("/api/results")
def results():
    path = os.path.join(OUTPUT_DIR, "results.csv")
    if os.path.exists(path):
        import csv
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        return jsonify(rows)
    # Fall back: run on bundled reviews.csv
    reviews = os.path.join(DATA_DIR, "reviews.csv")
    if os.path.exists(reviews):
        rows = ea.analyse_csv(
            reviews, text_col="text", category_col="category", out_path=path
        )
        return jsonify(rows)
    return jsonify({"error": "No pre-generated results. Run batch_analyze.py first."}), 404


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  ✦ EchoMind — Sentiment Intelligence Engine")
    print(f"  Backend : {ea.backend}")
    print(f"  Server  : http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
