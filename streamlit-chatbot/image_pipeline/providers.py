from __future__ import annotations

"""
providers.py - Hardened image generation providers with explicit API response validation.
"""

import io
import os
import sys
import datetime
import urllib.parse
from abc import ABC, abstractmethod
from PIL import Image
import requests


class BaseImageProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the API keys/dependencies are present."""
        pass

    @abstractmethod
    def generate(self, prompt: str, aspect_ratio: str, negative_prompt: str, quality: str) -> Image.Image:
        """Generates the image and returns a PIL Image."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


class OpenAIProvider(BaseImageProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def provider_name(self) -> str:
        return "OpenAI DALL-E 3"

    def generate(self, prompt: str, aspect_ratio: str, negative_prompt: str, quality: str) -> Image.Image:
        if not self.is_available():
            raise ValueError("OpenAI API key is missing or not configured.")

        # pyrefly: ignore [missing-import]
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        # Map aspect ratio to DALL-E 3 standard sizes
        size = "1024x1024"
        if aspect_ratio == "16:9":
            size = "1792x1024"
        elif aspect_ratio in ["3:4", "9:16"]:
            size = "1024x1792"

        dalle_quality = "hd" if quality in ["HD", "Ultra"] else "standard"

        print(f"[OpenAI Provider] Requesting size: {size}, quality: {dalle_quality}", file=sys.stderr)
        
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size=size,
                quality=dalle_quality,
                response_format="b64_json"
            )
        except Exception as api_err:
            raise RuntimeError(f"OpenAI Images API call failed: {api_err}")

        # Explicit API response validation
        if response is None:
            raise RuntimeError("OpenAI Images API returned an empty/None response.")
        
        data_arr = getattr(response, "data", None)
        if data_arr is None or not isinstance(data_arr, list) or len(data_arr) == 0:
            raise RuntimeError("OpenAI Images API returned a response with missing or empty 'data' field.")
            
        first_item = data_arr[0]
        if first_item is None:
            raise RuntimeError("OpenAI Images API returned a None response data item.")
            
        b64_data = getattr(first_item, "b64_json", None)
        if b64_data:
            import base64
            try:
                decoded_bytes = base64.b64decode(b64_data)
            except Exception as dec_err:
                raise RuntimeError(f"Failed to decode base64 image data from OpenAI response: {dec_err}")
            
            try:
                return Image.open(io.BytesIO(decoded_bytes))
            except Exception as pil_err:
                raise RuntimeError(f"OpenAI returned invalid/corrupted binary image data: {pil_err}")
                
        # Try URL fallback if b64 is missing
        url_data = getattr(first_item, "url", None)
        if url_data:
            print(f"[OpenAI Provider] b64_json missing, attempting URL retrieve: {url_data}", file=sys.stderr)
            try:
                img_resp = requests.get(url_data, timeout=30)
                if img_resp.status_code == 200:
                    if not img_resp.content:
                        raise RuntimeError("OpenAI image URL returned empty content.")
                    return Image.open(io.BytesIO(img_resp.content))
                raise RuntimeError(f"Failed to retrieve image URL: HTTP {img_resp.status_code}")
            except Exception as url_err:
                raise RuntimeError(f"Failed to retrieve OpenAI image URL: {url_err}")
                
        raise RuntimeError("OpenAI Images API response item contains neither 'b64_json' nor 'url'.")


class GeminiProvider(BaseImageProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def provider_name(self) -> str:
        return "Google Imagen 3"

    def generate(self, prompt: str, aspect_ratio: str, negative_prompt: str, quality: str) -> Image.Image:
        if not self.is_available():
            raise ValueError("Gemini API key is missing or not configured.")

        # pyrefly: ignore [missing-import]
        from google import genai
        # pyrefly: ignore [missing-import]
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        
        gemini_ar = aspect_ratio
        if gemini_ar not in ["1:1", "3:4", "4:3", "9:16", "16:9"]:
            gemini_ar = "1:1"

        gemini_models = [
            "imagen-3.0-generate-002",
            "imagen-3.0-generate-001",
            "imagen-2.0-generate-001"
        ]

        last_error = None
        for model in gemini_models:
            try:
                print(f"[Gemini Provider] Trying model: {model}, Aspect ratio: {gemini_ar}", file=sys.stderr)
                result = client.models.generate_images(
                    model=model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/jpeg",
                        aspect_ratio=gemini_ar,
                    ),
                )
                
                # Hardened response validations
                if result is None:
                    raise RuntimeError(f"Gemini Imagen returned no response object for model {model}.")
                    
                generated_images = getattr(result, "generated_images", None)
                if generated_images is None:
                    raise RuntimeError(f"Gemini Imagen response has no 'generated_images' field.")
                    
                if not isinstance(generated_images, list) or len(generated_images) == 0:
                    raise RuntimeError(f"Gemini Imagen response 'generated_images' array is empty.")
                    
                first_item = generated_images[0]
                if first_item is None:
                    raise RuntimeError("Gemini Imagen first image item is None.")
                    
                image_obj = getattr(first_item, "image", None)
                if image_obj is None:
                    raise RuntimeError("Gemini Imagen image item has no 'image' field.")
                    
                image_bytes = getattr(image_obj, "image_bytes", None)
                if not image_bytes:
                    raise RuntimeError("Gemini Imagen image object has no binary image_bytes.")
                    
                try:
                    return Image.open(io.BytesIO(image_bytes))
                except Exception as pil_err:
                    raise RuntimeError(f"Gemini Imagen returned corrupted image bytes: {pil_err}")
            except Exception as e:
                last_error = e
                print(f"[Gemini Provider] Model {model} failed: {e}", file=sys.stderr)

        raise RuntimeError(f"Google Imagen service failed: {last_error or 'All models failed'}")


class HuggingFaceProvider(BaseImageProvider):
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")

    def is_available(self) -> bool:
        return bool(self.token)

    @property
    def provider_name(self) -> str:
        return "HuggingFace (FLUX / SDXL)"

    def generate(self, prompt: str, aspect_ratio: str, negative_prompt: str, quality: str) -> Image.Image:
        if not self.is_available():
            raise ValueError("Hugging Face Hub API Token is missing.")

        endpoints = [
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
        ]
        headers = {"Authorization": f"Bearer {self.token}"}

        last_error = None
        for url in endpoints:
            model_name = url.rsplit("/", 1)[-1]
            try:
                print(f"[HuggingFace Provider] Querying model: {model_name}", file=sys.stderr)
                payload = {"inputs": prompt}
                if "stable-diffusion" in url:
                    payload["parameters"] = {"negative_prompt": negative_prompt}

                resp = requests.post(url, headers=headers, json=payload, timeout=45)
                if resp is None:
                    raise RuntimeError("HuggingFace Inference API returned no response object.")
                    
                if resp.status_code == 200:
                    if not resp.content:
                        raise RuntimeError("HuggingFace Inference API returned empty binary content.")
                    try:
                        return Image.open(io.BytesIO(resp.content))
                    except Exception as pil_err:
                        raise RuntimeError(f"HuggingFace model response is not a valid PIL Image: {pil_err}")
                
                resp.raise_for_status()
            except Exception as e:
                last_error = e
                print(f"[HuggingFace Provider] {model_name} error: {e}", file=sys.stderr)

        raise RuntimeError(f"Hugging Face models failed: {last_error or 'All endpoints failed'}")


class PollinationsProvider(BaseImageProvider):
    def is_available(self) -> bool:
        return True  # Free fallback, always available

    @property
    def provider_name(self) -> str:
        return "Pollinations.ai (Flux Fallback)"

    def generate(self, prompt: str, aspect_ratio: str, negative_prompt: str, quality: str) -> Image.Image:
        import time
        encoded = urllib.parse.quote(prompt)

        w, h = 768, 768
        if aspect_ratio == "16:9":
            w, h = 1024, 576
        elif aspect_ratio in ["3:4", "9:16"]:
            w, h = 576, 768

        attempts = [
            (f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&nologo=true", "default"),
            (f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&nologo=true", "default-retry-1"),
            (f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&nologo=true", "default-retry-2"),
        ]

        last_error = None
        for idx, (url, model_lbl) in enumerate(attempts, 1):
            seed = int(datetime.datetime.now().timestamp() * 1000) % 999999
            sep = "&" if "?" in url else "?"
            full_url = f"{url}{sep}seed={seed}"

            print(f"[Pollinations Provider] Querying {model_lbl} (attempt {idx}/{len(attempts)})", file=sys.stderr)
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                resp = requests.get(full_url, headers=headers, timeout=30)
                if resp is None:
                    raise RuntimeError("Pollinations returned no response object.")
                    
                if resp.status_code == 200:
                    content_type = resp.headers.get("content-type", "")
                    if content_type is None or not content_type.startswith("image"):
                        raise RuntimeError(f"Pollinations returned non-image content type: {content_type}")
                    if not resp.content:
                        raise RuntimeError("Pollinations returned empty content body.")
                    try:
                        return Image.open(io.BytesIO(resp.content))
                    except Exception as pil_err:
                        raise RuntimeError(f"Pollinations content is not a valid PIL Image: {pil_err}")
                
                resp.raise_for_status()
            except Exception as e:
                last_error = e
                print(f"[Pollinations Provider] Attempt failed: {e}", file=sys.stderr)

            if idx < len(attempts):
                time.sleep(2)

        raise RuntimeError(f"Pollinations fallback failed: {last_error or 'All endpoints failed'}")


class StabilityAIProvider(BaseImageProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("STABILITY_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def provider_name(self) -> str:
        return "Stability AI"

    def generate(self, prompt: str, aspect_ratio: str, negative_prompt: str, quality: str) -> Image.Image:
        if not self.is_available():
            raise ValueError("Stability AI API key is missing or not configured.")

        width, height = 1024, 1024
        if aspect_ratio == "16:9":
            width, height = 1216, 832
        elif aspect_ratio in ["3:4", "9:16"]:
            width, height = 832, 1216

        import base64
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        body = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1.0
                }
            ],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": 30
        }
        if negative_prompt:
            body["text_prompts"].append({
                "text": negative_prompt,
                "weight": -1.0
            })

        print(f"[Stability AI Provider] Querying text-to-image API", file=sys.stderr)
        resp = requests.post(url, headers=headers, json=body, timeout=60)
        if resp is None:
            raise RuntimeError("Stability AI returned no response object.")
        if resp.status_code != 200:
            raise RuntimeError(f"Stability AI API error (HTTP {resp.status_code}): {resp.text}")
        
        data = resp.json()
        if not data.get("artifacts"):
            raise RuntimeError("Stability AI response lacks artifacts.")
        
        base64_str = data["artifacts"][0]["base64"]
        img_data = base64.b64decode(base64_str)
        try:
            return Image.open(io.BytesIO(img_data))
        except Exception as pil_err:
            raise RuntimeError(f"Stability AI content is not a valid PIL Image: {pil_err}")


class ReplicateProvider(BaseImageProvider):
    def __init__(self, api_token: str | None = None):
        self.api_token = api_token or os.environ.get("REPLICATE_API_TOKEN")

    def is_available(self) -> bool:
        return bool(self.api_token)

    @property
    def provider_name(self) -> str:
        return "Replicate"

    def generate(self, prompt: str, aspect_ratio: str, negative_prompt: str, quality: str) -> Image.Image:
        if not self.is_available():
            raise ValueError("Replicate API token is missing or not configured.")

        import time
        width, height = 1024, 1024
        if aspect_ratio == "16:9":
            width, height = 1280, 720
        elif aspect_ratio in ["3:4", "9:16"]:
            width, height = 768, 1024

        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
        
        body = {
            "version": "7762d3561c06b868a94587519299aac50f4b57a187190584b47c0300527cd952",
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt or "",
                "width": width,
                "height": height,
                "num_outputs": 1,
                "scheduler": "K_EULER",
                "guidance_scale": 7.5,
                "num_inference_steps": 25
            }
        }

        print("[Replicate Provider] Creating prediction task", file=sys.stderr)
        resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=body, timeout=30)
        if resp is None:
            raise RuntimeError("Replicate returned no response object.")
        if resp.status_code not in [200, 201]:
            raise RuntimeError(f"Replicate API error (HTTP {resp.status_code}): {resp.text}")

        prediction = resp.json()
        poll_url = prediction.get("urls", {}).get("get")
        if not poll_url:
            raise RuntimeError("Replicate response did not contain a poll URL.")

        print(f"[Replicate Provider] Polling prediction status...", file=sys.stderr)
        for attempt in range(20):
            poll_resp = requests.get(poll_url, headers=headers, timeout=15)
            if poll_resp is None or poll_resp.status_code != 200:
                raise RuntimeError(f"Replicate status poll failed (HTTP {poll_resp.status_code if poll_resp else 'None'})")
            
            poll_data = poll_resp.json()
            status = poll_data.get("status")
            if status == "succeeded":
                outputs = poll_data.get("output")
                if not outputs or not isinstance(outputs, list):
                    raise RuntimeError("Replicate output is empty or malformed.")
                img_url = outputs[0]
                print(f"[Replicate Provider] Downloading generated image from {img_url}", file=sys.stderr)
                img_resp = requests.get(img_url, timeout=30)
                if img_resp is None or img_resp.status_code != 200:
                    raise RuntimeError("Failed to download image from Replicate CDN.")
                return Image.open(io.BytesIO(img_resp.content))
            elif status == "failed":
                raise RuntimeError(f"Replicate prediction failed: {poll_data.get('error')}")
            elif status in ["canceled", "cancelled"]:
                raise RuntimeError("Replicate prediction task was canceled.")
            
            time.sleep(2)

        raise RuntimeError("Replicate prediction timed out after 40 seconds.")


class FalAIProvider(BaseImageProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def provider_name(self) -> str:
        return "Fal.ai"

    def generate(self, prompt: str, aspect_ratio: str, negative_prompt: str, quality: str) -> Image.Image:
        if not self.is_available():
            raise ValueError("Fal.ai API key is missing or not configured.")

        image_size = "square_hd"
        if aspect_ratio == "16:9":
            image_size = "landscape_hd"
        elif aspect_ratio in ["3:4", "9:16"]:
            image_size = "portrait_hd"

        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "prompt": prompt,
            "image_size": image_size,
            "num_inference_steps": 4,
            "enable_safety_checker": True,
            "sync_mode": True
        }

        print("[Fal.ai Provider] Querying Flux Schnell sync API", file=sys.stderr)
        resp = requests.post("https://fal.run/fal-ai/flux/schnell", headers=headers, json=body, timeout=40)
        if resp is None:
            raise RuntimeError("Fal.ai returned no response object.")
        if resp.status_code != 200:
            raise RuntimeError(f"Fal.ai API error (HTTP {resp.status_code}): {resp.text}")

        data = resp.json()
        images = data.get("images")
        if not images or not isinstance(images, list):
            raise RuntimeError("Fal.ai response lacks images array.")
        
        img_url = images[0].get("url")
        if not img_url:
            raise RuntimeError("Fal.ai response image URL is missing.")

        print(f"[Fal.ai Provider] Downloading image from {img_url}", file=sys.stderr)
        img_resp = requests.get(img_url, timeout=30)
        if img_resp is None or img_resp.status_code != 200:
            raise RuntimeError("Failed to download image from Fal.ai CDN.")
        return Image.open(io.BytesIO(img_resp.content))
