#!/bin/bash
# Usage: ./find_lineage.sh column_name
# Finds all SQLX files that reference a specific column to help the agent identify impact.
grep -r "$1" data/definitions/