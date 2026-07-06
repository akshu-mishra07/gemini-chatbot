from __future__ import annotations

"""
entities.py - Hardened Entity extraction and understanding for the image pipeline.
"""

import json
import re
import sys


def extract_entities(prompt: str, api_key: str | None = None) -> list[dict]:
    """
    Extracts entities (name, category) from the prompt.
    Uses Gemini LLM if configured and online, falling back to local rule-based parsing.
    Guaranteed to return a valid list (never None).
    """
    if not prompt or not isinstance(prompt, str):
        return []

    entities = []
    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            system_instruction = (
                "You are an expert NLP entity extractor for an image generation pipeline.\n"
                "Extract every key entity (Person, Celebrity, God/Goddess, Animal, Building, Object, Place, Event, Brand).\n"
                "Return a strict JSON array of objects, each containing exactly 'name' and 'category'.\n"
                "Never add markdown formatting, markdown code blocks, or comments outside the JSON array."
            )
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"Extract entities from: {prompt}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            
            if response is not None and getattr(response, "text", None):
                clean_text = response.text.strip()
                if clean_text.startswith("```"):
                    clean_text = re.sub(r"^```(?:json)?\n|```$", "", clean_text, flags=re.MULTILINE).strip()
                
                if clean_text:
                    data = json.loads(clean_text)
                    if isinstance(data, list):
                        entities = data
        except Exception as e:
            print(f"[Image Pipeline] Gemini entity extraction failed: {e}. Falling back to local parser.", file=sys.stderr)

    # Fallback to local rule-based parsing if empty
    if not entities:
        try:
            entities = _local_entity_extraction(prompt)
        except Exception as local_err:
            print(f"[Image Pipeline] Local entity extraction critical failure: {local_err}", file=sys.stderr)
            entities = []

    # Ensure output is fully validated and contains no None values
    validated = []
    if isinstance(entities, list):
        for e in entities:
            if isinstance(e, dict) and e.get("name") is not None and e.get("category") is not None:
                validated.append({
                    "name": str(e["name"]).strip(),
                    "category": str(e["category"]).strip()
                })
    return validated


def _local_entity_extraction(prompt: str) -> list[dict]:
    """Fallback rule-based keyword & regex entity extractor."""
    low = prompt.lower()
    entities = []

    # 1. Gods & Goddesses
    gods_map = {
        "krishna": "God", "radha": "Goddess", "shiva": "God", "parvati": "Goddess",
        "ram": "God", "sita": "Goddess", "hanuman": "God", "ganesh": "God",
        "lakshmi": "Goddess", "durga": "Goddess", "saraswati": "Goddess",
        "vishnu": "God", "brahma": "God"
    }
    for g, cat in gods_map.items():
        if g in low:
            entities.append({"name": g.capitalize(), "category": cat})

    # 2. Landmarks / Buildings
    buildings_map = {
        "eiffel tower": "Building", "taj mahal": "Building", "statue of liberty": "Monument",
        "colosseum": "Historical Place", "empire state": "Building", "pyramids": "Historical Place"
    }
    for b, cat in buildings_map.items():
        if b in low:
            entities.append({"name": b.title(), "category": cat})

    # 3. Animals & Birds
    animals_map = {
        "dog": "Animal", "cat": "Animal", "lion": "Animal", "tiger": "Animal",
        "bear": "Animal", "peacock": "Bird", "eagle": "Bird", "horse": "Animal"
    }
    for a, cat in animals_map.items():
        if f" {a}" in f" {low}" or f"{a}s" in low:
            entities.append({"name": a.capitalize(), "category": cat})

    # 4. Extract Proper Nouns via title casing (e.g. Person, Celebrity)
    words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", prompt)
    for word in words:
        word_lower = word.lower()
        if word_lower in ["the", "a", "an", "in", "on", "at", "by", "for", "with", "and"]:
            continue
        if any(e["name"].lower() == word_lower for e in entities):
            continue

        cat = "Person"
        if any(x in word_lower for x in ["virat", "kohli", "dhoni", "sachin", "tendulkar"]):
            cat = "Cricketer"
        elif any(x in word_lower for x in ["gandhi", "lincoln", "einstein", "newton"]):
            cat = "Historical Personality"
        elif any(x in word_lower for x in ["yamuna", "ganges", "nile", "amazon"]):
            cat = "River"

        entities.append({"name": word, "category": cat})

    return entities
