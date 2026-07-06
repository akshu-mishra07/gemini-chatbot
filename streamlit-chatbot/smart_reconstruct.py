import json
import os
import re

transcript_path = r"C:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\reconstruct_from_clean_views.py" # just a reference Cwd
real_transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"

def smart_reconstruct():
    # Map from line_num -> {step_idx: line_val}
    line_versions = {}
    
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
                
            step_idx = data.get("step_index", 0)
            sub_lines = content.splitlines()
            
            for sl in sub_lines:
                m = re.match(r"^(\d+): (.*)$", sl)
                if m:
                    line_num = int(m.group(1))
                    line_val = m.group(2)
                    if line_val.endswith("\r"):
                        line_val = line_val[:-1]
                        
                    if line_num not in line_versions:
                        line_versions[line_num] = {}
                    line_versions[line_num][step_idx] = line_val

    if not line_versions:
        print("No lines found!")
        return

    max_line = max(line_versions.keys())
    print(f"Max line index: {max_line}")
    print(f"Total distinct lines with any version: {len(line_versions)}")

    # Let's inspect line versions around the scrambled area: 220 to 280
    print("\n--- VERSION HISTORY FOR LINES 228-235 ---")
    for ln in range(228, 236):
        if ln in line_versions:
            print(f"Line {ln}:")
            for step in sorted(line_versions[ln].keys()):
                print(f"  Step {step}: {repr(line_versions[ln][step])}")
        else:
            print(f"Line {ln}: MISSING")

    # Let's write out the latest version for each line, but let's see which lines are still missing.
    missing = []
    reconstructed = []
    for i in range(1, max_line + 1):
        if i in line_versions:
            # Get the best version
            steps = sorted(line_versions[i].keys())
            # For lines in the greetings/CSS scramble range (229-257), let's see which step is clean.
            # Step 2600/2608/2610/2618 might have scrambling. Let's see.
            best_step = steps[-1] # default to latest
            
            # If it's in the greetings range, let's prefer steps < 2600 if available
            if 229 <= i <= 257:
                clean_steps = [s for s in steps if s < 2600]
                if clean_steps:
                    best_step = clean_steps[-1]
            
            reconstructed.append(line_versions[i][best_step])
        else:
            missing.append(i)
            reconstructed.append(f"# MISSING LINE {i}")

    print(f"\nMissing lines count: {len(missing)}")
    if missing:
        print(f"Missing ranges: {missing[:50]}")

    out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app_smart_reconstructed.py"
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(reconstructed))
    print(f"Wrote smart reconstruction to {out_path}")

if __name__ == "__main__":
    smart_reconstruct()
