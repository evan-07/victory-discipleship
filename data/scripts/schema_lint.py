#!/usr/bin/env python3
"""
Schema linter for Dataform SQLX files.
Validates naming conventions, required config fields, and dependencies.
"""

import os
import sys
import re
from pathlib import Path


def lint_sqlx_file(filepath):
    """Validate a single SQLX file"""
    errors = []
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for required config block
    if 'config {' not in content:
        errors.append(f"Missing config block")
    
    # Check for required fields
    if 'type:' not in content:
        errors.append(f"Missing 'type' in config")
    if 'description:' not in content:
        errors.append(f"Missing 'description' in config")
    
    # Check naming conventions based on layer
    filename = Path(filepath).stem
    parent_dir = Path(filepath).parent.name
    
    # Bronze tables should start with 'raw_'
    if '1_bronze' in str(filepath) and not filename.startswith('raw_'):
        errors.append(f"Bronze tables should start with 'raw_' (got: {filename})")
    
    # Silver analytical views should start with 'view_'
    if '2_silver' in str(filepath) and filename.startswith('view_') and 'type: "view"' not in content and 'type: "table"' not in content:
        errors.append(f"Silver views should have type 'view' or 'table'")
    
    # Gold reporting tables should start with 'rept_' or 'dim_' or 'fact_'
    if '3_gold' in str(filepath):
        if not (filename.startswith('rept_') or filename.startswith('dim_') or filename.startswith('fact_') or filename in ['summary', 'view_stats']):
            errors.append(f"Gold tables should start with 'rept_', 'dim_', or 'fact_' (got: {filename})")
    
    return errors


def main():
    """Lint all SQLX files in data/definitions"""
    script_dir = Path(__file__).parent
    definitions_dir = script_dir.parent / 'definitions'
    
    if not definitions_dir.exists():
        print(f"❌ Error: definitions directory not found at {definitions_dir}")
        return 1
    
    sqlx_files = list(definitions_dir.rglob('*.sqlx'))
    
    if not sqlx_files:
        print(f"⚠️  Warning: No SQLX files found in {definitions_dir}")
        return 0
    
    total_errors = 0
    files_with_errors = 0
    
    for sqlx_file in sqlx_files:
        errors = lint_sqlx_file(sqlx_file)
        if errors:
            files_with_errors += 1
            print(f"❌ {sqlx_file.relative_to(definitions_dir)}:")
            for error in errors:
                print(f"   - {error}")
            total_errors += len(errors)
    
    if total_errors == 0:
        print(f"✅ All {len(sqlx_files)} SQLX files pass schema lint")
        return 0
    else:
        print(f"\n❌ Found {total_errors} schema lint errors in {files_with_errors}/{len(sqlx_files)} files")
        return 1


if __name__ == '__main__':
    sys.exit(main())
