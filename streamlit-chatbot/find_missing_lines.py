with open("app_clean_perfect.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

missing = []
for idx, line in enumerate(lines):
    if "# MISSING LINE" in line or "MISSING LINE" in line:
        missing.append(idx + 1)

print(f"Total missing lines in app_clean_perfect.py: {len(missing)}")
if missing:
    # Group into ranges
    ranges = []
    start = missing[0]
    prev = missing[0]
    for m in missing[1:]:
        if m == prev + 1:
            prev = m
        else:
            ranges.append((start, prev))
            start = m
            prev = m
    ranges.append((start, prev))
    print("Ranges of missing lines:")
    for r in ranges:
        print(f"Lines {r[0]} to {r[1]} (Count: {r[1] - r[0] + 1})")
