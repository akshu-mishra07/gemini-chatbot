import os
import json

messages_dir = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\messages"
files = [f for f in os.listdir(messages_dir) if f.endswith('.json')]
print(f"Total JSON files: {len(files)}")

for f_name in files:
    path = os.path.join(messages_dir, f_name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            text = json.dumps(data)
            if "Total Lines: 2311" in text:
                print(f"Found file with app.py contents: {f_name}, length: {len(text)}")
                # Print a slice of the text
                print(text[:2000])
                break
    except Exception as e:
         pass
