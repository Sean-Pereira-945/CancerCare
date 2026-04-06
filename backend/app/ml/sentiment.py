from transformers import pipeline
from functools import lru_cache


@lru_cache(maxsize=1)
def load_sentiment():
    """Load DistilBERT sentiment model. Loaded once and cached."""
    return pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )


def analyze_mood(text: str) -> dict:
    """
    Analyze sentiment of a patient's journal entry.
    Returns label (POSITIVE/NEGATIVE), score, and normalized mood_score (0-1).
    """
    if not text or len(text.strip()) < 10:
        return {"label": "NEUTRAL", "score": 0.5, "mood_score": 0.5}

    sentiment = load_sentiment()
    result = sentiment(text[:512])[0]

    return {
        "label": result["label"],       # POSITIVE or NEGATIVE
        "score": round(result["score"], 3),
        "mood_score": round(
            result["score"] if result["label"] == "POSITIVE" else 1 - result["score"],
            3
        )
    }
