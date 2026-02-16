#!/bin/bash
# Usage: ./find_lineage.sh column_name
# Finds all SQLX files that reference a specific column to help the agent identify impact.
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: ./find_lineage.sh <column_name>"
    echo "Finds all SQLX files that reference a specific column."
    exit 0
fi

grep -r "$1" data/definitions/