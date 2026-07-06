import sys
import traceback

def check(file_path):
    print(f"Checking {file_path}...")
    try:
        content = open(file_path, "r", encoding="utf-8").read()
        compile(content, file_path, "exec")
        print("Success! No syntax errors.")
    except SyntaxError as e:
        print(f"SyntaxError in {file_path}:")
        print(f"  Line: {e.lineno}")
        print(f"  Col: {e.offset}")
        print(f"  Text: {repr(e.text)}")
        print(f"  Message: {e.msg}")
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check(sys.argv[1])
    else:
        print("Provide a file path")
