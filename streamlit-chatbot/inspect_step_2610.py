import json
import os

transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"

def inspect_view():
    with open(transcript_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                data = json.loads(line)
            except Exception:
                continue
            if data.get("step_index") == 2610:
                content = data.get("content", "")
                print(f"Step 2610 Content Length: {len(content)}")
                # Write content to a file to inspect it
                out_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\scratch\step_2610_view.txt"
                with open(out_path, "w", encoding="utf-8") as out_f:
                    out_f.write(content)
                print("Wrote view content to step_2610_view.txt")
                # Print first 500 characters
                print("Content start:", repr(content[:500]))

if __name__ == "__main__":
    inspect_view()
