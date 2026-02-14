# Test Data Generation & Loading Guide

This guide explains how to generate realistic test data for the Member Profile system and load it into BigQuery.

## 1. Prerequisites

Ensure you have Python 3 installed. You will also need the dependencies listed in `tests/data_generator/requirements.txt`.

```bash
pip3 install -r tests/data_generator/requirements.txt
```

## 2. Generating Test Data

The script `tests/data_generator/generate_test_data.py` creates a JSON file containing `Leaders` and `Members` with the correct relational links established (i.e., Members are assigned to seeded Leaders, and some Members are interns of those Leaders).

Run the script from the root of the repository:

```bash
python3 tests/data_generator/generate_test_data.py
```

**Output:**
- A file named `test_cases.json` will be created in your current directory.
- It contains approximately 20 records (5 Leaders, 15 Members by default configuration).

## 3. Loading Data into BigQuery (Bronze Layer)

Once you have the `test_cases.json` file, you can load it into your BigQuery Bronze dataset.

### Option A: Using `bq` Command Line Tool

Adjust the dataset and table names (`your_project:bronze_dataset.members_raw`) as per your actual BigQuery setup.

```bash
# General syntax: bq load --autodetect --source_format=NEWLINE_DELIMITED_JSON [DATASET].[TABLE] [SOURCE_FILE]

# NOTE: The generated JSON is a standard JSON array. BigQuery 'bq load' often expects 
# Newline Delimited JSON (NDJSON). 
# You might need to use `jq` to convert it or use the BigQuery UI which handles standard JSON arrays better.

# To convert to NDJSON using jq:
jq -c '.[]' test_cases.json > test_cases.ndjson

# Then load:
bq load --project_id=victory-discipleship \
  --source_format=NEWLINE_DELIMITED_JSON \
  victory-discipleship:bronze_dataset.raw_members \
  test_cases.ndjson \
  ingestion_timestamp:TIMESTAMP,payload:JSON,metadata:JSON
```

**Note:** If you haven't set a default project in gcloud, you must include `--project_id=victory-discipleship` (as shown above) so BigQuery knows which project to bill for the load job. Alternatively, run `gcloud config set project victory-discipleship` once to set it as default.

### Option B: Using BigQuery Console (Web UI)

1. Go to the [BigQuery Console](https://console.cloud.google.com/bigquery).
2. Select your `bronze` dataset.
3. Click **Create Table**.
4. **Source**: Upload -> Select `test_cases.json`.
5. **File format**: JSON.
6. **Table**: Enter a table name (e.g., `members_raw`).
7. **Schema**: Check "Auto detect".
8. Click **Create Table**.

## 4. Script Configuration

You can modify `tests/data_generator/generate_test_data.py` to change the number of records:

```python
# Configuration
NUM_LEADERS = 5   # "X count of victory group leaders"
NUM_MEMBERS = 15  # Pool of members to assign to leaders
```
