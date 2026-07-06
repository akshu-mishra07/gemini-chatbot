import re

dis_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\dis.txt"

def scan():
    line_nums = set()
    with open(dis_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\s*(\d+)\s+(.*)$", line)
            if m:
                line_nums.add(int(m.group(1)))
                
    print(f"Total distinct source line numbers in dis.txt: {len(line_nums)}")
    print(f"Min line: {min(line_nums)}, Max line: {max(line_nums)}")
    # Find missing numbers in the sequence from min to max
    missing = []
    for i in range(min(line_nums), max(line_nums) + 1):
        if i not in line_nums:
            missing.append(i)
    print(f"Missing source lines count: {len(missing)}")
    if missing:
        print(f"First 50 missing: {missing[:50]}")

if __name__ == "__main__":
    scan()
