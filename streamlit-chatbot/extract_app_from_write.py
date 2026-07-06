import json
import os

def extract():
    transcript_path = r"C:\Users\ACER\.gemini\antigravity-ide\brain\0581bd1e-0418-42b8-9427-2ceef83cb7ef\.system_generated\logs\transcript.jsonl"
    if not os.path.exists(transcript_path):
        print("Transcript file not found:", transcript_path)
        return

    best_code = ""
    best_len = 0

    print("Reading transcript to search for app.py writes...")
    with open(transcript_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                data = json.loads(line)
                
                # Check tool_calls in model responses
                # or checks of arguments
                # We can do a string search for tool_calls or search key-values
                if "tool_calls" in data:
                    for tc in data["tool_calls"]:
                        if tc.get("name") in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
                            args = tc.get("args", {})
                            if "app.py" in str(args.get("TargetFile", "")):
                                # Check if it is a write_to_file with full contents
                                code = args.get("CodeContent", "")
                                if not code:
                                    # check if it's in other fields
                                    code = args.get("ReplacementContent", "")
                                if len(code) > best_len:
                                    best_len = len(code)
                                    best_code = code
                                    print(f"Line {idx}: Found write for app.py, length: {len(code)}")
                
                # Also check in system-generated step logs if they have tool calls
                if "content" in data and "write_to_file" in data["content"] and "app.py" in data["content"]:
                    # Try to find JSON-like block in content
                    # But the dictionary key check is cleaner
                    pass
            except Exception as e:
                pass

    if best_code:
        print(f"Extracted best app.py code of length: {len(best_code)}")
        out_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app.py"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(best_code)
        print("Wrote extracted app.py to:", out_path)
    else:
        print("No app.py write found in transcript.")

if __name__ == "__main__":
    extract()
