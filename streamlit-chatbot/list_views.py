import json
import re
import os

def main():
    transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"
    if not os.path.exists(transcript_path):
        print("Transcript not found")
        return
        
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
            except Exception:
                continue
                
            if data.get("type") != "VIEW_FILE":
                continue
                
            content = data.get("content", "")
            if "app.py" not in content.lower():
                continue
                
            # Parse showing line ranges
            # Example: "Showing lines 1 to 800"
            m = re.search(r"Showing lines (\d+) to (\d+)", content)
            line_range = f"lines {m.group(1)}-{m.group(2)}" if m else "unknown range"
            
            # Find file path
            m_path = re.search(r"File Path: `file:///([^`]+)`", content)
            path = m_path.group(1) if m_path else "unknown path"
            
            print(f"Step {data.get('step_index')}: path={os.path.basename(path)}, range={line_range}, length={len(content)}")

if __name__ == "__main__":
    main()
