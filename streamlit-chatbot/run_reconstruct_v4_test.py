import json
import os
import re
import py_compile

def restore_test():
    transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"
    if not os.path.exists(transcript_path):
        print("Transcript file not found:", transcript_path)
        return

    lines_map = {}
    print("Parsing transcript JSON lines...")
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            try:
                data = json.loads(line)
                
                # Check all string values in the JSON object recursively
                def check_val(val):
                    if isinstance(val, str):
                        if "app.py" in val and ":" in val:
                            parse_raw_text(val, lines_map)
                    elif isinstance(val, dict):
                        for k, v in val.items():
                            check_val(v)
                    elif isinstance(val, list):
                        for item in val:
                            check_val(item)
                            
                check_val(data)
            except Exception as e:
                pass

    if not lines_map:
        print("No lines reconstructed.")
        return

    # Filter keys to be <= 2315
    valid_keys = [k for k in lines_map.keys() if k <= 2315]
    if not valid_keys:
        print("No lines found under 2315.")
        return
        
    print("Reconstructed total distinct lines:", len(valid_keys))
    max_line = max(valid_keys)
    print("Max line index:", max_line)

    restored_content = []
    missing_lines = []
    for i in range(1, max_line + 1):
        if i in lines_map:
            restored_content.append(lines_map[i])
        else:
            missing_lines.append(i)
            restored_content.append(f"# MISSING LINE {i}")

    print("Number of missing lines:", len(missing_lines))
    
    out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app_test_v4.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(restored_content))
    print("Wrote to:", out_path)
    
    try:
        py_compile.compile(out_path, doraise=True)
        print("Compilation SUCCESSFUL!")
    except Exception as e:
        print("Compilation FAILED:", str(e))

def parse_raw_text(text, lines_map):
    lines = text.split("\n")
    for line in lines:
        match = re.match(r'^\s*(\d+)\s*:\s*(.*)$', line)
        if match:
            num = int(match.group(1))
            content = match.group(2)
            if content.endswith("\r"):
                content = content[:-1]
            # ONLY store if it doesn't look like markdown notes or log comments
            # To avoid scrambling, let's look for known scrambled patterns
            if num not in lines_map or len(content) > len(lines_map[num]):
                lines_map[num] = content

if __name__ == "__main__":
    restore_test()
