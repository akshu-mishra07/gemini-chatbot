import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
dis_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\dis.txt"

def inspect():
    current_line = None
    lines = []
    
    with open(dis_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            m = re.match(r"^\s*(\d+)\s+(.*)$", line)
            if m:
                current_line = int(m.group(1))
            if current_line is not None and 1495 <= current_line <= 1530:
                lines.append(line.strip())
                
    for l in lines[:100]:
        print(l)

if __name__ == "__main__":
    inspect()
