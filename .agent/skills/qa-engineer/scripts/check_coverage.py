import ast
import os
import sys

# Configuration
SOURCE_DIR = "backend"
TEST_DIR = "backend/tests"
IGNORE_FUNCTIONS = {"__init__", "main", "lifespan"}  # Skip boilerplate

def get_functions_from_file(filepath):
    """Extracts function names from a python file using AST."""
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
            return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        except SyntaxError:
            return set()

def scan_coverage():
    missing_tests = []
    
    # Walk through source directory
    for root, _, files in os.walk(SOURCE_DIR):
        if "tests" in root: continue # Skip test folder itself

        for file in files:
            if file.endswith(".py"):
                source_path = os.path.join(root, file)
                functions = get_functions_from_file(source_path)
                
                # Determine expected test file path (e.g., main.py -> tests/test_main.py)
                test_filename = f"test_{file}"
                test_path = os.path.join(TEST_DIR, test_filename)
                
                # Get existing tests
                existing_tests = get_functions_from_file(test_path)
                
                for func in functions:
                    if func in IGNORE_FUNCTIONS:
                        continue
                        
                    # Rule: Code 'create_user' -> Expects 'test_create_user'
                    expected_test_name = f"test_{func}"
                    if expected_test_name not in existing_tests:
                        missing_tests.append(f"{file} :: {func} (Expected: {expected_test_name})")

    if missing_tests:
        print("❌ [QA FAIL] The following functions are missing tests:")
        for item in missing_tests:
            print(f"   - {item}")
        sys.exit(1)
    else:
        print("✅ [QA PASS] All functions have corresponding test definitions.")

if __name__ == "__main__":
    scan_coverage()