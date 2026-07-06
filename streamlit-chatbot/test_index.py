import os
import sys

# Ensure streamlit-chatbot folder is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge_manager import add_document, load_metadata
from vector_store import load_vector_store

def run_test():
    print("Testing document indexing...")
    test_content = b"This is a test document about Python programming. Python is an interpreted high-level general-purpose programming language. Created by Guido van Rossum."
    test_filename = "test_python_info.txt"
    
    success, msg = add_document(test_filename, test_content)
    print(f"Index result: success={success}, msg={msg}")
    
    meta = load_metadata()
    print("Metadata content:", meta)
    
    db = load_vector_store()
    if db is not None:
        print("Vector store loaded successfully!")
        docs = db.similarity_search("Who created Python?")
        print(f"Search results count: {len(docs)}")
        if docs:
            print("Top doc content:", docs[0].page_content)
    else:
        print("Vector store remains empty/None.")

if __name__ == "__main__":
    run_test()
