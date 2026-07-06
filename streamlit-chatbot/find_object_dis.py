import sys

sys.stdout.reconfigure(encoding='utf-8')
dis_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\dis.txt"

def find_dis():
    with open(dis_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    start_str = "Disassembly of <code object query_local_fallback_assistant"
    idx = content.find(start_str)
    if idx == -1:
        print("Not found")
        return
        
    next_idx = content.find("Disassembly of ", idx + len(start_str))
    if next_idx == -1:
        print(content[idx:])
    else:
        print(content[idx:next_idx])

if __name__ == "__main__":
    find_dis()
