import re

dis_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\dis.txt"
with open(dis_path, "r", encoding="utf-8") as f:
    content = f.read()

matches = re.findall(r"Disassembly of <code object (\w+)", content)
for m in set(matches):
    if "image" in m.lower():
        print(m)
