import os

def print_missing():
    path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\app_clean_reconstructed_v3.py"
    if not os.path.exists(path):
        print("File not found")
        return
        
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        
    # Find all missing lines (marked with # MISSING LINE)
    missing_indices = []
    for idx, line in enumerate(lines):
        if line.startswith("# MISSING LINE"):
            missing_indices.append(idx)
            
    if not missing_indices:
        print("No missing lines!")
        return
        
    # Group into ranges
    ranges = []
    start = missing_indices[0]
    prev = missing_indices[0]
    for idx in missing_indices[1:]:
        if idx == prev + 1:
            prev = idx
        else:
            ranges.append((start, prev))
            start = idx
            prev = idx
    ranges.append((start, prev))
    
    print(f"Total missing lines: {len(missing_indices)} across {len(ranges)} ranges.")
    for start_idx, end_idx in ranges:
        print("\n" + "="*50)
        print(f"MISSING RANGE: lines {start_idx + 1} to {end_idx + 1} (count: {end_idx - start_idx + 1})")
        print("="*50)
        
        # 5 lines before
        before_start = max(0, start_idx - 5)
        print("--- BEFORE ---")
        for i in range(before_start, start_idx):
            line_str = lines[i].encode('ascii', errors='replace').decode('ascii')
            print(f"{i+1}: {line_str}")
            
        # The range
        print("--- MISSING CHUNK ---")
        print(f"... [{end_idx - start_idx + 1} lines missing] ...")
        
        # 5 lines after
        after_end = min(len(lines), end_idx + 6)
        print("--- AFTER ---")
        for i in range(end_idx + 1, after_end):
            line_str = lines[i].encode('ascii', errors='replace').decode('ascii')
            print(f"{i+1}: {line_str}")

if __name__ == "__main__":
    print_missing()
