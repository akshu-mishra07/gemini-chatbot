from __future__ import annotations

"""
pipeline.py - Hardened orchestrator coordinating extraction, optimization, routing, validation, logging, and retries.
"""

import sys
import datetime
import os
import json
from PIL import Image

from image_pipeline.entities import extract_entities
from image_pipeline.optimizer import optimize_prompt
from image_pipeline.providers import (
    OpenAIProvider,
    GeminiProvider,
    HuggingFaceProvider,
    PollinationsProvider,
    StabilityAIProvider,
    ReplicateProvider,
    FalAIProvider
)


def _should_retry_exception(exc: Exception) -> bool:
    """
    Check if the exception is a transient error that warrants a retry:
    429 (rate limit), 5xx (server error), Timeout, Connection reset, or Empty response.
    """
    exc_str = str(exc).lower()
    
    # 1. Connection/Timeout errors
    if "timeout" in exc_str or "connection" in exc_str or "read timed out" in exc_str or "connection reset" in exc_str:
        return True
        
    # 2. HTTP status codes (from requests HTTPError)
    import requests
    if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None:
        status_code = exc.response.status_code
        if status_code in [429, 500, 502, 503, 504]:
            return True
            
    # 3. Text/String matching for generic HTTP status codes
    for code in ["429", "500", "502", "503", "504"]:
        if code in exc_str:
            return True
            
    # 4. Empty responses
    if "empty" in exc_str or "returned no" in exc_str:
        return True
        
    return False


def run_pipeline(
    prompt: str | None,
    gemini_key: str | None = None,
    openai_key: str | None = None,
    style_override: str | None = None,
    aspect_ratio_override: str | None = None,
    provider_override: str | None = None,
    quality_override: str | None = "Standard",
    bypass_cache: bool = False,
    allow_placeholder: bool | None = None
) -> dict:
    """
    Orchestrates the entire image generation process:
      1. Cache lookup
      2. Entity extraction (guaranteed fallback)
      3. Prompt optimization & style analysis (guaranteed fallback)
      4. Provider routing with cooldown check
      5. Auto-retries (up to 3 times) for transient issues
      6. Post-validation checks
      7. Caching & Database recording & Disk logging
    """
    start_time = datetime.datetime.now()
    if not prompt or not isinstance(prompt, str):
        return {
            "success": False,
            "status": "failed",
            "provider": "None",
            "image_path": "",
            "filepath": "",
            "image_url": "",
            "error": "Prompt cannot be empty or None for image generation.",
            "original_prompt": "",
            "enhanced_prompt": "",
            "entities": [],
            "style": "Photorealistic",
            "aspect_ratio": "1:1",
            "generation_time_sec": 0.0,
            "image": None,
            "metadata": {}
        }

    # Load or initialize manager
    manager = None
    try:
        import streamlit as st
        if "provider_manager" not in st.session_state:
            from image_pipeline.manager import ImageProviderManager
            st.session_state.provider_manager = ImageProviderManager()
        manager = st.session_state.provider_manager
    except Exception:
        from image_pipeline.manager import ImageProviderManager
        global_manager = globals().get("_global_provider_manager")
        if not global_manager:
            global_manager = ImageProviderManager()
            globals()["_global_provider_manager"] = global_manager
        manager = global_manager

    # Check cache
    if not bypass_cache:
        cached = manager.get_cached_result(prompt, style_override, aspect_ratio_override, quality_override)
        if cached:
            # Determine resolved placeholder allowance
            is_test_env = os.environ.get("OMNICHAT_SCHEDULER_DISABLE") == "1"
            resolved_allow_placeholder = is_test_env if allow_placeholder is None else allow_placeholder
            if cached.get("is_placeholder", False) and not resolved_allow_placeholder:
                print(f"[Pipeline] Bypassing cached placeholder because resolved_allow_placeholder=False", file=sys.stderr)
            else:
                print(f"[Pipeline] Return cached image for prompt: {repr(prompt)}", file=sys.stderr)
                return cached

    # Determine placeholder allowance
    is_test_env = os.environ.get("OMNICHAT_SCHEDULER_DISABLE") == "1"
    if allow_placeholder is None:
        allow_placeholder = is_test_env

    print(f"[Pipeline] Initializing run for: {repr(prompt)}", file=sys.stderr)

    # 1. Extract Entities (validated list)
    entities = []
    try:
        entities = extract_entities(prompt, api_key=gemini_key)
    except Exception as ent_err:
        print(f"[Pipeline Warning] Entity extraction failed: {ent_err}", file=sys.stderr)

    # 2. Optimize prompt (guaranteed fallback to original prompt)
    optimized = prompt
    meta = {
        "style": style_override or "Photorealistic",
        "aspect_ratio": aspect_ratio_override or "1:1",
        "negative_prompt": (
            "blurry, duplicate limbs, extra fingers, cropped face, low resolution, artifacts, "
            "bad anatomy, poor lighting, low quality, bad hands, noise, watermarks, text, logo, compression"
        )
    }
    
    try:
        opt, m = optimize_prompt(
            prompt,
            entities,
            style_override=style_override,
            aspect_ratio_override=aspect_ratio_override
        )
        if opt:
            optimized = opt
            meta = m
    except Exception as opt_err:
        print(f"[Pipeline Warning] Prompt optimization failed: {opt_err}. Using fallback.", file=sys.stderr)

    ar = meta.get("aspect_ratio", "1:1")
    neg = meta.get("negative_prompt", "")
    quality = quality_override or "Standard"

    # 3. Configure providers in preferred order: Imagen -> OpenAI -> Stability -> Replicate -> Fal.ai -> HF -> Pollinations
    openai_prov = OpenAIProvider(api_key=openai_key)
    gemini_prov = GeminiProvider(api_key=gemini_key)
    stability_prov = StabilityAIProvider()
    replicate_prov = ReplicateProvider()
    fal_prov = FalAIProvider()
    hf_prov = HuggingFaceProvider()
    pollinations_prov = PollinationsProvider()

    providers = []
    if provider_override and provider_override != "Auto":
        mapping = {
            "Google Imagen 3": gemini_prov,
            "OpenAI DALL-E 3": openai_prov,
            "Stability AI": stability_prov,
            "Replicate": replicate_prov,
            "Fal.ai": fal_prov,
            "HuggingFace (FLUX / SDXL)": hf_prov,
            "Pollinations.ai (Flux Fallback)": pollinations_prov
        }
        selected = mapping.get(provider_override)
        if selected and selected.is_available():
            providers = [selected]
        else:
            print(f"[Pipeline Warning] Chosen provider {provider_override} is not available/configured. Falling back to Auto-routing.", file=sys.stderr)

    if not providers:
        # Preferred order: Google Imagen -> OpenAI -> Stability AI -> Replicate -> Fal.ai -> HF -> Pollinations
        all_ordered = [
            gemini_prov,
            openai_prov,
            stability_prov,
            replicate_prov,
            fal_prov,
            hf_prov,
            pollinations_prov
        ]
        for prov in all_ordered:
            if prov.is_available():
                providers.append(prov)

    # Hard absolute fallback
    if not providers:
        providers = [pollinations_prov]

    # Skip any providers currently on cooldown
    active_providers = []
    for prov in providers:
        if manager.is_cooling_down(prov.provider_name):
            print(f"[Pipeline] Skipping provider '{prov.provider_name}' because it is on cooldown.", file=sys.stderr)
            continue
        active_providers.append(prov)

    # If all configured active providers are on cooldown, clear cooldowns to try them as a last resort
    if not active_providers:
        print("[Pipeline Warning] All configured providers are on cooldown! Clearing cooldown states to retry.", file=sys.stderr)
        active_providers = providers

    # 4. Generate with Auto-Retries & Fallbacks
    img = None
    active_provider = None
    last_error = None
    attempts_log = []
    is_placeholder = False

    for provider in active_providers:
        active_provider = provider
        # Up to 3 attempts per provider
        for attempt in range(1, 4):
            attempt_start = datetime.datetime.now()
            try:
                print(f"[Pipeline] Querying {provider.provider_name} (Attempt {attempt}/3)...", file=sys.stderr)
                img = provider.generate(optimized, ar, neg, quality)
                
                # Post-Validation check
                if img is None:
                    raise ValueError(f"Provider {provider.provider_name} returned None image object.")
                
                # Check dimensions and corruption
                width, height = img.size
                if width <= 0 or height <= 0:
                    raise ValueError(f"Provider {provider.provider_name} returned invalid dimensions: {width}x{height}")
                
                # Success
                attempts_log.append({
                    "provider": provider.provider_name,
                    "attempt": attempt,
                    "status": "success",
                    "duration_sec": round((datetime.datetime.now() - attempt_start).total_seconds(), 2)
                })
                break
            except Exception as e:
                last_error = e
                # Update cooldown tracker if 429 rate limits are hit
                manager.handle_provider_error(provider.provider_name, e)
                
                duration = round((datetime.datetime.now() - attempt_start).total_seconds(), 2)
                attempts_log.append({
                    "provider": provider.provider_name,
                    "attempt": attempt,
                    "status": "failed",
                    "error": str(e),
                    "duration_sec": duration
                })
                
                # If not retryable, break to try next provider in fallback chain
                if not _should_retry_exception(e):
                    print(f"[Pipeline] Transient retry check passed: exception is non-transient. Skipping further retries on {provider.provider_name}.", file=sys.stderr)
                    break
                
                if attempt < 3:
                    import time
                    sleep_sec = attempt * 5
                    if "429" in str(e) or "too many requests" in str(e).lower() or "rate limit" in str(e).lower():
                        sleep_sec = attempt * 20
                    print(f"[Pipeline] Transient error hit. Sleeping for {sleep_sec}s before retry...", file=sys.stderr)
                    time.sleep(sleep_sec)
                
        if img is not None:
            break

    if img is None:
        if allow_placeholder:
            print("[Pipeline Fallback] All online backends failed/throttled. Generating a local fallback placeholder image.", file=sys.stderr)
            is_placeholder = True
            img = Image.new("RGB", (512, 512), color=(48, 25, 82))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), "Fallback Placeholder", fill=(255, 255, 255))
            draw.text((20, 50), f"Prompt: {prompt[:40]}...", fill=(200, 200, 200))
            draw.text((20, 80), f"Reason: All providers failed/throttled", fill=(220, 100, 100))
        else:
            err_msg = "No online image provider is currently available. Please try again later."
            detailed_log = {
                "timestamp": datetime.datetime.now().isoformat(),
                "original_prompt": prompt,
                "attempts": attempts_log,
                "last_error": str(last_error)
            }
            print(f"[Pipeline Critical Error] Full trace: {json.dumps(detailed_log, indent=2)}", file=sys.stderr)
            
            return {
                "success": False,
                "status": "failed",
                "is_placeholder": False,
                "provider": "None",
                "image_path": "",
                "filepath": "",
                "image_url": "",
                "error": err_msg,
                "original_prompt": prompt,
                "enhanced_prompt": optimized,
                "entities": entities,
                "style": meta.get("style", "Photorealistic"),
                "aspect_ratio": ar,
                "generation_time_sec": round((datetime.datetime.now() - start_time).total_seconds(), 2),
                "image": None,
                "metadata": meta
            }

    # 5. Save generated image safely
    from image_generator import save_generated_image
    try:
        filepath = save_generated_image(img, prompt)
    except Exception as save_err:
        err_msg = f"Successfully generated image but failed to write to disk: {save_err}"
        return {
            "success": False,
            "status": "failed",
            "is_placeholder": is_placeholder,
            "provider": "Placeholder" if is_placeholder else (active_provider.provider_name if active_provider else "None"),
            "image_path": "",
            "filepath": "",
            "image_url": "",
            "error": err_msg,
            "original_prompt": prompt,
            "enhanced_prompt": optimized,
            "entities": entities,
            "style": meta.get("style", "Photorealistic"),
            "aspect_ratio": ar,
            "generation_time_sec": round((datetime.datetime.now() - start_time).total_seconds(), 2),
            "image": None,
            "metadata": meta
        }

    generation_time = (datetime.datetime.now() - start_time).total_seconds()
    
    result = {
        "success": True,
        "status": "success",
        "is_placeholder": is_placeholder,
        "provider": "Placeholder" if is_placeholder else (active_provider.provider_name if active_provider else "None"),
        "image_path": filepath,
        "filepath": filepath,
        "image_url": "",
        "error": "Fallback placeholder generated." if is_placeholder else None,
        "original_prompt": prompt,
        "enhanced_prompt": optimized,
        "entities": entities,
        "style": meta.get("style", "Photorealistic"),
        "aspect_ratio": ar,
        "generation_time_sec": round(generation_time, 2),
        "attempts": attempts_log,
        "metadata": meta,
        "image": img
    }

    # 6. Save companion log next to the image file
    try:
        log_path = filepath.rsplit(".", 1)[0] + ".log"
        with open(log_path, "w", encoding="utf-8") as lf:
            json.dump(result, lf, indent=2, default=str)
    except Exception as log_err:
        print(f"[Pipeline Warning] Could not write companion log file: {log_err}", file=sys.stderr)

    # 7. Persistent DB record
    try:
        from database.storage import record_image_generation_history
        record_image_generation_history(result)
    except Exception as dberr:
        print(f"[Pipeline Warning] Could not record history to SQLite: {dberr}", file=sys.stderr)

    # 8. Cache result successfully
    manager.cache_result(prompt, style_override, aspect_ratio_override, quality_override, result)

    return result
