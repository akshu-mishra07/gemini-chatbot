import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
real_transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"

def view_step():
    with open(real_transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
            except Exception:
                continue
            if data.get("step_index") == 2443:
                print("Found step 2443")
                print(data.get("content"))
                return

if __name__ == "__main__":
    view_step()
