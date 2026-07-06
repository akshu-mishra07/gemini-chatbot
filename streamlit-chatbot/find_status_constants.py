import sys

sys.stdout.reconfigure(encoding='utf-8')
constants_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\constants.txt"

def find_status_constants():
    with open(constants_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Find all blocks
    blocks = content.split("\n\n")
    for b in blocks:
        if any(kw in b for kw in ["Online", "Quota", "Rate", "Billing", "Invalid", "Missing", "Offline"]):
            print("-" * 50)
            print(b.strip())

if __name__ == "__main__":
    find_status_constants()
