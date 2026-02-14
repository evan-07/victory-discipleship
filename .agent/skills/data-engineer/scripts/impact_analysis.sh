#!/bin/bash
# Usage: ./impact_analysis.sh [column_name]

SEARCH_TERM=$1

if [ -z "$SEARCH_TERM" ]; then
  echo "Error: No column name provided."
  exit 1
fi

echo "🔍 Searching for '$SEARCH_TERM' in Dataform definitions..."
echo "--------------------------------------------------------"

# Find matches in SQLX files
grep -rnw "data/definitions" -e "$SEARCH_TERM"

echo "--------------------------------------------------------"
echo "⚠️  Check the files listed above. If any act as a source for Looker, you must flag a breaking change."