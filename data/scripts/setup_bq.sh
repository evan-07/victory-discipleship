#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
DATASET_ID="bronze_dataset"
TABLE_ID="raw_members"
LOCATION="asia-southeast1" # Adjust if your project is in a different region

echo "Setting up BigQuery infrastructure in project: $PROJECT_ID"

# 1. Create Dataset (if not exists)
if bq show --dataset "$PROJECT_ID:$DATASET_ID" > /dev/null 2>&1; then
  echo "Dataset $DATASET_ID already exists."
else
  echo "Creating dataset $DATASET_ID..."
  bq --location=$LOCATION mk --dataset "$PROJECT_ID:$DATASET_ID"
fi

# 2. Create Table (if not exists)
# Schema: ingestion_timestamp:TIMESTAMP, payload:JSON, metadata:JSON
if bq show --table "$PROJECT_ID:$DATASET_ID.$TABLE_ID" > /dev/null 2>&1; then
  echo "Table $TABLE_ID already exists."
else
  echo "Creating table $TABLE_ID..."
  bq mk \
    --table \
    --time_partitioning_type=DAY \
    --time_partitioning_field=ingestion_timestamp \
    "$PROJECT_ID:$DATASET_ID.$TABLE_ID" \
    ingestion_timestamp:TIMESTAMP,payload:JSON,metadata:JSON
    
  echo "Table $TABLE_ID created successfully."
fi

echo "Infrastructure setup complete!"
