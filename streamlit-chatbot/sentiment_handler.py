"""
sentiment_handler.py - Sentiment analysis using TextBlob.

Detects positive, negative, or neutral sentiment in user messages
and adjusts the chatbot's response tone accordingly.
"""

# Download required NLTK corpora silently on first import
import nltk

for _corpus in ("punkt", "brown", "averaged_perceptron_tagger", "punkt_tab"):
    try:
        nltk.download(_corpus, quiet=True)
    except Exception:
        pass

from textblob import TextBlob  # noqa: E402 — must come after NLTK downloads

# Polarity thresholds
_POSITIVE_THRESHOLD = 0.1
_NEGATIVE_THRESHOLD = -0.1

# Tone instructions injected into the system prompt based on detected sentiment
_TONE_INSTRUCTIONS: dict[str, str] = {
    "positive": (
        "The user appears to be in a positive or enthusiastic mood. "
        "Match their energy with a warm, upbeat, and encouraging tone."
    ),
    "negative": (
        "The user seems frustrated, sad, or upset. "
        "Respond with extra empathy, patience, and a calm, supportive tone."
    ),
    "neutral": (
        "The user's tone is neutral and matter-of-fact. "
        "Respond in a balanced, clear, and informative manner."
    ),
}

_SENTIMENT_EMOJI: dict[str, str] = {
    "positive": "😊",
    "negative": "😔",
    "neutral": "😐",
}


def analyze_sentiment(text: str) -> dict:
    """
    Analyse the sentiment of the given text using TextBlob.

    Args:
        text: User input string.

    Returns:
        dict with keys: label (positive|negative|neutral), polarity, subjectivity
    """
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
    except Exception:
        # Graceful fallback if TextBlob fails
        return {"label": "neutral", "polarity": 0.0, "subjectivity": 0.0}

    if polarity > _POSITIVE_THRESHOLD:
        label = "positive"
    elif polarity < _NEGATIVE_THRESHOLD:
        label = "negative"
    else:
        label = "neutral"

    return {
        "label": label,
        "polarity": round(polarity, 3),
        "subjectivity": round(subjectivity, 3),
    }


def get_tone_instruction(sentiment_label: str) -> str:
    """
    Return the tone instruction string for the given sentiment label.

    Args:
        sentiment_label: One of "positive", "negative", "neutral".

    Returns:
        str: Instruction for the chatbot's response tone.
    """
    return _TONE_INSTRUCTIONS.get(sentiment_label, _TONE_INSTRUCTIONS["neutral"])


def get_sentiment_emoji(label: str) -> str:
    """Return a display emoji for the sentiment label."""
    return _SENTIMENT_EMOJI.get(label, "😐")
