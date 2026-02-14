#!/bin/bash
# Generates a high-level summary of the project state

echo "=== PROJECT MAP ==="
# Print directory tree excluding trash
find . -maxdepth 3 -not -path '*/.*' | sed 's|/[^/]*|  |g'

echo -e "\n=== ARCHITECTURAL CONSTRAINTS ==="
grep -A 5 "Tech Stack" ARCHITECTURE.md

echo -e "\n=== RECENT CHANGES ==="
git log -1 --pretty=format:"Last Commit: %h - %s (%cr)"