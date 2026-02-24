#!/bin/bash
# Generates a high-level summary of the project state

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: ./generate_context.sh"
    echo "Generates a high-level summary of the project state, including file tree and recent changes."
    exit 0
fi

echo "=== PROJECT MAP ==="
# Print directory tree excluding trash
find . -maxdepth 3 -not -path '*/.*' | sed 's|/[^/]*|  |g'

echo -e "\n=== ARCHITECTURAL CONSTRAINTS ==="
grep -A 5 "Tech Stack" ARCHITECTURE.md

echo -e "\n=== RECENT CHANGES ==="
git log -1 --pretty=format:"Last Commit: %h - %s (%cr)"