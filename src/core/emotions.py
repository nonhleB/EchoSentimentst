"""
ecomind/emotions.py — Plutchik Emotion Wheel Engine
Maps text to 8 primary emotions: Joy, Trust, Fear, Surprise,
Sadness, Disgust, Anger, Anticipation.

Part of EchoMind · Sentiment Intelligence Engine
"""

import re
from typing import Dict, List, Tuple

# ── Plutchik Emotion Lexicon ──────────────────────────────────────────────────
EMOTION_LEXICON: Dict[str, Dict[str, float]] = {
    "joy": {
        "happy": 0.9, "happiness": 0.9, "joy": 1.0, "joyful": 1.0,
        "delighted": 0.9, "delight": 0.9, "ecstatic": 1.0, "elated": 0.9,
        "thrilled": 0.9, "excited": 0.8, "wonderful": 0.8, "fantastic": 0.8,
        "amazing": 0.8, "excellent": 0.8, "great": 0.7, "awesome": 0.8,
        "love": 0.9, "loved": 0.9, "enjoy": 0.7, "enjoyed": 0.7,
        "pleasure": 0.8, "pleased": 0.7, "glad": 0.7, "cheerful": 0.8,
        "brilliant": 0.8, "perfect": 0.9, "superb": 0.9, "beautiful": 0.7,
        "outstanding": 0.9, "impressed": 0.7, "incredible": 0.8,
    },
    "trust": {
        "trust": 1.0, "trustworthy": 1.0, "reliable": 0.9, "dependable": 0.9,
        "honest": 0.9, "safe": 0.8, "secure": 0.8, "confident": 0.8,
        "authentic": 0.8, "genuine": 0.8, "faithful": 0.9, "loyal": 0.9,
        "consistent": 0.7, "transparent": 0.8, "credible": 0.8,
        "professional": 0.7, "quality": 0.6, "recommend": 0.8,
        "satisfied": 0.7, "satisfaction": 0.7, "helpful": 0.7,
    },
    "fear": {
        "afraid": 0.9, "fear": 1.0, "fearful": 1.0, "scared": 0.9,
        "terrified": 1.0, "terror": 1.0, "anxious": 0.8, "anxiety": 0.8,
        "worried": 0.8, "worry": 0.8, "panic": 0.9, "nervous": 0.7,
        "uneasy": 0.7, "dread": 0.9, "dreading": 0.9, "threatened": 0.8,
        "unsafe": 0.8, "dangerous": 0.7, "risk": 0.5, "concern": 0.5,
        "concerned": 0.6, "startled": 0.7, "shocked": 0.6,
    },
    "surprise": {
        "surprised": 0.8, "surprise": 0.8, "unexpected": 0.8, "shocking": 0.7,
        "shocked": 0.7, "astonished": 0.9, "astonishing": 0.9, "wow": 0.9,
        "unbelievable": 0.8, "incredible": 0.8, "remarkable": 0.7,
        "sudden": 0.6, "amazed": 0.8, "astounded": 0.9, "stunned": 0.8,
        "speechless": 0.8, "blown away": 0.9,
    },
    "sadness": {
        "sad": 0.9, "sadness": 0.9, "unhappy": 0.8, "miserable": 1.0,
        "disappointed": 0.8, "disappointment": 0.8, "depressed": 0.9,
        "heartbroken": 1.0, "grief": 1.0, "sorrow": 0.9, "sorry": 0.6,
        "regret": 0.8, "regrets": 0.8, "unfortunate": 0.7, "loss": 0.6,
        "lost": 0.5, "missing": 0.5, "lonely": 0.8, "hopeless": 0.9,
        "devastated": 1.0, "terrible": 0.7, "awful": 0.7,
    },
    "disgust": {
        "disgusting": 1.0, "disgusted": 1.0, "disgust": 1.0, "revolting": 1.0,
        "repulsive": 1.0, "awful": 0.8, "horrible": 0.9, "dreadful": 0.9,
        "appalling": 0.9, "nasty": 0.9, "filthy": 0.9, "gross": 0.8,
        "vile": 0.9, "loathe": 1.0, "loathing": 1.0,
        "hate": 0.9, "hated": 0.9, "worst": 0.8, "terrible": 0.8,
        "unacceptable": 0.7, "shameful": 0.8, "ridiculous": 0.7,
    },
    "anger": {
        "angry": 1.0, "anger": 1.0, "furious": 1.0, "rage": 1.0,
        "outraged": 1.0, "mad": 0.9, "livid": 1.0, "infuriated": 1.0,
        "frustrated": 0.8, "frustrating": 0.8, "frustration": 0.8,
        "irritated": 0.8, "annoyed": 0.8, "irritating": 0.8,
        "aggressive": 0.8, "hostile": 0.9, "irate": 0.9,
        "enraged": 1.0, "upset": 0.7, "complaint": 0.5,
        "wrong": 0.5, "broken": 0.6, "failed": 0.6, "failure": 0.6,
        "nightmare": 0.8, "refused": 0.6,
    },
    "anticipation": {
        "hope": 0.8, "hopeful": 0.9, "excited": 0.8, "excitement": 0.8,
        "eager": 0.9, "eagerly": 0.9, "looking forward": 0.9,
        "anticipate": 1.0, "anticipation": 1.0, "await": 0.8, "awaiting": 0.8,
        "expect": 0.6, "expecting": 0.6, "expectation": 0.6, "soon": 0.5,
        "potential": 0.6, "promise": 0.7, "promising": 0.7, "curious": 0.7,
        "interested": 0.6, "opportunity": 0.6, "plan": 0.4,
    },
}

EMOTION_SYMBOLS = {
    "joy":          "◉",
    "trust":        "◈",
    "fear":         "◎",
    "surprise":     "◇",
    "sadness":      "◆",
    "disgust":      "▽",
    "anger":        "△",
    "anticipation": "○",
}

EMOTION_COLORS = {
    "joy":          "#f5c842",
    "trust":        "#4ade80",
    "fear":         "#c084fc",
    "surprise":     "#22d3ee",
    "sadness":      "#60a5fa",
    "disgust":      "#86efac",
    "anger":        "#f87171",
    "anticipation": "#fb923c",
}


class EmotionEngine:
    """
    Classifies text into Plutchik's 8 primary emotions.
    Returns normalised scores 0–1 per emotion.
    """

    def __init__(self):
        self._lexicon = EMOTION_LEXICON

    def classify(self, text: str) -> Dict[str, float]:
        """Return emotion → score (0.0–1.0) mapping."""
        if not text:
            return {e: 0.0 for e in EMOTION_LEXICON}

        lower = text.lower()
        tokens = set(re.findall(r"\b\w+\b", lower))
        raw: Dict[str, float] = {}

        for emotion, lexicon in self._lexicon.items():
            score = 0.0
            for word, weight in lexicon.items():
                if " " in word:
                    if word in lower:
                        score += weight
                elif word in tokens:
                    score += weight
            raw[emotion] = score

        max_score = max(raw.values()) or 1.0
        return {e: round(min(s / max(max_score, 3.0), 1.0), 3) for e, s in raw.items()}

    def dominant(self, text: str) -> str:
        scores = self.classify(text)
        return max(scores, key=scores.get)

    def top_n(self, text: str, n: int = 3) -> List[Tuple[str, float]]:
        scores = self.classify(text)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]

    @staticmethod
    def symbol(emotion: str) -> str:
        return EMOTION_SYMBOLS.get(emotion, "·")

    @staticmethod
    def color(emotion: str) -> str:
        return EMOTION_COLORS.get(emotion, "#ffffff")
