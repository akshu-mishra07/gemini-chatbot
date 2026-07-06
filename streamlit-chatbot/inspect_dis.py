import re

def search_lines(start_line, end_line):
    dis_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\dis.txt"
    current_line = None
    lines = []
    
    with open(dis_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            # Try to match the source line number at the start of a block of disassembly
            m = re.match(r"^\s*(\d+)\s+(.*)$", line)
            if m:
                current_line = int(m.group(1))
                if start_line <= current_line <= end_line:
                    lines.append((idx + 1, current_line, line.strip()))
            else:
                if current_line is not None and start_line <= current_line <= end_line:
                    lines.append((idx + 1, current_line, line.strip()))
                    
    # Print the lines grouped by source line number
    by_source = {}
    for idx_file, src_ln, instruction in lines:
        if src_ln not in by_source:
            by_source[src_ln] = []
        by_source[src_ln].append(instruction)
        
    for src_ln in sorted(by_source.keys()):
        print(f"\n--- SOURCE LINE {src_ln} ---")
        for instr in by_source[src_ln][:30]: # print first 30 instructions of the line
            print(instr.encode('ascii', errors='replace').decode('ascii'))
        if len(by_source[src_ln]) > 30:
            print(f"... and {len(by_source[src_ln]) - 30} more instructions")

if __name__ == "__main__":
    import sys
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 2050
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 2070
    search_lines(start, end)
