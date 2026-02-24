#!/usr/bin/env python3
import sys
import os
import argparse

def scaffold_feature(feature_name):
    # normalize feature name
    feature_name = feature_name.lower().replace("-", "_")
    
    src_path = f"backend/src/{feature_name}.py"
    test_path = f"backend/tests/test_{feature_name}.py"

    # Create src file
    if not os.path.exists(src_path):
        os.makedirs(os.path.dirname(src_path), exist_ok=True)
        with open(src_path, "w") as f:
            f.write(f"# Feature: {feature_name}\n\ndef {feature_name}_logic():\n    pass\n")
        print(f"Created {src_path}")
    else:
        print(f"Skipped {src_path} (exists)")

    # Create test file
    if not os.path.exists(test_path):
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        with open(test_path, "w") as f:
            f.write(f"import pytest\nfrom backend.src.{feature_name} import {feature_name}_logic\n\ndef test_{feature_name}_initial():\n    assert {feature_name}_logic() is None  # Change expectation to fail if needed\n")
        print(f"Created {test_path}")
    else:
        print(f"Skipped {test_path} (exists)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffolds a new feature (source and test files) for the backend.")
    parser.add_argument("feature_name", help="Name of the feature to scaffold.")
    args = parser.parse_args()
    
    scaffold_feature(args.feature_name)
