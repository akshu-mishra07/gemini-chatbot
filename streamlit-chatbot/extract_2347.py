import json
import os
import re

real_transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"

def extract_2347():
    # Map from line_num -> {step_idx: line_val}
    lines_map = {}
    
    with open(real_transcript_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                data = json.loads(line)
            except Exception:
                continue
                
            if data.get("type") != "VIEW_FILE":
                continue
                
            content = data.get("content", "")
            if not content:
                continue
                
            if "app.py" not in content.lower():
                continue
                
            # Search for Total Lines header
            m = re.search(r"Total Lines:\s*(\d+)", content)
            if not m:
                continue
                
            total_lines = int(m.group(1))
            # We ONLY want views from versions that are 2347 lines
            if total_lines != 2347:
                continue
                
            step_idx = data.get("step_index", 0)
            sub_lines = content.splitlines()
            for sl in sub_lines:
                lm = re.match(r"^(\d+): (.*)$", sl)
                if lm:
                    line_num = int(lm.group(1))
                    line_val = lm.group(2)
                    if line_val.endswith("\r"):
                        line_val = line_val[:-1]
                        
                    # Save the line value, keeping the latest step's version
                    if line_num not in lines_map or step_idx >= lines_map[line_num][1]:
                        lines_map[line_num] = (line_val, step_idx)

    if not lines_map:
        print("No lines found!")
        return

    max_line = max(lines_map.keys())
    print(f"Max line number: {max_line}")
    print(f"Total lines found: {len(lines_map)} / 2347")
    
    missing = []
    reconstructed = []
    for i in range(1, 2348):
        if i in lines_map:
            reconstructed.append(lines_map[i][0])
        else:
            missing.append(i)
            reconstructed.append(f"# MISSING LINE {i}")
            
    print(f"Missing lines count: {len(missing)}")
    if missing:
        print(f"Missing ranges: {missing[:50]}")
        
    out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app_clean_reconstructed_v3.py"
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(reconstructed))
    print(f"Wrote 2347 reconstruction to {out_path}")

if __name__ == "__main__":
    extract_2347()
