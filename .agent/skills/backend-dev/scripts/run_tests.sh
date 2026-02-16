#!/bin/bash
# Runs pytest with verbose output
# Usage: ./run_tests.sh [path_to_test_file]

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: ./run_tests.sh [path_to_test_file]"
    echo "Runs pytest with verbose output. If no file provided, runs all tests."
    exit 0
fi

if [ -z "$1" ]; then
    echo "Running all tests..."
    pytest -v backend/tests/
else
    echo "Running specific test: $1"
    pytest -v "$1"
fi
