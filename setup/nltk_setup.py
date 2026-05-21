"""
nltk_setup.py — Pre-download NLTK data for EchoMind.
Run once before deploying or first use.
"""
import nltk

PACKAGES = ["vader_lexicon", "punkt", "stopwords"]

print("\n  ✦ EchoMind — NLTK Setup\n")
for pkg in PACKAGES:
    print(f"  Downloading: {pkg} ...", end=" ", flush=True)
    nltk.download(pkg, quiet=True)
    print("✓")

print("\n  All NLTK data downloaded successfully.\n")
