"""
ecomind/analyzer.py — Multi-Layer Sentiment Analysis Engine
EchoMind · Sentiment Intelligence Platform

Analysis pipeline:
  1. VADER (via NLTK) — primary engine, fast, social-text tuned
  2. TextBlob            — secondary fallback
  3. Rule-based          — tertiary fallback for edge cases

Each result is enriched with Plutchik 8-emotion scoring.
"""

import re
import csv
import json
from typing import Dict, List, Optional, Any

from src.core.emotions import EmotionEngine

# ── Sentiment thresholds ──────────────────────────────────────────────────────
POS_THRESHOLD =  0.05
NEG_THRESHOLD = -0.05


def _rule_based_score(text: str) -> float:
    """Lightweight rule-based scorer for environments without VADER/TextBlob."""
    text_lower = text.lower()
    pos_words = [
        "good", "great", "excellent", "amazing", "fantastic", "love", "loved",
        "perfect", "wonderful", "awesome", "best", "outstanding", "superb",
        "brilliant", "happy", "impressed", "pleased", "satisfied",
    ]
    neg_words = [
        "bad", "terrible", "horrible", "awful", "worst", "hate", "hated",
        "poor", "disappointed", "broken", "useless", "failed", "disaster",
        "waste", "never", "refund", "return", "damaged", "wrong", "problem",
    ]
    tokens = set(re.findall(r"\b\w+\b", text_lower))
    pos = sum(1 for w in pos_words if w in tokens)
    neg = sum(1 for w in neg_words if w in tokens)
    total = pos + neg or 1
    raw = (pos - neg) / total
    return round(max(-1.0, min(1.0, raw)), 4)


class EchoAnalyzer:
    """
    Primary EchoMind analysis object.

    Usage:
        ea = EchoAnalyzer()
        result = ea.analyse("This product is absolutely incredible!")
        results = ea.analyse_batch(["Great!", "Terrible."])
        summary = ea.summarise(results)
    """

    def __init__(self):
        self._emotions = EmotionEngine()
        self._backend = self._init_backend()

    # ── Backend detection ────────────────────────────────────────────────────

    def _init_backend(self) -> str:
        try:
            import nltk
            from nltk.sentiment import SentimentIntensityAnalyzer
            try:
                self._sia = SentimentIntensityAnalyzer()
            except LookupError:
                nltk.download("vader_lexicon", quiet=True)
                self._sia = SentimentIntensityAnalyzer()
            return "vader"
        except ImportError:
            pass

        try:
            from textblob import TextBlob  # noqa: F401
            return "textblob"
        except ImportError:
            pass

        return "rule-based"

    @property
    def backend(self) -> str:
        return self._backend

    # ── Core scoring ─────────────────────────────────────────────────────────

    def _score(self, text: str) -> Dict[str, float]:
        if self._backend == "vader":
            scores = self._sia.polarity_scores(text)
            return {
                "compound": scores["compound"],
                "pos":      round(scores["pos"], 4),
                "neg":      round(scores["neg"], 4),
                "neu":      round(scores["neu"], 4),
            }
        if self._backend == "textblob":
            from textblob import TextBlob
            tb = TextBlob(text)
            compound = round(tb.sentiment.polarity, 4)
            pos = round(max(compound, 0), 4)
            neg = round(abs(min(compound, 0)), 4)
            neu = round(1.0 - pos - neg, 4)
            return {"compound": compound, "pos": pos, "neg": neg, "neu": max(neu, 0)}
        # rule-based
        compound = _rule_based_score(text)
        pos = round(max(compound, 0), 4)
        neg = round(abs(min(compound, 0)), 4)
        neu = round(max(1.0 - pos - neg, 0), 4)
        return {"compound": compound, "pos": pos, "neg": neg, "neu": neu}

    # ── Classification ───────────────────────────────────────────────────────

    @staticmethod
    def _classify(compound: float) -> str:
        if compound >= POS_THRESHOLD:
            return "Positive"
        if compound <= NEG_THRESHOLD:
            return "Negative"
        return "Neutral"

    @staticmethod
    def _sentiment_emoji(sentiment: str) -> str:
        return {"Positive": "😊", "Negative": "😞", "Neutral": "😐"}.get(sentiment, "😐")

    @staticmethod
    def _intensity(compound: float) -> str:
        abs_c = abs(compound)
        if abs_c >= 0.75:
            return "Strong"
        if abs_c >= 0.40:
            return "Moderate"
        if abs_c >= 0.05:
            return "Mild"
        return "Borderline"

    # ── Public API ───────────────────────────────────────────────────────────

    def analyse(self, text: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Analyse a single piece of text. Returns enriched result dict."""
        if not text or not text.strip():
            return {"error": "Empty text provided"}

        scores = self._score(text)
        compound = scores["compound"]
        sentiment = self._classify(compound)
        emotions = self._emotions.classify(text)
        dominant_emo = max(emotions, key=emotions.get)
        top3 = self._emotions.top_n(text, 3)

        return {
            "text":          text,
            "sentiment":     sentiment,
            "compound":      compound,
            "pos":           scores["pos"],
            "neg":           scores["neg"],
            "neu":           scores["neu"],
            "intensity":     self._intensity(compound),
            "emoji":         self._sentiment_emoji(sentiment),
            "emotions":      emotions,
            "dominant_emotion": dominant_emo,
            "top_emotions":  [{"emotion": e, "score": s} for e, s in top3],
            "backend":       self._backend,
            "category":      category or "general",
        }

    def analyse_batch(
        self,
        texts: List[str],
        categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Analyse a list of texts. Returns list of result dicts."""
        results = []
        for i, text in enumerate(texts):
            cat = categories[i] if categories and i < len(categories) else None
            result = self.analyse(text, category=cat)
            result["id"] = i + 1
            results.append(result)
        return results

    def analyse_csv(
        self,
        filepath: str,
        text_col: str = "text",
        category_col: Optional[str] = "category",
        out_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Read CSV, analyse text column, optionally write enriched CSV."""
        results = []
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                text = row.get(text_col, "").strip()
                if not text:
                    continue
                cat = row.get(category_col, "general") if category_col else None
                result = self.analyse(text, category=cat)
                result.update({k: v for k, v in row.items() if k not in result})
                result["id"] = i + 1
                results.append(result)

        if out_path:
            self._write_csv(results, out_path)
        return results

    def summarise(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate statistics from a list of analyse() results."""
        if not results:
            return {}

        total     = len(results)
        pos_list  = [r for r in results if r.get("sentiment") == "Positive"]
        neg_list  = [r for r in results if r.get("sentiment") == "Negative"]
        neu_list  = [r for r in results if r.get("sentiment") == "Neutral"]

        compounds = [r.get("compound", 0) for r in results]
        avg_compound = round(sum(compounds) / total, 4)

        # Emotion aggregation
        all_emotions: Dict[str, float] = {
            e: 0.0 for e in [
                "joy", "trust", "fear", "surprise",
                "sadness", "disgust", "anger", "anticipation",
            ]
        }
        for r in results:
            for e, s in r.get("emotions", {}).items():
                all_emotions[e] = round(all_emotions.get(e, 0) + s, 4)
        avg_emotions = {e: round(s / total, 3) for e, s in all_emotions.items()}
        dominant_emo = max(avg_emotions, key=avg_emotions.get)

        # Category breakdown
        category_stats: Dict[str, Dict] = {}
        for r in results:
            cat = r.get("category", "general")
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "positive": 0, "neutral": 0, "negative": 0, "compounds": []}
            cs = category_stats[cat]
            cs["total"] += 1
            cs[r.get("sentiment", "Neutral").lower()] += 1
            cs["compounds"].append(r.get("compound", 0))

        for cat, cs in category_stats.items():
            comps = cs.pop("compounds")
            cs["avg_compound"] = round(sum(comps) / len(comps), 4) if comps else 0

        # Extremes
        sorted_by_compound = sorted(results, key=lambda x: x.get("compound", 0))
        most_negative = sorted_by_compound[0] if sorted_by_compound else {}
        most_positive = sorted_by_compound[-1] if sorted_by_compound else {}

        # Health score
        if avg_compound >= 0.30:
            health = "Excellent ✦"
        elif avg_compound >= 0.10:
            health = "Good ✓"
        elif avg_compound >= -0.05:
            health = "Neutral ◌"
        elif avg_compound >= -0.20:
            health = "Concerning !"
        else:
            health = "Critical ✗"

        positive_pct = round(len(pos_list) / total * 100, 1)
        neutral_pct  = round(len(neu_list) / total * 100, 1)
        negative_pct = round(len(neg_list) / total * 100, 1)

        return {
            "total":            total,
            "positive":         len(pos_list),
            "neutral":          len(neu_list),
            "negative":         len(neg_list),
            "positive_pct":     positive_pct,
            "neutral_pct":      neutral_pct,
            "negative_pct":     negative_pct,
            "avg_compound":     avg_compound,
            "overall_sentiment": "Positive" if avg_compound >= POS_THRESHOLD else "Negative" if avg_compound <= NEG_THRESHOLD else "Neutral",
            "sentiment_health": health,
            "dominant_emotion": dominant_emo,
            "avg_emotions":     avg_emotions,
            "category_stats":   category_stats,
            "most_positive":    {"id": most_positive.get("id"), "text": most_positive.get("text", "")[:80], "compound": most_positive.get("compound", 0)},
            "most_negative":    {"id": most_negative.get("id"), "text": most_negative.get("text", "")[:80], "compound": most_negative.get("compound", 0)},
            "compounds":        compounds,
            "backend":          results[0].get("backend", "unknown") if results else "unknown",
        }

    # ── I/O helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _write_csv(results: List[Dict[str, Any]], out_path: str) -> None:
        if not results:
            return
        import os
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        flat_keys = ["id", "text", "category", "sentiment", "compound", "pos", "neg", "neu", "intensity", "dominant_emotion"]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=flat_keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
