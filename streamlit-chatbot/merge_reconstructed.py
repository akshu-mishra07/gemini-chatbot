import json
import os
import re

real_transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"
base_file = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app_clean_reconstructed_v2.py"

def merge():
    # Load base lines
    with open(base_file, "r", encoding="utf-8") as f:
        base_lines = [line.rstrip("\r\n") for line in f]
        
    print(f"Base file has {len(base_lines)} lines.")
    
    # Scan all transcript views
    db = {} # total_lines -> line_num -> content
    
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
                
            m = re.search(r"Total Lines:\s*(\d+)", content)
            if not m:
                continue
            total_lines = int(m.group(1))
            step_idx = data.get("step_index", 0)
            
            # Allow all close versions
            if total_lines not in [2311, 2315, 2324, 2330, 2339, 2345, 2347]:
                continue
                
            if total_lines not in db:
                db[total_lines] = {}
                
            sub_lines = content.splitlines()
            for sl in sub_lines:
                lm = re.match(r"^(\d+): (.*)$", sl)
                if lm:
                    line_num = int(lm.group(1))
                    line_val = lm.group(2)
                    if line_val.endswith("\r"):
                        line_val = line_val[:-1]
                        
                    # Filter scrambled lines
                    if 215 <= line_num <= 275:
                        if any(x in line_val for x in ["!important", "/*", "*/", "margin:", "overflow:", "white-space:", "background-color:"]):
                            continue
                            
                    if line_num not in db[total_lines] or step_idx >= db[total_lines][line_num][1]:
                        db[total_lines][line_num] = (line_val, step_idx)

    # Now try to merge and fill missing lines
    merged_lines = []
    filled_count = 0
    versions_to_try = [2347, 2345, 2339, 2330, 2324, 2315, 2311]
    
    for i in range(1, len(base_lines) + 1):
        original = base_lines[i-1]
        
        # Check if line is missing or scrambled
        is_missing = original.startswith("# MISSING LINE")
        is_scrambled_greetings = (229 <= i <= 256) and any(x in original for x in ["!important", "/*", "*/", "margin:"])
        
        if is_missing or is_scrambled_greetings:
            # Try to find a value from database
            found = False
            for v in versions_to_try:
                if v in db and i in db[v]:
                    merged_lines.append(db[v][i][0])
                    filled_count += 1
                    found = True
                    break
            if not found:
                merged_lines.append(original)
        else:
            merged_lines.append(original)
            
    print(f"Filled {filled_count} missing/scrambled lines.")
    
    # Count how many missing lines remain
    still_missing = [idx+1 for idx, l in enumerate(merged_lines) if l.startswith("# MISSING LINE")]
    print(f"Still missing lines count: {len(still_missing)}")
    if still_missing:
        print(f"Still missing ranges: {still_missing[:50]}")
        
    out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app_merged.py"
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(merged_lines))
    print(f"Wrote merged file to {out_path}")

if __name__ == "__main__":
    merge()
