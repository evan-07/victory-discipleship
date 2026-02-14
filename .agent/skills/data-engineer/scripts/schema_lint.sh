import os
import re

def validate_sqlx():
    # Regex to find column definitions or select statements
    # This is a simplified check; a real parser would be better but this works for agents
    bad_patterns = [
        (r"select.*[ ,]id[ ,]", "Ambiguous 'id' column found. Use 'member_id' or 'event_id'."),
        (r"date_created", "Use 'created_at' for timestamps."),
    ]
    
    for root, _, files in os.walk("data/definitions"):
        for file in files:
            if file.endswith(".sqlx"):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read().lower()
                    for pattern, msg in bad_patterns:
                        if re.search(pattern, content):
                            print(f"❌ LINT ERROR in {file}: {msg}")

if __name__ == "__main__":
    validate_sqlx()