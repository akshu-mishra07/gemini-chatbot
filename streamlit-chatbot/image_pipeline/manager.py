import os
import sys
import datetime

class ImageProviderManager:
    def __init__(self):
        self.cooldowns = {}  # provider_name -> expire_datetime
        self.cache = {}      # cache_key -> result_dict

    def mark_cooldown(self, provider_name: str, duration_minutes: int = 5):
        self.cooldowns[provider_name] = datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)

    def is_cooling_down(self, provider_name: str) -> bool:
        expire_time = self.cooldowns.get(provider_name)
        if expire_time:
            if datetime.datetime.now() < expire_time:
                return True
            else:
                # Cooldown expired, remove
                del self.cooldowns[provider_name]
        return False

    def handle_provider_error(self, provider_name: str, exception: Exception):
        exc_str = str(exception).lower()
        if "429" in exc_str or "too many requests" in exc_str or "rate limit" in exc_str:
            self.mark_cooldown(provider_name, duration_minutes=5)
        else:
            # 3-minute cooldown for other failures (e.g. 404, 500, timeouts)
            # to prevent unhealthy providers from locking out healthy fallbacks
            self.mark_cooldown(provider_name, duration_minutes=3)

    def get_cached_result(self, prompt: str, style: str | None, aspect_ratio: str | None, quality: str | None) -> dict | None:
        key = (prompt.strip().lower(), style or "Auto", aspect_ratio or "Auto", quality or "Standard")
        cached = self.cache.get(key)
        if cached:
            # Check if file still exists on disk
            img_path = cached.get("image_path") or cached.get("filepath")
            if img_path and os.path.exists(img_path):
                print(f"[Provider Manager] Memory cache hit for prompt: '{prompt}'", file=sys.stderr)
                return cached
            else:
                # File deleted or missing, invalidate cache
                del self.cache[key]

        # Check SQLite db if not in memory cache
        try:
            from database.storage import fetch_one
            import json
            row = fetch_one(
                "SELECT * FROM generated_images_history WHERE LOWER(original_prompt) = ? AND (style = ? OR ? = 'Auto') AND (aspect_ratio = ? OR ? = 'Auto') ORDER BY created_at DESC LIMIT 1",
                (prompt.strip().lower(), style or "Auto", style or "Auto", aspect_ratio or "Auto", aspect_ratio or "Auto")
            )
            if row:
                img_path = row.get("filepath")
                if img_path and os.path.exists(img_path):
                    # Reconstruct result dict
                    try:
                        entities = json.loads(row.get("detected_entities", "[]"))
                    except Exception:
                        entities = []
                    
                    is_placeholder = "placeholder" in row.get("provider", "").lower()
                    result = {
                        "success": True,
                        "status": "success",
                        "is_placeholder": is_placeholder,
                        "provider": row.get("provider", "None"),
                        "image_path": img_path,
                        "filepath": img_path,
                        "image_url": "",
                        "error": "Fallback placeholder generated." if is_placeholder else None,
                        "original_prompt": row.get("original_prompt", ""),
                        "enhanced_prompt": row.get("enhanced_prompt", ""),
                        "entities": entities,
                        "style": row.get("style", "Photorealistic"),
                        "aspect_ratio": row.get("aspect_ratio", "1:1"),
                        "generation_time_sec": row.get("generation_time", 0.0),
                        "metadata": {
                            "style": row.get("style", "Photorealistic"),
                            "aspect_ratio": row.get("aspect_ratio", "1:1")
                        }
                    }
                    # Populate in-memory cache
                    self.cache[key] = result
                    print(f"[Provider Manager] Persistent DB Cache hit for prompt: '{prompt}' -> {img_path}", file=sys.stderr)
                    return result
        except Exception as db_cache_err:
            print(f"[Provider Manager Warning] Persistent cache check failed: {db_cache_err}", file=sys.stderr)
            
        return None

    def cache_result(self, prompt: str, style: str | None, aspect_ratio: str | None, quality: str | None, result: dict):
        key = (prompt.strip().lower(), style or "Auto", aspect_ratio or "Auto", quality or "Standard")
        self.cache[key] = result
        print(f"[Provider Manager] Cached successfully under key: {key}", file=sys.stderr)
