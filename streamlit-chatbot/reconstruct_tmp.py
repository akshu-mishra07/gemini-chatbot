import json
import os
import re

def restore():
    transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"
    if not os.path.exists(transcript_path):
        print("Transcript file not found:", transcript_path)
        return

    lines_map = {}
    print("Parsing transcript JSON lines...")
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                content = str(data)
                
                # Split by newline
                for sub_line in re.split(r'\n|\\n|\\\\n', content):
                    match = re.match(r'^\s*\\*["\'\[\s]*(\d+)\s*:\s*(.*)$', sub_line)
                    if match:
                        num = int(match.group(1))
                        val = match.group(2)
                        if 1 <= num <= 2450:
                            # Clean up trailing escapes
                            val = val.rstrip()
                            if val.endswith('\\r') or val.endswith('\r'):
                                val = val[:-2] if val.endswith('\\r') else val[:-1]
                            val = val.rstrip()
                            if len(val) >= 2 and ((val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'"))):
                                val = val[1:-1]
                            if val.endswith('\\'):
                                val = val[:-1]
                            
                            if num not in lines_map or len(val) > len(lines_map[num]):
                                lines_map[num] = val
            except Exception as e:
                pass

    if not lines_map:
        print("No lines reconstructed.")
        return
        
    max_line = max(lines_map.keys())
    print("Max line index:", max_line)
    
    restored_content = []
    missing = []
    for i in range(1, max_line + 1):
        if i in lines_map:
            restored_content.append(lines_map[i])
        else:
            missing.append(i)
            restored_content.append(f"# MISSING LINE {i}")
            
    # Group missing lines
    if missing:
        ranges = []
        start = missing[0]
        prev = missing[0]
        for m in missing[1:]:
            if m == prev + 1:
                prev = m
            else:
                ranges.append((start, prev))
                start = m
                prev = m
        ranges.append((start, prev))
        print("Missing line ranges:")
        for r in ranges:
            print(f"Lines {r[0]} to {r[1]} (Count: {r[1] - r[0] + 1})")
            
    out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app_reconstructed.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(restored_content))
    print("Wrote to:", out_path)

if __name__ == "__main__":
    restore()
