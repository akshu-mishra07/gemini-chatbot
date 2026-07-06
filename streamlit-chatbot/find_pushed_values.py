import sys

sys.stdout.reconfigure(encoding='utf-8')
dis_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\dis.txt"

def print_before():
    with open(dis_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for idx, line in enumerate(lines):
        if "STORE_NAME             143 (status_colors)" in line:
            # Print 20 lines before it
            for i in range(max(0, idx - 25), idx + 2):
                print(f"{i}: {lines[i].strip()}")
            return

if __name__ == "__main__":
    print_before()
