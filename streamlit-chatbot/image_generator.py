from __future__ import annotations

"""
image_generator.py - Real AI image generation engine with prompt optimization.

Features:
  - Automatic prompt enhancement & optimization templates
  - Category context detection (Human, God/Goddess, Animal, Architecture, etc.)
  - Style detection & default inference (photorealistic, oil painting, sketch, etc.)
  - Aspect ratio resolution mapping
  - Dual prompt logging
  - In-memory optimization caching
"""

import os
import io
import sys
import datetime
import hashlib
import urllib.parse
import requests
from PIL import Image

# In-memory cache for prompt optimizations
_OPTIMIZER_CACHE = {}


def get_optimized_prompt(prompt: str) -> tuple[str, dict]:
    """
    Analyzes and optimizes a user prompt into a high-quality, descriptive prompt.
    Returns (optimized_prompt, metadata_dict).
    """
    import re
    raw_prompt = prompt.strip()
    if not raw_prompt:
        return "", {}

    # Check cache
    cache_key = hashlib.sha256(raw_prompt.encode("utf-8")).hexdigest()
    if cache_key in _OPTIMIZER_CACHE:
        return _OPTIMIZER_CACHE[cache_key]

    low_prompt = raw_prompt.lower()

    # 0. Simple/Short Prompt expansions (per Optimizer rules)
    simple_mappings = {
        "dog": "A photorealistic golden retriever sitting in a lush green park during golden hour",
        "cat": "A photorealistic tabby cat sitting near a sunlit window with dust motes in the air",
        "car": "A sleek modern red sports car driving on a coastal highway at dusk",
        "flower": "A close-up macro photograph of a blooming red rose with morning dew drops",
        "house": "A cozy rustic wooden cabin nestled in a snowy pine forest under the northern lights",
        "mountain": "A majestic snow-capped mountain peak reflecting in a crystal clear alpine lake",
        "city": "A vibrant futuristic cyberpunk city street with neon signs and flying vehicles",
    }

    stripped_key = re.sub(r"[^a-z\s]", "", low_prompt).strip()
    base_text = raw_prompt
    if stripped_key in simple_mappings:
        base_text = simple_mappings[stripped_key]
    elif "radha" in low_prompt and "krishna" in low_prompt and "swing" in low_prompt:
        base_text = (
            "Radha and Krishna seated together on a beautifully decorated traditional swing "
            "beside the Yamuna River during sunset, surrounded by blooming flowers, peacocks, "
            "lush greenery and soft golden light, devotional atmosphere, intricate traditional attire"
        )

    # 1. Style Detection
    styles = {
        "oil painting": "oil painting",
        "watercolor": "watercolor painting",
        "anime": "anime style",
        "ghibli": "studio ghibli art style",
        "sketch": "pencil sketch",
        "pencil sketch": "pencil sketch",
        "digital painting": "digital painting",
        "fantasy art": "fantasy art style",
        "cinematic": "cinematic movie style",
        "concept art": "detailed concept art",
        "studio portrait": "studio portrait photography",
        "watercolor painting": "watercolor painting",
        "drawing": "drawing illustration",
        "cartoon": "cartoon illustration",
        "pixel art": "pixel art",
        "3d render": "3d render",
    }

    detected_style = None
    for key, style_val in styles.items():
        if key in low_prompt:
            detected_style = style_val
            break

    if not detected_style:
        if any(w in low_prompt for w in ["movie", "scene", "dramatic", "cinematic", "film"]):
            detected_style = "cinematic"
        elif any(w in low_prompt for w in ["dragon", "magic", "wizard", "elf", "mythical", "fairy", "fantasy"]):
            detected_style = "fantasy art"
        elif any(w in low_prompt for w in ["portrait", "face", "headshot"]):
            detected_style = "studio portrait"
        else:
            detected_style = "photorealistic"

    # 2. Context Detection
    contexts = []

    # Gods & Goddesses check
    gods = ["krishna", "radha", "shiva", "parvati", "ram", "sita", "hanuman", "ganesh", "lakshmi", "durga", "saraswati", "vishnu", "brahma"]
    is_god = any(f"\\b{g}\\b" in low_prompt or g in low_prompt for g in gods)

    # Humans/Celebrities/Historical Figures
    humans = ["man", "woman", "person", "girl", "boy", "doctor", "agent", "child", "officer", "nurse", "lady", "guy", "face", "model", "actor", "actress", "president", "king", "queen", "soldier", "warrior", "monk", "priest", "worker", "human", "people"]
    is_human = any(w in low_prompt for w in humans) or is_god

    # Animals
    animals = ["dog", "cat", "lion", "tiger", "bear", "wolf", "bird", "peacock", "horse", "elephant", "deer", "eagle", "hawk", "monkey", "fox", "cow", "rabbit", "animal", "pet", "fish", "shark", "whale", "dolphin", "snake", "leopard", "cheetah"]
    is_animal = any(w in low_prompt for w in animals)

    # Landscapes
    landscapes = ["sunset", "sunrise", "mountain", "river", "lake", "ocean", "sea", "beach", "forest", "desert", "scenery", "landscape", "waterfall", "sky", "valley", "canyon", "clouds", "nature"]
    is_landscape = any(w in low_prompt for w in landscapes)

    # Architecture
    architectures = ["building", "temple", "house", "castle", "skyscraper", "palace", "tower", "cathedral", "church", "monument", "bridge", "architecture", "room", "interior", "cabin", "street", "cityscape"]
    is_architecture = any(w in low_prompt for w in architectures)

    # Objects
    objects = ["car", "watch", "phone", "laptop", "computer", "coffee", "cup", "mug", "bottle", "shoe", "bag", "chair", "table", "guitar", "piano", "object", "food", "cake", "fruit", "product", "toy"]
    is_object = any(w in low_prompt for w in objects)

    # 3. Enhance Prompt based on categories
    enhancements = []

    if detected_style in ["photorealistic", "cinematic", "studio portrait", "portrait"]:
        enhancements.extend([
            "ultra realistic", "photorealistic", "high resolution", "8K quality", "DSLR photography",
            "ultra detailed", "sharp focus", "natural lighting", "physically accurate", "rich textures",
            "cinematic composition", "professional photography", "realistic shadows", "accurate colors"
        ])

    if is_god:
        contexts.append("God/Goddess")
        enhancements.extend([
            "respectful devotional atmosphere", "highly detailed artistic depiction matching traditional iconography",
            "ornate intricate jewelry and traditional attire", "serene divine facial expression", "soft glowing halo and aura",
            "rich vibrant colors", "elegant majestic presentation"
        ])
    elif is_human:
        contexts.append("Human")
        enhancements.extend([
            "highly detailed face", "correct anatomy", "natural skin tones", "facial symmetry", "natural expressions",
            "correct hands", "correct fingers", "proper body proportions", "realistic hair", "natural eyes",
            "high facial detail", "accurate clothing", "realistic skin texture", "sharp focus"
        ])

    if is_animal:
        contexts.append("Animal")
        enhancements.extend([
            "wildlife photography quality", "natural fur texture", "detailed eyes", "realistic lighting",
            "National Geographic style", "photorealistic textures", "sharp focus on eyes"
        ])

    if is_landscape:
        contexts.append("Landscape")
        enhancements.extend([
            "majestic landscape view", "scenic composition", "volumetric natural lighting", "high dynamic range",
            "vibrant sky details", "atmospheric depth", "breathtaking panoramic photography"
        ])

    if is_architecture:
        contexts.append("Architecture")
        enhancements.extend([
            "clean perspective lines", "intricate architectural details", "realistic materials and textures",
            "volumetric lighting", "dramatic sky background", "physically accurate reflection and shadows"
        ])

    if is_object:
        contexts.append("Object")
        enhancements.extend([
            "commercial product photography style", "studio lighting environment", "clean minimal background",
            "macro lens details", "realistic surface textures", "accurate reflections", "extremely sharp focus"
        ])

    # 4. Aspect Ratio Detection
    aspect_ratio = "1:1"
    if is_landscape or any(w in low_prompt for w in ["wide", "panorama", "wallpaper"]):
        aspect_ratio = "16:9"
    elif is_human or is_god or any(w in low_prompt for w in ["portrait", "vertical", "phone"]):
        aspect_ratio = "3:4"

    # 5. Build Final Optimized Prompt
    if detected_style and detected_style != "photorealistic" and detected_style not in low_prompt:
        base_text = f"A beautiful {detected_style} of {base_text}"

    seen = set()
    unique_enhancements = []
    for item in enhancements:
        item_clean = item.lower().strip()
        if item_clean not in low_prompt and item_clean not in seen:
            seen.add(item_clean)
            unique_enhancements.append(item)

    final_prompt = base_text
    if unique_enhancements:
        final_prompt = f"{base_text}, " + ", ".join(unique_enhancements)

    meta = {
        "style": detected_style,
        "contexts": contexts or ["General"],
        "aspect_ratio": aspect_ratio,
        "negative_prompt": (
            "blurry, low quality, distorted, duplicate limbs, extra fingers, extra arms, "
            "cropped face, watermark, text, logo, artifacts, poor anatomy, low resolution, noisy image"
        )
    }

    res_tuple = (final_prompt, meta)
    _OPTIMIZER_CACHE[cache_key] = res_tuple
    return res_tuple


def generate_image(prompt: str, api_key: str | None = None, aspect_ratio: str | None = None) -> Image.Image:
    """
    Generate a real AI image from the given prompt.
    Automatically enhances the prompt and uses dynamic aspect ratios.
    """
    from image_pipeline.pipeline import run_pipeline
    import os
    
    openai_key = os.environ.get("OPENAI_API_KEY")
    result = run_pipeline(
        prompt=prompt,
        gemini_key=api_key,
        openai_key=openai_key,
        aspect_ratio_override=aspect_ratio
    )
    return result["image"]


def save_generated_image(image: Image.Image, prompt: str) -> str:
    """Save generated image to ./generated_images/ and return the file path."""
    folder = "./generated_images"
    os.makedirs(folder, exist_ok=True)

    slug = "".join(c if c.isalnum() else "_" for c in prompt[:30]).strip("_") or "image"
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gen_{ts}_{slug}.png"
    filepath = os.path.join(folder, filename)

    image.save(filepath, "PNG")
    print(f"[Image Gen] Saved to: {filepath}", file=sys.stderr)
    return filepath
