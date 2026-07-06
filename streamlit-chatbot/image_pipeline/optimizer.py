from __future__ import annotations

"""
optimizer.py - Hardened scene understanding, style engine, and prompt optimization.
"""

import re


SUPPORTED_STYLES = [
    "Photorealistic", "DSLR", "Portrait", "Fantasy", "Oil Painting",
    "Watercolor", "Anime", "Ghibli", "Comic", "Pixar", "3D Render",
    "Sketch", "Cyberpunk", "Concept Art", "Digital Art", "Minimal",
    "Low Poly", "Pixel Art", "Fantasy Illustration"
]


def classify_prompt_category(prompt: str) -> str | None:
    low = prompt.lower()
    
    # 1. Celebrity / Sports Person
    celebrities = ["virat kohli", "narendra modi", "elon musk", "sachin tendulkar", "messi", "ronaldo", "dhoni", "kohli", "modi", "musk", "tendulkar"]
    if any(name in low for name in celebrities):
        return "Celebrity"
        
    # 2. God/Goddess
    gods = ["krishna", "shiva", "radha", "goddess", "deity", "jesus", "buddha", "vishnu", "ganesha", "ram", "durga"]
    if any(god in low for god in gods):
        return "God/Goddess"
        
    # 3. Scientific Diagram
    if any(w in low for w in ["diagram", "scientific", "cell", "molecule", "anatomy chart", "geological section"]):
        return "Scientific Diagram"
        
    # 4. Medical Illustration
    if any(w in low for w in ["medical", "biological", "microscopic", "organism", "illustration of a", "pathology", "disease cell"]):
        return "Medical Illustration"
        
    # 5. Vehicle
    if any(w in low for w in ["car", "ferrari", "porsche", "tesla", "vehicle", "automobile", "sports car", "jet", "plane", "motorcycle"]):
        return "Vehicle"
        
    # 6. Landscape
    if any(w in low for w in ["sunset", "galaxy", "landscape", "scenery", "mountains", "everest", "view", "sea", "ocean", "nature", "forest"]):
        return "Landscape"
        
    # 7. Animal
    if any(w in low for w in ["animal", "lion", "tiger", "panda", "cat", "dog", "retriever", "peacock", "bird", "wolf", "bear"]):
        return "Animal"
        
    # 8. Logo
    if any(w in low for w in ["logo", "brand mark", "vector logo", "emblem"]):
        return "Logo"
        
    # 9. Product
    if any(w in low for w in ["product", "bottle", "watch", "perfume", "sneaker", "gadget", "commercial photography"]):
        return "Product"
        
    # 10. Architecture
    if any(w in low for w in ["taj mahal", "eiffel", "castle", "temple", "ruins", "architecture", "building", "house", "room", "apartment"]):
        return "Architecture"
        
    # 11. Food
    if any(w in low for w in ["food", "dish", "burger", "pizza", "sushi", "cake", "salad", "recipe"]):
        return "Food"
        
    # 12. Painting
    if any(w in low for w in ["painting", "oil painting", "watercolor", "canvas", "artwork"]):
        return "Painting"
        
    # 13. Anime
    if any(w in low for w in ["anime", "manga", "ghibli", "cel shading", "illustration"]):
        return "Anime"
        
    return None


def optimize_prompt(
    prompt: str,
    entities: list[dict] | None,
    style_override: str | None = None,
    aspect_ratio_override: str | None = None
) -> tuple[str, dict]:
    """
    Rewrites the prompt into a rich, detailed cinematic version using style maps and entity contexts.
    Returns (optimized_prompt, metadata).
    """
    if not prompt or not isinstance(prompt, str):
        return "", {
            "style": "Photorealistic",
            "aspect_ratio": "1:1",
            "negative_prompt": "blurry, low quality"
        }

    raw_prompt = prompt.strip()
    low_prompt = raw_prompt.lower()
    
    if entities is None:
        entities = []

    # 1. Style Detection
    style = "Photorealistic"
    if style_override and style_override in SUPPORTED_STYLES:
        style = style_override
    else:
        for s in SUPPORTED_STYLES:
            if s.lower() in low_prompt:
                style = s
                break

    # Determine category
    category = classify_prompt_category(low_prompt)

    # 2. Category & Context Extraction from entities list
    categories = set()
    for e in entities:
        if isinstance(e, dict) and "category" in e and e["category"] is not None:
            categories.add(e["category"])

    has_god = any(cat in ["God", "Goddess"] for cat in categories) or (category == "God/Goddess")
    has_human = any(cat in ["Person", "Cricketer", "Footballer", "Historical Personality"] for cat in categories) or has_god or (category == "Celebrity")
    has_animal = any(cat in ["Animal", "Bird"] for cat in categories) or (category == "Animal")
    has_building = any(cat in ["Building", "Monument", "Historical Place"] for cat in categories) or (category == "Architecture")
    has_river = any(cat in ["River"] for cat in categories)

    # 3. Style-specific Prefix / Framework
    style_boosters_by_style = {
        "Photorealistic": "A highly detailed photorealistic DSLR photograph of",
        "DSLR": "A professional DSLR photography of",
        "Portrait": "A close-up studio portrait photography of",
        "Fantasy": "An epic fantasy digital painting of",
        "Oil Painting": "A classic textured oil painting of",
        "Watercolor": "A delicate artistic watercolor painting of",
        "Anime": "A vibrant anime key visual illustration of",
        "Ghibli": "A whimsical studio ghibli art style drawing of",
        "Comic": "A detailed comic book illustration of",
        "Pixar": "A highly detailed 3D Pixar character render of",
        "3D Render": "A physically based 3D render of",
        "Sketch": "A detailed pencil sketch drawing of",
        "Cyberpunk": "A neon-lit futuristic cyberpunk style painting of",
        "Concept Art": "A professional video game concept art of",
        "Digital Art": "A masterfully created digital art of",
        "Minimal": "A clean elegant minimalist design of",
        "Low Poly": "A beautiful low poly 3D design of",
        "Pixel Art": "A retro 8-bit detailed pixel art of",
        "Fantasy Illustration": "A whimsical fantasy illustration of"
    }

    style_boosters_by_category = {
        "Celebrity": "Ultra realistic professional sports portrait of",
        "God/Goddess": "Beautiful devotional artwork of",
        "Scientific Diagram": "Accurate detailed scientific diagram of",
        "Medical Illustration": "High quality detailed medical illustration of",
        "Vehicle": "Sleek aerodynamic high-speed photograph of",
        "Landscape": "Vibrant cinematic landscape of",
        "Animal": "Stunning wildlife photography of",
        "Logo": "Minimalist modern commercial logo design of",
        "Product": "Professional commercial product photography of",
        "Architecture": "An architecturally accurate DSLR photograph of",
        "Food": "Mouth-watering professional studio food photography of",
        "Painting": "A classic textured masterwork painting of",
        "Anime": "A vibrant anime key visual illustration of",
    }

    # Determine Prefix
    prefix = None
    if style_override and style_override != "Auto":
        prefix = style_boosters_by_style.get(style_override)
    elif category in style_boosters_by_category:
        prefix = style_boosters_by_category[category]
        if category in ["Celebrity", "Vehicle", "Architecture", "Food"]:
            style = "DSLR"
        elif category in ["God/Goddess", "Painting"]:
            style = "Oil Painting"
        elif category in ["Anime"]:
            style = "Anime"
    else:
        prefix = style_boosters_by_style.get(style)

    base_subject = raw_prompt
    if prefix:
        low_prefix = prefix.lower()
        if not low_prompt.startswith(low_prefix[:10]):
            base_subject = f"{prefix} {raw_prompt}"

    # 4. Scenario Enhancements
    enhancements = []

    # Quality boosters
    if style in ["Photorealistic", "DSLR", "Portrait"]:
        enhancements.extend([
            "ultra realistic", "8K resolution", "HDR", "DSLR quality", "natural lighting",
            "golden ratio composition", "rich textures", "sharp focus", "depth of field",
            "professional color grading", "physically based rendering", "cinematic composition",
            "soft shadows", "studio quality", "extremely detailed", "masterpiece"
        ])

    # Category specific detail boosters
    if category == "Celebrity":
        enhancements.extend([
            "natural lighting", "DSLR photography", "8K", "cinematic composition", 
            "ultra detailed", "realistic skin textures", "accurate anatomy", "correct eyes"
        ])
    elif category == "God/Goddess":
        enhancements.extend([
            "traditional Indian attire", "divine aura", "intricate jewelry", "lotus flowers", 
            "temple background", "highly detailed digital painting", "serene facial expression"
        ])
    elif category == "Scientific Diagram":
        enhancements.extend([
            "clear labeling", "high resolution vector style", "clean layout", "highly detailed"
        ])
    elif category == "Medical Illustration":
        enhancements.extend([
            "anatomical precision", "rich textures", "3D visualization style", "highly detailed",
            "clean surgical medical background"
        ])
    elif category == "Vehicle":
        enhancements.extend([
            "motion blur background", "realistic metallic reflections", "dynamic angle", "sharp focus"
        ])
    elif category == "Landscape":
        enhancements.extend([
            "majestic vista", "volumetric lighting", "HDR", "high dynamic range", "breathtaking panoramic photography"
        ])
    elif category == "Food":
        enhancements.extend([
            "macro lens", "perfect studio lighting", "rich food textures", "appetizing colors"
        ])
    elif category == "Logo":
        enhancements.extend([
            "clean vector art", "high contrast", "elegant typography style", "flat design icon"
        ])
    elif category == "Product":
        enhancements.extend([
            "studio softbox lighting", "clean studio background", "highly detailed", "sharp focus"
        ])

    # Legacy fallback entities
    if has_god and category != "God/Goddess":
        enhancements.extend([
            "respectful devotional atmosphere consistent with traditional classical iconography",
            "ornate traditional attire and intricate golden jewelry", "serene divine facial expression",
            "soft glowing aura and halo", "rich colors", "majestic elegant presentation"
        ])
    elif has_human and category != "Celebrity" and category != "God/Goddess":
        enhancements.extend([
            "high facial details", "accurate anatomy", "correct hands", "correct fingers",
            "correct eyes", "natural skin texture", "natural expressions", "realistic hair",
            "realistic skin texture"
        ])

    if has_animal and category != "Animal":
        enhancements.extend([
            "photorealistic wildlife photography style", "National Geographic quality",
            "detailed natural fur and feather textures", "sharp focus on eyes", "realistic natural lighting"
        ])

    if has_building and category != "Architecture":
        enhancements.extend([
            "architecturally accurate visual characteristics", "clean perspective lines",
            "volumetric lighting", "physically accurate reflections and shadows", "realistic weather atmosphere"
        ])

    if has_river:
        enhancements.extend([
            "shimmering realistic water reflections", "rippling water textures", "scenic natural environment"
        ])

    # 5. Aspect Ratio Mapping
    aspect_ratio = "1:1"
    if aspect_ratio_override:
        aspect_ratio = aspect_ratio_override
    else:
        if any(cat in ["Building", "Monument", "Historical Place", "River"] for cat in categories) or any(w in low_prompt for w in ["scenery", "landscape", "sunset", "view", "wide"]):
            aspect_ratio = "16:9"
        elif has_human or "portrait" in low_prompt:
            aspect_ratio = "3:4"

    # Assemble unique modifications
    seen = set()
    unique_enhancements = []
    for item in enhancements:
        item_clean = item.lower().strip()
        if item_clean not in low_prompt and item_clean not in seen:
            seen.add(item_clean)
            unique_enhancements.append(item)

    final_prompt = base_subject
    if unique_enhancements:
        final_prompt = f"{base_subject}, " + ", ".join(unique_enhancements)

    meta = {
        "style": style,
        "aspect_ratio": aspect_ratio,
        "negative_prompt": (
            "blurry, duplicate limbs, extra fingers, cropped face, low resolution, artifacts, "
            "bad anatomy, poor lighting, low quality, bad hands, noise, watermarks, text, logo, compression"
        )
    }

    return final_prompt, meta
