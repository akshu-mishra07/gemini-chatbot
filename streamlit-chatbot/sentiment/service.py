from __future__ import annotations

"""Sentiment and Emotion analysis service with robust local fallbacks."""

import math
import re
import sys
from typing import Any

from database.storage import execute, fetch_all, now_iso


POSITIVE_TERMS = {
    "amazing", "awesome", "best", "brilliant", "clear", "delight", "excellent",
    "fantastic", "good", "great", "happy", "helpful", "love", "perfect",
    "positive", "resolved", "satisfied", "smooth", "thanks", "thank", "wonderful",
    "superb", "satisfying", "glad", "cool", "nice", "perfectly", "efficient",
    "impressive", "outstanding", "useful", "appreciate", "helpful", "gem",
    "wow", "lovely", "splendid", "terrific", "phenomenal", "ideal"
}

NEGATIVE_TERMS = {
    "angry", "awful", "bad", "broken", "confused", "disappointed", "error",
    "fail", "failed", "frustrated", "hate", "issue", "negative", "problem",
    "refund", "sad", "slow", "terrible", "unhappy", "upset", "wrong",
    "worst", "unacceptable", "useless", "garbage", "trash", "lag", "crash",
    "horrible", "annoyed", "bug", "broken", "poor", "pain", "waste", "disgusting",
    "worried", "scared", "fear", "afraid", "anxious", "panic", "dread", "frightened", "nervous"
}

import threading

_PIPELINE = None
_PIPELINE_FAILED = False
_LOADING_THREAD = None


def _load_pipeline_worker():
    global _PIPELINE, _PIPELINE_FAILED
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

        model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        try:
            # First attempt: load from local cache only (fast, offline)
            tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(model_name, local_files_only=True)
        except Exception:
            # Check connectivity to HuggingFace before attempting download to avoid hanging
            try:
                import requests
                # Attempt to ping HuggingFace Hub with a short timeout
                requests.head("https://huggingface.co", timeout=3.0)
                connectivity_ok = True
            except Exception:
                connectivity_ok = False
                
            if not connectivity_ok:
                raise RuntimeError("HuggingFace Hub is unreachable or connection timed out.")

            # Second attempt: download model from HF Hub
            tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=False)
            model = AutoModelForSequenceClassification.from_pretrained(model_name, local_files_only=False)
        _PIPELINE = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    except Exception as e:
        print(f"[Sentiment Model Load Warning] Failed to initialize transformers sentiment pipeline: {e}. Falling back to lexical analysis.", file=sys.stderr)
        _PIPELINE_FAILED = True
        _PIPELINE = None


def _load_transformer_pipeline():
    global _PIPELINE, _PIPELINE_FAILED, _LOADING_THREAD
    if _PIPELINE is not None or _PIPELINE_FAILED:
        return _PIPELINE
        
    if _LOADING_THREAD is None:
        _LOADING_THREAD = threading.Thread(target=_load_pipeline_worker, daemon=True)
        _LOADING_THREAD.start()
        
    return _PIPELINE


def _lexical_sentiment_and_emotion(text: str) -> dict[str, Any]:
    text_lower = text.lower()
    positive_emojis = {":-)", ":)", "=)", ";)", "<3", "🙂", "😀", "😄", "😊", "👍", "❤️"}
    negative_emojis = {":-(", ":(", "=(", ";(", "😢", "😭", "👎", "😠", "😡", "💩"}
    
    pos_emoji_count = sum(text_lower.count(e) for e in positive_emojis)
    neg_emoji_count = sum(text_lower.count(e) for e in negative_emojis)

    tokens = re.findall(r"[a-zA-Z']+", text_lower)
    if not tokens and not pos_emoji_count and not neg_emoji_count:
        return {"label": "Neutral", "emotion": "Neutral", "confidence": 0.55, "source": "lexicon"}

    positive = sum(1 for token in tokens if token in POSITIVE_TERMS) + pos_emoji_count * 2
    negative = sum(1 for token in tokens if token in NEGATIVE_TERMS) + neg_emoji_count * 2
    raw = positive - negative
    magnitude = positive + negative

    if raw > 0:
        label = "Positive"
    elif raw < 0:
        label = "Negative"
    else:
        label = "Neutral"

    # Emotion keywords
    emotions_lexicon = {
        "Joy": {"happy", "glad", "joy", "excited", "love", "great", "excellent", "awesome", "wonderful", "delighted", "thanks", "thank", "smile", "positive", "resolved", "satisfied", "superb", "satisfying", "cool", "nice", "perfect", "wow", "lovely", "splendid", "terrific", "phenomenal", "ideal"},
        "Sadness": {"sad", "unhappy", "cry", "crying", "depressed", "sorry", "hurt", "pain", "disappointed", "grief", "gloomy", "heartbroken", "lonely", "regret", "tears", "awful", "terrible", "poor", "waste", "horrible"},
        "Anger": {"angry", "mad", "furious", "hate", "annoyed", "pissed", "trash", "garbage", "useless", "worst", "terrible", "frustrated", "rage", "insult", "slow", "unacceptable", "refund", "issue", "problem", "wrong", "annoy", "annoying", "disgusting"},
        "Fear": {"afraid", "scared", "fear", "anxious", "worry", "worried", "panic", "dread", "terror", "frightened", "nervous", "uneasy", "concern", "concerned", "alarmed", "spooked"},
        "Surprise": {"surprise", "surprised", "shocked", "wow", "amazing", "unexpected", "incredible", "unbelievable", "sudden", "suddenness", "startle", "startled", "shock", "brilliant", "fantastic"}
    }
    
    scores = {emo: 0 for emo in emotions_lexicon}
    for token in tokens:
        for emo, words in emotions_lexicon.items():
            if token in words:
                scores[emo] += 1
                
    # Emoji adjustments
    scores["Joy"] += pos_emoji_count * 2
    scores["Sadness"] += text_lower.count("😢") * 2 + text_lower.count("😭") * 2
    scores["Anger"] += text_lower.count("😠") * 2 + text_lower.count("😡") * 2

    max_score = max(scores.values())
    if max_score > 0:
        candidate_emotions = [emo for emo, score in scores.items() if score == max_score]
        emotion = candidate_emotions[0]
    else:
        if label == "Positive":
            emotion = "Joy"
        elif label == "Negative":
            emotion = "Sadness"
        else:
            emotion = "Neutral"

    confidence = 0.55 if magnitude == 0 else 0.55 + min(0.4, math.log1p(magnitude) / 4)
    return {
        "label": label,
        "emotion": emotion,
        "confidence": round(confidence, 3),
        "source": "lexicon"
    }


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Return Positive, Negative, or Neutral sentiment with confidence, and the emotion."""
    lexical = _lexical_sentiment_and_emotion(text)
    
    pipeline = _load_transformer_pipeline()
    if pipeline is not None:
        try:
            result = pipeline(text[:512])[0]
            raw_label = str(result.get("label", "")).upper()
            confidence = float(result.get("score", 0.0))
            if confidence < 0.62:
                label = "Neutral"
            elif "NEG" in raw_label:
                label = "Negative"
            else:
                label = "Positive"
            
            lexical["label"] = label
            lexical["confidence"] = round(confidence, 3)
            lexical["source"] = "transformers"
            
            # Recalculate emotion if default neutral
            if lexical["emotion"] == "Neutral":
                if label == "Positive":
                    lexical["emotion"] = "Joy"
                elif label == "Negative":
                    lexical["emotion"] = "Sadness"
        except Exception:
            pass
            
    return lexical


def sentiment_badge_html(sentiment: dict[str, Any]) -> str:
    label = sentiment.get("label", "Neutral")
    emotion = sentiment.get("emotion", "Neutral")
    confidence = float(sentiment.get("confidence", 0.0))
    colors = {
        "Positive": ("#064e3b", "#34d399"),
        "Negative": ("#7f1d1d", "#f87171"),
        "Neutral": ("#1f2937", "#9ca3af"),
    }
    bg, fg = colors.get(label, colors["Neutral"])
    
    badge_label = f"{label} ({emotion})" if emotion != label else label
    return (
        "<span style=\""
        f"background:{bg};color:{fg};border:1px solid {fg};"
        "border-radius:999px;padding:2px 8px;font-size:0.78rem;font-weight:700;"
        "\">"
        f"{badge_label} · {confidence:.0%}"
        "</span>"
    )


def build_sentiment_instruction(sentiment: dict[str, Any]) -> str:
    label = sentiment.get("label", "Neutral")
    emotion = sentiment.get("emotion", "Neutral")
    confidence = float(sentiment.get("confidence", 0.0))
    
    if emotion == "Sadness":
        tone = "The user is sad. Respond empathetically, gently, and offer warm support."
    elif emotion == "Anger":
        tone = "The user is angry or frustrated. Respond calmly, validate their concerns, de-escalate, and focus on helpful solutions."
    elif emotion == "Joy":
        tone = "The user is happy. Respond positively, enthusiastically, and match their warmth."
    elif emotion == "Fear":
        tone = "The user is anxious or fearful. Reassure them and provide clear, simple step-by-step guidance."
    elif emotion == "Surprise":
        tone = "The user is surprised. Respond with interest, clarity, and thorough explanations."
    else:
        if label == "Negative":
            tone = "Use a calm, empathetic, solution-oriented customer-service tone."
        elif label == "Positive":
            tone = "Keep the response warm and positive."
        else:
            tone = "Use a clear, professional, concise customer-service tone."
            
    return f"Detected customer sentiment: {label}, Emotion: {emotion} ({confidence:.0%} confidence). Tone policy: {tone}"


def record_sentiment(
    user_id: str,
    session_id: str,
    message: str,
    sentiment: dict[str, Any],
) -> None:
    execute(
        """
        INSERT INTO sentiment_events
            (user_id, session_id, label, emotion, confidence, message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(user_id),
            session_id,
            sentiment.get("label", "Neutral"),
            sentiment.get("emotion", "Neutral"),
            float(sentiment.get("confidence", 0.0)),
            message,
            now_iso(),
        ),
    )


def list_sentiment_events(limit: int = 200) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT * FROM sentiment_events
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )


def sentiment_summary() -> dict[str, Any]:
    rows = fetch_all("SELECT label, COUNT(*) AS count FROM sentiment_events GROUP BY label")
    counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for row in rows:
        counts[row["label"]] = int(row["count"])
        
    # Also fetch emotion summary
    emo_rows = fetch_all("SELECT emotion, COUNT(*) AS count FROM sentiment_events GROUP BY emotion")
    emotions = {"Joy": 0, "Sadness": 0, "Anger": 0, "Fear": 0, "Surprise": 0, "Neutral": 0}
    for row in emo_rows:
        if row["emotion"] in emotions:
            emotions[row["emotion"]] = int(row["count"])
            
    total = sum(counts.values())
    return {"counts": counts, "emotions": emotions, "total": total}
