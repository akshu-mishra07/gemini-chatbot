from __future__ import annotations

"""
verify_30_prompts.py - Phase 9 Final Validation Script
Generates 30 diverse prompts using the hardened modular image pipeline and verifies formatting, saves, and logging.
"""

import os
import sys
import time
import json
import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from image_pipeline.pipeline import run_pipeline


PROMPTS_30 = [
    # 1-15: Requested by user in Phase 4
    "Generate an image of Virat Kohli",
    "Generate an image of Narendra Modi",
    "Generate an image of Elon Musk",
    "Generate an image of Radha Rani",
    "Generate an image of Lord Krishna",
    "Generate an image of Lord Shiva",
    "Generate an image of Taj Mahal",
    "Generate an image of Golden Retriever",
    "Generate an image of Iron Man",
    "Generate an image of futuristic Mumbai",
    "Generate an image of Earth from Space",
    "Generate an image of a cyberpunk city",
    "Generate an image of Mount Everest",
    "Generate an image of a Peacock",
    "Generate an image of a Bengal Tiger",
    
    # 16-30: Additional diverse prompts to fulfill Phase 9
    "A cute baby panda eating bamboo in a misty forest",
    "Vibrant cherry blossoms blooming in Kyoto during spring watercolor style",
    "A majestic medieval castle on a rocky cliff overlooking a stormy sea",
    "Close-up portrait of a wise old wizard with a long silver beard",
    "Retro 8-bit pixel art of a cozy coffee shop in the rain",
    "Futuristic sports car speeding down a neon-lit highway 3D render",
    "Whimsical studio ghibli style meadow with floating lanterns",
    "A sleek modern minimalist living room with large glass windows",
    "Ancient ruins of a Greek temple under a starry night sky",
    "A colorful coral reef teeming with exotic tropical fish",
    "Surreal painting of a clock melting over a tree branch",
    "Epic battle scene between a red dragon and a knight in shining armor",
    "A cozy log cabin in the snowy mountains with smoke rising from chimney",
    "Abstract digital art with flowing gradients of purple and gold",
    "Vibrant low poly landscape of a desert canyon at sunset"
]


def run_validation():
    print("====================================================")
    print("      RUNNING PHASE 9 FINAL VALIDATION (30 PROMPTS)   ")
    print("====================================================\n")
    
    # Set HF and other configurations
    os.environ["OMNICHAT_SCHEDULER_DISABLE"] = "1"
    
    real_ai_count = 0
    placeholder_count = 0
    failed_count = 0
    failures = []
    
    for idx, prompt in enumerate(PROMPTS_30, 1):
        print(f"[{idx}/30] Prompt: {prompt}")
        start_time = time.time()
        
        result = run_pipeline(
            prompt=prompt,
            style_override="Auto",
            aspect_ratio_override="Auto",
            provider_override="Auto",
            quality_override="Standard",
            allow_placeholder=False
        )
        
        duration = time.time() - start_time
        is_real = result.get("success", False) and not result.get("is_placeholder", False)
        is_placeholder = result.get("success", False) and result.get("is_placeholder", False)
        is_failed = not result.get("success", False)
        
        if is_real:
            status_lbl = "REAL_GENERATED_IMAGE"
            real_ai_count += 1
        elif is_placeholder:
            status_lbl = "PLACEHOLDER_IMAGE"
            placeholder_count += 1
            print("  Fallback placeholder generated.")
        else:
            status_lbl = "FAILED"
            failed_count += 1
            print(f"  [ERROR] Generation failed: {result.get('error')}")
            failures.append((prompt, result.get("error", "Unknown error")))
            continue
            
        print(f"  Duration: {duration:.2f}s | Status: {status_lbl} | Provider: {result['provider']}")
            
        # Verify Phase 6 return dictionary fields
        assert "success" in result, "Missing 'success' field!"
        assert "provider" in result, "Missing 'provider' field!"
        assert "image_path" in result, "Missing 'image_path' field!"
        assert "image_url" in result, "Missing 'image_url' field!"
        assert "error" in result, "Missing 'error' field!"
        assert "is_placeholder" in result, "Missing 'is_placeholder' field!"
        
        # Verify file creation and content
        img_path = result["image_path"]
        assert img_path, "Result reports success but image_path is empty!"
        assert os.path.exists(img_path), f"File does not exist: {img_path}"
        
        # Verify companion log file
        log_path = img_path.rsplit(".", 1)[0] + ".log"
        assert os.path.exists(log_path), f"Companion log file does not exist: {log_path}"
        
        # Phase 8 detailed logging check
        print(f"  [OK] Saved to: {img_path}")
        print(f"  [OK] Companion log: {log_path}")
        print(f"  [OK] Optimized prompt preview: {result['enhanced_prompt'][:80]}...")
        print(f"  [OK] Detected Style: {result['style']} | Aspect Ratio: {result['aspect_ratio']}")
        
        print("-" * 50)
        if duration > 1.0:
            time.sleep(15)
        
    print("\n====================================================")
    print(f"                VALIDATION SUMMARY                 ")
    print("====================================================")
    print(f"Total Prompts:         30")
    print(f"Real AI Generated:     {real_ai_count}")
    print(f"Placeholder Fallbacks: {placeholder_count}")
    print(f"Failed:                {failed_count}")
    print("====================================================")
    
    if placeholder_count > 0:
        print(f"\n[FAIL] Validation did not satisfy project completion: {placeholder_count} placeholder fallback images were generated instead of real AI images.")
        sys.exit(1)
        
    if failed_count > 0 or failures:
        print("\nFailures:")
        for f_prompt, f_err in failures:
            print(f"  - {f_prompt}: {f_err}")
        sys.exit(1)
        
    print("\n[PASS] All 30 validation prompts completed and verified successfully!")
    sys.exit(0)


if __name__ == "__main__":
    run_validation()
