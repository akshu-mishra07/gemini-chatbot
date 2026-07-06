import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
dis_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\dis.txt"

def print_lines():
    with open(dis_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    current_line = None
    for line in lines:
        m = re.match(r"^\s*(\d+)\s+(.*)$", line)
        if m:
            current_line = int(m.group(1))
        if current_line is not None and 1508 <= current_line <= 1514:
            print(line.strip())

if __name__ == "__main__":
    print_lines()
