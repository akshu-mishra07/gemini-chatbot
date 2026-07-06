import json
import os
import re

real_transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"

def scan_all():
    # structure: db[total_lines][line_num] = (content, step_idx)
    db = {}
    
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
                        
                    # Save the latest step's version for this total_lines
                    if line_num not in db[total_lines] or step_idx >= db[total_lines][line_num][1]:
                        db[total_lines][line_num] = (line_val, step_idx)
                        
    print("Found total lines versions:")
    for tl in sorted(db.keys()):
        print(f"  Version with {tl} lines: recovered {len(db[tl])} distinct lines")
        # Let's find missing ranges for this version
        missing = []
        for i in range(1, tl + 1):
            if i not in db[tl]:
                missing.append(i)
        print(f"    Missing count: {len(missing)}")
        if missing:
            # group missing into ranges
            ranges = []
            start = None
            for m_ln in missing:
                if start is None:
                    start = m_ln
                elif m_ln != missing[missing.index(m_ln)-1] + 1:
                    ranges.append((start, missing[missing.index(m_ln)-1]))
                    start = m_ln
            if start is not None:
                ranges.append((start, missing[-1]))
            print(f"    Missing ranges: {ranges}")

if __name__ == "__main__":
    scan_all()
