import os
import sys
import argparse

# Rules: Forbidden imports or file placements
RESTRICTIONS = {
    "frontend/": ["import sqlalchemy", "import pandas", "secrets"],
    "backend/models/": ["from flask import request"], # Models should be pure
}

def check_files():
    violations = []
    for folder, banned_terms in RESTRICTIONS.items():
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                # Clean up directories we don't want to traverse
                dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__']]
                
                for file in files:
                    if file.endswith((".js", ".py", ".ts")):
                        path = os.path.join(root, file)
                        with open(path, 'r', errors='ignore') as f:
                            content = f.read()
                            for term in banned_terms:
                                if term in content:
                                    violations.append(f"VIOLATION in {path}: Found banned term '{term}'")
    
    if violations:
        print("\n".join(violations))
        sys.exit(1)
    print("✅ Project structure adheres to ARCHITECTURE.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validates project structure against ARCHITECTURE.md rules.")
    args = parser.parse_args()
    
    check_files()