"""
app.py — EchoMind Gunicorn Entry Point

Render is configured to run: gunicorn src.web.app:app
This file imports and re-exports the Flask `app` from server.py.

The original CLI functionality lives in __main__ below — run it with:
  python src/web/app.py
"""

import os
import sys

# Ensure project root is on the path so `src.*` imports resolve on Render
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.web.server import app  # noqa: F401 — re-exported for gunicorn
@app.route('/')
def index():
    return render_template('index.html')  # or send_from_directory

@app.route('/report')
def report():
    return render_template('report.html')


if __name__ == "__main__":
    # Original CLI behaviour preserved
    port = int(os.environ.get("PORT", 5000))
    from src.web.server import ea
    print(f"\n  ✦ EchoMind — Sentiment Intelligence Engine")
    print(f"  Backend : {ea.backend}")
    print(f"  Server  : http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
