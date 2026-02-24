import os
import re
import argparse
import sys

def validate_sqlx():
    # Regex to find column definitions or select statements
    # This is a simplified check; a real parser would be better but this works for agents
    bad_patterns = [
        (r"select.*[ ,]id[ ,]", "Ambiguous 'id' column found. Use 'member_id' or 'event_id'."),
        (r"date_created", "Use 'created_at' for timestamps."),
    ]
    
    violations = 0
    for root, _, files in os.walk("data/definitions"):
        for file in files:
            if file.endswith(".sqlx"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r') as f:
                        content = f.read().lower()
                        for pattern, msg in bad_patterns:
                            if re.search(pattern, content):
                                print(f"❌ LINT ERROR in {file}: {msg}")
                                violations += 1
                except Exception as e:
                    print(f"Error reading {file}: {e}")

    if violations == 0:
        print("✅ Schema lint passed.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lints SQLX files for schema conventions.")
    args = parser.parse_args()
    
    validate_sqlx()