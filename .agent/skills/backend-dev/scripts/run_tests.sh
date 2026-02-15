#!/bin/bash
# Runs pytest with verbose output
# Usage: ./run_tests.sh [path_to_test_file]

if [ -z "$1" ]; then
    echo "Running all tests..."
    pytest -v backend/tests/
else
    echo "Running specific test: $1"
    pytest -v "$1"
fi
