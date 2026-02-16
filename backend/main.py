import os
import json
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- CRITICAL IMPORT
from google.cloud import bigquery
from datetime import datetime

app = Flask(__name__)

# --- FIX START ---
# Allow ALL origins (*) for now to get it working.
# Once stable, change "*" to "https://your-project.pages.dev"
CORS(app, resources={r"/api/*": {"origins": "*"}}) 
# --- FIX END ---

# Initialize BigQuery client
project_id = os.getenv("GCP_PROJECT", "victory-discipleship")
client = bigquery.Client(project=project_id)

def get_api_version():
    """
    Returns the current API version.
    This is a test function to verify PR and SonarQube workflows.
    """
    return "1.0.0"

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

@app.route('/api/search', methods=['GET'])
def search_members():
    """
    Search for members by email or name in silver_dataset.members table.
    Query parameter: query (email or name substring)
    Returns: JSON array of matching members
    """
    try:
        query = request.args.get('query', '').strip()
        
        if not query:
            return jsonify({"result": "error", "message": "Query parameter required"}), 400
        
        # Build BigQuery SQL query
        # Search by exact email match OR partial first/last name match (case-insensitive)
        sql_query = f"""
        SELECT 
            ingestion_timestamp,
            first_name,
            middle_name,
            last_name,
            suffix,
            email,
            fb_name,
            gender,
            birthday,
            marital_status,
            anniversary,
            occupation_type,
            education_level,
            school,
            year_level,
            course,
            job_title,
            company,
            employer_industry,
            business_name,
            business_nature,
            business_address,
            discipleship_classes,
            is_ministry_member,
            ministry_teams,
            want_ministry,
            is_vg_member,
            vg_leader_name,
            want_vg,
            is_vg_leader,
            vg_count,
            vg_details,
            has_intern,
            intern_names,
            mobile_number,
            sec_mobile_number
        FROM `silver_dataset.stg_members`
        WHERE 
            LOWER(email) = LOWER(@query)
            OR LOWER(first_name) LIKE CONCAT('%', LOWER(@query), '%')
            OR LOWER(last_name) LIKE CONCAT('%', LOWER(@query), '%')
        ORDER BY ingestion_timestamp DESC
        LIMIT 50
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("query", "STRING", query)
            ]
        )
        
        query_job = client.query(sql_query, job_config=job_config)
        results = query_job.result()
        
        # Convert results to list of dicts
        members = []
        for row in results:
            member = dict(row.items())
            members.append(member)
        
        return jsonify({"result": "success", "members": members}), 200
        
    except Exception as e:
        print(f"Search Error: {str(e)}")
        return jsonify({"result": "error", "message": "Search failed"}), 500

@app.route('/api/reference-data', methods=['GET'])
def get_reference_data():
    """
    Get reference data for form dropdowns.
    Returns: JSON object with categories as keys and arrays as values
    """
    try:
        sql_query = """
        SELECT 
            category,
            value,
            display_order
        FROM `bronze_dataset.raw_reference_data`
        WHERE is_active = TRUE
        ORDER BY category, display_order
        """
        
        query_job = client.query(sql_query)
        results = query_job.result()
        
        # Group by category
        reference_data = {}
        for row in results:
            category = row['category']
            if category not in reference_data:
                reference_data[category] = []
            reference_data[category].append(row['value'])
        
        return jsonify({
            "result": "success",
            "data": reference_data
        }), 200
        
    except Exception as e:
        print(f"Reference Data Error: {str(e)}")
        return jsonify({
            "result": "error",
            "message": "Failed to fetch reference data"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
