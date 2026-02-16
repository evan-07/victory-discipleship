#!/bin/bash
# Returns a summary of changes since the last README update

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: ./get_diff.sh"
    echo "Returns a summary of git changes in src/ since HEAD."
    exit 0
fi

git diff HEAD -- 'src/'