import os
import sys
import hashlib
import time
from PIL import Image

sys.path.append(os.path.abspath('.'))
import image_generator

prompts = [
    "create a sunrise image",
    "create a scenery image",
    "draw a cat",
    "generate a logo"
]

print("Starting end-to-end verification of image generator...")
print(f"Will test {len(prompts)} prompts with 10s delay between each.\n")
results = {}

for i, prompt in enumerate(prompts):
    if i > 0:
        print(f"\nSleeping 10 seconds before next prompt...")
        time.sleep(10)
        
    print(f"\n[{i+1}/{len(prompts)}] Generating image for: '{prompt}'...")
    try:
        img = image_generator.generate_image(prompt)
        filepath = image_generator.save_generated_image(img, prompt)
        
        assert isinstance(img, Image.Image), "Result is not a PIL Image"
        assert os.path.exists(filepath), f"File {filepath} was not saved"
        
        with open(filepath, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            
        results[prompt] = {
            "path": filepath,
            "size": img.size,
            "hash": file_hash
        }
        print(f"SUCCESS! File: {filepath}, Size: {img.size}, Hash: {file_hash[:16]}")
    except Exception as e:
        print(f"FAILED for '{prompt}': {e}")
        sys.exit(1)

# Check uniqueness
hashes = [info["hash"] for info in results.values()]
if len(hashes) != len(set(hashes)):
    print("\nERROR: Some generated images are identical!")
    sys.exit(1)

print(f"\n{'='*60}")
print(f"ALL {len(prompts)} IMAGES GENERATED SUCCESSFULLY!")
print(f"All images are distinct (unique hashes confirmed).")
print(f"{'='*60}")
for prompt, info in results.items():
    print(f"  '{prompt}' -> {info['path']} ({info['size']})")
