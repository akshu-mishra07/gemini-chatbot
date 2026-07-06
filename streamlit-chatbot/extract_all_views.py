import json
import os
import re

def extract():
    transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"
    if not os.path.exists(transcript_path):
        print("Transcript not found")
        return
        
    lines_map = {}
    
    # Read the transcript line-by-line
    with open(transcript_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                data = json.loads(line)
            except Exception:
                continue
                
            step_idx = data.get("step_index", 0)
            
            # We want to ignore views after the scrambling occurred.
            # Scrambling started when bad replacements were written. Step 2743 is a write_to_file,
            # and after that, the views of app.py are scrambled. So we only parse views before step 2740.
            if step_idx >= 2740:
                continue
                
            # Check if it's a VIEW_FILE output
            # Usually, view_file output is in a message with source = SYSTEM or similar,
            # containing "File Path: `file:///c:/users/acer/onedrive/desktop/gemini-chatbot/streamlit-chatbot/app.py`"
            content = data.get("content", "")
            if not content:
                continue
                
            if not re.search(r"File Path:\s*`file:///c:/users/acer/onedrive/desktop/gemini-chatbot/streamlit-chatbot/app.py`", content, re.IGNORECASE):
                continue
                
            # Parse lines of the view content
            # Each line looks like "LineNumber: LineContent"
            sub_lines = content.splitlines()
            count = 0
            for sl in sub_lines:
                # Match "123: text"
                m = re.match(r"^(\d+): (.*)$", sl)
                if m:
                    line_num = int(m.group(1))
                    line_val = m.group(2)
                    if line_val.endswith("\r"):
                        line_val = line_val[:-1]
                        
                    # We store it. In case of multiple views, we prefer the one from the largest step_idx
                    # before 2740, because it will contain the most up-to-date edits made by the agent
                    # that were correct.
                    if line_num not in lines_map or step_idx >= lines_map[line_num][1]:
                        lines_map[line_num] = (line_val, step_idx)
                        count += 1
            # print(f"Step {step_idx}: parsed {count} lines")
            
    if not lines_map:
        print("No lines found!")
        return
        
    max_line = max(lines_map.keys())
    print(f"Max line index: {max_line}")
    print(f"Total distinct lines recovered: {len(lines_map)} / {max_line}")
    
    missing = []
    for i in range(1, max_line + 1):
        if i not in lines_map:
            missing.append(i)
            
    print(f"Number of missing lines: {len(missing)}")
    if missing:
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
        print(f"Missing ranges: {ranges}")
        
    # Let's write the reconstructed lines
    reconstructed = []
    for i in range(1, max_line + 1):
        if i in lines_map:
            reconstructed.append(lines_map[i][0])
        else:
            reconstructed.append(f"# MISSING LINE {i}")
            
    out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app_clean_reconstructed_v3.py"
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(reconstructed))
    print(f"Wrote reconstruction to {out_path}")

if __name__ == "__main__":
    extract()
