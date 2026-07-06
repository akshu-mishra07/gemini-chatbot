import json
import os
import re

def main():
    transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"
    if not os.path.exists(transcript_path):
        print("Transcript not found")
        return

    lines_map = {}
    print("Reading transcript...")
    
    with open(transcript_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                data = json.loads(line)
            except Exception as e:
                continue
            
            if data.get("type") != "VIEW_FILE":
                continue
            
            content = data.get("content", "")
            if not content:
                continue
                
            # STRICT file path check
            if "file:///c:/users/acer/onedrive/desktop/gemini-chatbot/streamlit-chatbot/app.py" not in content.lower():
                continue
                
            # Process lines
            sub_lines = content.splitlines()
            for sl in sub_lines:
                # Matches line number format: "123: line content"
                m = re.match(r"^(\d+): (.*)$", sl)
                if m:
                    line_num = int(m.group(1))
                    line_val = m.group(2)
                    
                    if line_val.endswith("\r"):
                        line_val = line_val[:-1]
                        
                    if line_num not in lines_map or data.get("step_index", 0) >= lines_map[line_num][1]:
                        lines_map[line_num] = (line_val, data.get("step_index", 0))

    if not lines_map:
        print("No app.py lines found!")
        return

    max_line = max(lines_map.keys())
    print(f"Max line number: {max_line}")
    print(f"Total lines found: {len(lines_map)}")
    
    reconstructed = []
    missing_ranges = []
    current_missing_start = None
    
    for i in range(1, max_line + 1):
        if i in lines_map:
            if current_missing_start is not None:
                missing_ranges.append((current_missing_start, i - 1))
                current_missing_start = None
            reconstructed.append(lines_map[i][0])
        else:
            if current_missing_start is None:
                current_missing_start = i
            reconstructed.append(f"# MISSING LINE {i}")
            
    if current_missing_start is not None:
        missing_ranges.append((current_missing_start, max_line))
        
    print(f"Missing lines: {missing_ranges}")
    
    out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app_clean_reconstructed.py"
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(reconstructed))
    print(f"Wrote reconstructed file to {out_path}")

if __name__ == "__main__":
    main()
