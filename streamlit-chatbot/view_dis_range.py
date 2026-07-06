with open("../missing_disassembly.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

found = False
for idx, line in enumerate(lines):
    if "RANGE: 2051 to 2277" in line:
        found = True
        print(f"Found on line {idx + 1}:")
        for i in range(max(0, idx - 2), min(len(lines), idx + 30)):
            print(f"{i+1}: {repr(lines[i])}")
        break

if not found:
    print("Not found")
