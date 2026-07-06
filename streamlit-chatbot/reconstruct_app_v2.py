import json
import os
import sys

def restore():
    messages_dir = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\messages"
    if not os.path.exists(messages_dir):
        print("Messages directory not found:", messages_dir)
        return

    lines_map = {}
    
    files = [f for f in os.listdir(messages_dir) if f.endswith('.json')]
    print("Found", len(files), "JSON files in messages directory.")
    
    for filename in files:
        filepath = os.path.join(messages_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                content = str(data)
                if "app.py" in content and ":" in content:
                    for line in content.split("\\n"):
                        # Match strings like "123: text"
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            num_str = "".join(c for c in parts[0] if c.isdigit())
                            if num_str:
                                try:
                                    num = int(num_str)
                                    # Limit the parsed line numbers to the valid range [1, 3000]
                                    if 1 <= num <= 3000:
                                        val = parts[1]
                                        if val.startswith(" "):
                                            val = val[1:]
                                        # strip trailing quote/backslash characters
                                        if val.endswith("'") or val.endswith('"'):
                                            val = val[:-1]
                                        
                                        # Only save if we don't already have it or if the new one is longer
                                        if num not in lines_map or len(val) > len(lines_map[num]):
                                            lines_map[num] = val
                                except ValueError:
                                    pass
        except Exception as e:
            pass

    if not lines_map:
        print("No lines reconstructed from messages JSON files.")
        return

    print("Reconstructed total lines:", len(lines_map))
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
