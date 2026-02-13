import os
import json
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- CRITICAL IMPORT
from google.cloud import bigquery

app = Flask(__name__)

# --- FIX START ---
# Allow ALL origins (*) for now to get it working.
# Once stable, change "*" to "https://your-project.pages.dev"
CORS(app, resources={r"/api/*": {"origins": "*"}}) 
# --- FIX END ---

# Initialize BigQuery Client
client = bigquery.Client()

# Configuration (Change these to match your GCP project)
DATASET_ID = "bronze_dataset"
TABLE_ID = "raw_members"

@app.route('/api/submit', methods=['POST'])
def submit_form():
    try:
        # Check if request is JSON
        if not request.is_json:
            return jsonify({"result": "error", "message": "Request must be JSON"}), 400

        data = request.json
        
        # --- HONEY POT SPAM CHECK ---
        if data.get('website_url'):
            print(f"Spam bot detected from IP: {request.remote_addr}")
            return jsonify({"result": "success", "message": "Saved"}), 200

        # --- VALIDATION ---
        # Minimal validation: just ensure it's not empty. 
        # Schema enforcement happens in Dataform, not here.
        if not data:
             return jsonify({"result": "error", "message": "Empty payload"}), 400

        # --- PREPARE ROW ---
        table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
        
        # Metadata extraction
        metadata = {
            "ip_address": request.headers.get('X-Forwarded-For', request.remote_addr),
            "user_agent": request.headers.get('User-Agent'),
            "origin": request.headers.get('Origin'),
            "referer": request.headers.get('Referer')
        }

        row_to_insert = [{
            "ingestion_timestamp": datetime.datetime.utcnow().isoformat(),
            "payload": json.dumps(data),  # Store entire payload as JSON string
            "metadata": json.dumps(metadata) # Store metadata as JSON string
        }]

        # --- INSERT ---
        errors = client.insert_rows_json(table_ref, row_to_insert)

        if errors:
            print(f"BigQuery Errors: {errors}")
            return jsonify({"result": "error", "message": "Database error"}), 500

        return jsonify({"result": "success"}), 200

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"result": "error", "message": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
