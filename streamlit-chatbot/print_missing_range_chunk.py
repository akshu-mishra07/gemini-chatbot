import sys

sys.stdout.reconfigure(encoding='utf-8')
dis_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\missing_disassembly.txt"

def print_chunk():
    with open(dis_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    start_str = "RANGE: 1959 to 2017"
    idx = content.find(start_str)
    if idx == -1:
        print("Not found")
        return
        
    next_idx = content.find("RANGE: ", idx + len(start_str))
    if next_idx == -1:
        print(content[idx:])
    else:
        print(content[idx:next_idx])

if __name__ == "__main__":
    print_chunk()
