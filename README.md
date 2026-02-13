# Victory Discipleship

This repository contains the code for the Victory Discipleship member management system.

## Data Pipeline (Dataform & BigQuery)

We use **Dataform** to manage data transformations in BigQuery. The pipeline consists of two layers:
1.  **Bronze (Raw)**: Raw JSON data ingested from the website.
2.  **Silver (Clean)**: Cleaned, deduplicated, and standardized data.

### Prerequisites

1.  **Install Dataform CLI**:
    ```bash
    npm install -g @dataform/cli
    # OR use npx without installing:
    # npx @dataform/cli <command>
    ```
2.  **Authentication**:
    Ensure you are authenticated with Google Cloud:
    ```bash
    gcloud auth application-default login
    ```

### Infrastructure Setup

To create the initial BigQuery dataset and raw table, run:

```bash
chmod +x data/scripts/setup_bq.sh
./data/scripts/setup_bq.sh
```

### Running Dataform

1.  **Compile** (Check for errors):
    ```bash
    cd data
    dataform compile
    ```

2.  **Run** (Execute changes in BigQuery):
    ```bash
    cd data
    dataform run
    ```
    *Note: This will create/update tables in the `victory_data` schema.*

### Development vs Production

-   **Development**: Uses `victory_data_dev` schema.
-   **Production**: Uses `victory_data` schema. Set via `dataform.json` environments.

## Website