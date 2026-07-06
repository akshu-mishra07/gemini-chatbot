import json
import os
import re

def restore():
    lines_map = {}
    
    # 1. Search messages directory
    messages_dir = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\messages"
    if os.path.exists(messages_dir):
        files = [f for f in os.listdir(messages_dir) if f.endswith('.json')]
        for filename in files:
            filepath = os.path.join(messages_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    content = str(data)
                    parse_text(content, lines_map)
            except Exception:
                pass

    # 2. Search transcript
    transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"
    if os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                parse_text(line, lines_map)

    if not lines_map:
        print("No lines reconstructed.")
        return

    print("Reconstructed total distinct lines:", len(lines_map))
    # We know app.py is around 2311 lines. Let's find the max line under 2320.
    valid_lines = [k for k in lines_map.keys() if k <= 2315]
    if not valid_lines:
        print("No valid lines under 2315.")
        return
        
    max_line = max(valid_lines)
    print("Max valid line index:", max_line)

    restored_content = []
    missing_lines = []
    for i in range(1, max_line + 1):
        if i in lines_map:
            restored_content.append(lines_map[i])
        else:
            missing_lines.append(i)
            restored_content.append(f"# MISSING LINE {i}")

    print("Number of missing lines:", len(missing_lines))
    if len(missing_lines) > 0:
        print("First 20 missing lines:", missing_lines[:20])
        
    out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(restored_content))
    print("Wrote reconstructed app.py to:", out_path)

def parse_text(text, lines_map):
    # Split by actual newline, escaped newline, and double-escaped newline
    lines = re.split(r'\n|\\n|\\\\n', text)
    for line in lines:
        # Match pattern: optional quotes/brackets/spaces, then digits, then colon, then space, then content
        match = re.match(r'^\s*\\*["\'\[]*(\d+)\s*:\s*(.*)$', line)
        if match:
            try:
                num = int(match.group(1))
                if 1 <= num <= 2315:
                    content = match.group(2)
                    # Clean up trailing escaped characters
                    content = clean_val(content)
                    # Save or keep the longer version
                    if num not in lines_map or len(content) > len(lines_map[num]):
                        lines_map[num] = content
            except ValueError:
                pass

def clean_val(val):
    # Remove trailing quotes, backslashes, and carriage returns
    val = val.rstrip()
    if val.endswith('\\r') or val.endswith('\r'):
        val = val[:-2] if val.endswith('\\r') else val[:-1]
    val = val.rstrip()
    if len(val) >= 2 and ((val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'"))):
        val = val[1:-1]
    if val.endswith('\\') or val.endswith('/'):
        val = val[:-1]
    return val

if __name__ == "__main__":
    restore()
