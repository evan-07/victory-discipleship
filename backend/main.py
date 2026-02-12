import os
import json
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import bigquery

app = Flask(__name__)

# Enable CORS: Allows your Cloudflare site to talk to this Cloud Run URL
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize BigQuery Client
client = bigquery.Client()

# Configuration (Change these to match your GCP project)
DATASET_ID = "bronze_dataset"
TABLE_ID = "raw_members"

@app.route('/api/submit', methods=['POST'])
def submit_form():
    try:
        data = request.json
        
        # --- 1. HONEY POT SPAM CHECK ---
        # If the hidden 'website_url' field has ANY text, it is a bot.
        if data.get('website_url'):
            print(f"Spam bot detected from IP: {request.remote_addr}")
            # Return "Success" so the bot thinks it won, but DO NOT save data.
            return jsonify({"result": "success", "message": "Saved"}), 200

        # --- 2. VALIDATION (Basic) ---
        if not data.get('email') or not data.get('lastName'):
            return jsonify({"result": "error", "message": "Missing required fields"}), 400

        # --- 3. PREPARE ROW FOR BIGQUERY ---
        # We assume the table is: project.dataset.table
        table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
        
        # Clean up data before inserting (remove the honey pot field from storage)
        clean_payload = data.copy()
        clean_payload.pop('website_url', None)

        row_to_insert = [{
            "event_timestamp": datetime.datetime.utcnow().isoformat(),
            "email": data.get('email'),
            "first_name": data.get('firstName'),
            "last_name": data.get('lastName'),
            "mobile_number": data.get('primaryMobile'),
            "ip_address": request.headers.get('X-Forwarded-For', request.remote_addr),
            "user_agent": request.headers.get('User-Agent'),
            "payload_json": json.dumps(clean_payload) # Dump everything else here
        }]

        # --- 4. INSERT INTO BIGQUERY ---
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