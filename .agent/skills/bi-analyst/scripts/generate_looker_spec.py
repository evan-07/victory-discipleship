#!/usr/bin/env python3
import sys
import json
import os

def generate_spec(schema_file):
    """
    Generates a Looker Studio configuration specification from a BigQuery schema JSON.
    """
    if not os.path.exists(schema_file):
        print(f"Error: Schema file '{schema_file}' not found.")
        sys.exit(1)

    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{schema_file}'.")
        sys.exit(1)

    table_name = schema.get('table_name', 'Unknown Table')
    columns = schema.get('columns', [])

    print(f"# Looker Studio Configuration Spec: {table_name}")
    print("\n## 1. Data Source")
    print(f"* **Connection:** BigQuery")
    print(f"* **Table:** `{table_name}`")
    print(f"* **Update Frequency:** Daily (Partitioned)")

    print("\n## 2. Recommended Configuration")
    
    dims = []
    metrics = []
    dates = []

    for col in columns:
        name = col.get('name')
        type_ = col.get('type', 'STRING').upper()

        if type_ in ['TIMESTAMP', 'DATE', 'DATETIME']:
            dates.append(name)
            dims.append(f"{name} (Date)")
        elif type_ in ['INTEGER', 'FLOAT', 'NUMERIC']:
            metrics.append(f"SUM({name})")
            metrics.append(f"AVG({name})")
            dims.append(name) # Can also be a dim
        else:
            dims.append(name)
            metrics.append(f"COUNT_DISTINCT({name})")

    print("\n### Dimensions (Drag to 'Dimensions')")
    for d in dims:
        print(f"* {d}")

    print("\n### Metrics (Drag to 'Metrics')")
    print(f"* Record Count (Default)")
    for m in metrics:
        print(f"* {m}")

    print("\n### Filters (Drag to 'Filter' or 'Date Range')")
    if dates:
        print(f"* **Date Range:** {dates[0]}")
    else:
        print("* *No date columns detected for date range controls.*")

    print("\n## 3. Visualization Suggestions")
    print("* **Time Series:** Use Date dimension + any Metric.")
    print("* **Scorecard:** Use 'Record Count' or specific KPIs.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_looker_spec.py <schema_json_file>")
        print("\nExpected JSON format:")
        print('{ "table_name": "example", "columns": [ {"name": "id", "type": "STRING"}, ... ] }')
        sys.exit(1)
    
    generate_spec(sys.argv[1])
