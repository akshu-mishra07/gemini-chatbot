import json
import os
import sys

def restore():
    transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"
    if not os.path.exists(transcript_path):
        print("Transcript file not found:", transcript_path)
        return

    lines_map = {}
    total_parsed_lines = 0

    print("Reading transcript file...")
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f):
            try:
                data = json.loads(line)
                # Search recursively or directly in content
                content_str = str(data)
                if "app.py" in content_str and ":" in content_str:
                    # Let's split by newline and parse line-by-line
                    for sub_line in content_str.split("\\n"):
                        # Match like "123: text"
                        parts = sub_line.split(":", 1)
                        if len(parts) == 2:
                            num_str = "".join(c for c in parts[0] if c.isdigit())
                            if num_str:
                                try:
                                    num = int(num_str)
                                    if 1 <= num <= 3000:
                                        val = parts[1]
                                        if val.startswith(" "):
                                            val = val[1:]
                                        # strip trailing quotes/backslashes if any
                                        if val.endswith("'") or val.endswith('"'):
                                            val = val[:-1]
                                        if val.endswith("\\r"):
                                            val = val[:-2]
                                            
                                        # Save or keep the longest/most complete content
                                        if num not in lines_map or len(val) > len(lines_map[num]):
                                            lines_map[num] = val
                                            total_parsed_lines += 1
                                except ValueError:
                                    pass
            except Exception as e:
                pass

    if not lines_map:
        print("No lines reconstructed from transcript.")
        return

    print("Reconstructed total distinct lines:", len(lines_map))
    max_line = max(lines_map.keys())
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
    if len(missing_lines) > 0:
        print("First 20 missing lines:", missing_lines[:20])
        
    out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(restored_content))
    print("Wrote reconstructed app.py to:", out_path)

if __name__ == "__main__":
    restore()
