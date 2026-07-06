with open("app_clean_perfect.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for idx in range(280, 305):
    if idx < len(lines):
        line_repr = repr(lines[idx])
        print(f"{idx+1}: {line_repr.encode('ascii', 'replace').decode('ascii')}")
