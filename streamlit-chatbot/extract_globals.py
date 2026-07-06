import marshal
import sys
import os
import pprint

class MockObject:
    def __init__(self, *args, **kwargs):
        pass
    def __getattr__(self, name):
        return MockObject()
    def __call__(self, *args, **kwargs):
        return MockObject()
    def __getitem__(self, key):
        return MockObject()
    def __iter__(self):
        return iter([])
    def __bool__(self):
        return False

class SessionStateMock(dict):
    def __getattr__(self, name):
        if name not in self:
            self[name] = MockObject()
        return self[name]
    def __setattr__(self, name, value):
        self[name] = value
    def __delattr__(self, name):
        if name in self:
            del self[name]

class StreamlitMock:
    def __init__(self):
        self.session_state = SessionStateMock()
    def __getattr__(self, name):
        return MockObject()

def extract():
    pyc_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\__pycache__\app.cpython-313.pyc"
    if not os.path.exists(pyc_path):
        print("pyc not found")
        return
        
    with open(pyc_path, "rb") as f:
        f.read(16)  # Skip 16-byte header
        code_obj = marshal.load(f)
        
    st_mock = StreamlitMock()
    
    # Setup mock sys.modules
    sys.modules['streamlit'] = st_mock
    sys.modules['PIL'] = MockObject()
    sys.modules['PIL.Image'] = MockObject()
    sys.modules['chatbot'] = MockObject()
    sys.modules['knowledge_manager'] = MockObject()
    sys.modules['rag_engine'] = MockObject()
    
    # Run the module bytecode in a clean dict
    globals_dict = {
        '__name__': '__main__',
        'st': st_mock,
        'datetime': MockObject(),
        'os': MockObject(),
        'Image': sys.modules['PIL.Image'],
        'send_message_stream': MockObject(),
        'load_metadata': MockObject(),
        'add_document': MockObject(),
        'delete_document': MockObject(),
        'rebuild_knowledge_base': MockObject(),
        'sync_and_refresh_knowledge_base': MockObject(),
        'query_relevant_chunks': MockObject(),
        'format_rag_context': MockObject(),
        'build_system_prompt_with_context': MockObject(),
    }
    
    print("Executing bytecode...")
    try:
        exec(code_obj, globals_dict)
        print("Bytecode executed successfully!")
    except Exception as e:
        print("Execution failed/stopped at some statement:", e)
        
    # Dump key global variables
    interesting_keys = [
        'LOCAL_GREETINGS', 'LOCAL_KNOWLEDGE_BASE', 
        'LOCAL_GREETINGS_EN', 'LOCAL_GREETINGS_HI',
        'LOCAL_DEFAULT_HELP_EN', 'LOCAL_DEFAULT_HELP_HI',
        'OFFLINE_TOPICS', 'KB_SYSTEM_PROMPT_TEMPLATE', 
        'RESEARCH_SYSTEM_PROMPT'
    ]
    
    output_path = r"c:\Users\ACER\OneDrive\Desktop\gemini-chatbot\streamlit-chatbot\recovered_globals.py"
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write("# Recovered global variables from compiled bytecode\n\n")
        for k in interesting_keys:
            if k in globals_dict:
                val = globals_dict[k]
                out_f.write(f"{k} = ")
                pprint.pprint(val, stream=out_f, width=120, compact=False)
                out_f.write("\n\n")
                print(f"Extracted {k}")
            else:
                print(f"Key {k} not found in globals")
                
    print(f"Saved recovered globals to {output_path}")

if __name__ == "__main__":
    extract()
