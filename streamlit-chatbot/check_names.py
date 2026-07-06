import ast
import os
import sys

def check_file(filepath):
    print(f"Analyzing {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)
        
    defined_names = set()
    used_names = []
    
    # Simple visitor to collect definitions and usages
    class ASTVisitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                defined_names.add(name.split('.')[0])
            self.generic_visit(node)
            
        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                defined_names.add(name)
            self.generic_visit(node)
            
        def visit_FunctionDef(self, node):
            defined_names.add(node.name)
            self.generic_visit(node)
            
        def visit_ClassDef(self, node):
            defined_names.add(node.name)
            self.generic_visit(node)
            
        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
                elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            defined_names.add(elt.id)
            self.generic_visit(node)
            
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                used_names.append((node.id, node.lineno))
            self.generic_visit(node)

    visitor = ASTVisitor()
    visitor.visit(tree)
    
    # Add builtins
    import builtins
    builtins_names = set(dir(builtins))
    
    # Check for undefined
    undefined = []
    for name, lineno in used_names:
        if name not in defined_names and name not in builtins_names:
            undefined.append((name, lineno))
            
    # Filter duplicates
    unique_undefined = {}
    for name, lineno in undefined:
        if name not in unique_undefined:
            unique_undefined[name] = lineno
            
    if unique_undefined:
        print(f"  Undefined names in {filepath}:")
        for name, lineno in unique_undefined.items():
            print(f"    - line {lineno}: {name}")
    else:
        print(f"  No undefined names found in {filepath}.")
        
if __name__ == "__main__":
    files = [f for f in os.listdir('.') if f.endswith('.py')]
    for file in files:
        try:
            check_file(file)
        except Exception as e:
            print(f"  Error reading {file}: {e}")
