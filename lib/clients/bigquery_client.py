import json
import uuid
from datetime import datetime
from google.cloud import bigquery
from lib.gcloud_env_client import (
    BRIGHTDATA_DATASET_ID,
)


bq = bigquery.Client()

def log_request_to_bigquery(response_body, status, request_id):
    try:
        table_id = "sylvan-replica-478802-p4.brightdata_jobs.scrape_requests"
        
        # Keep response_body as JSON string for the JSON column type
        # If it's not a string, convert it to JSON string
        if isinstance(response_body, str):
            response_json = response_body
        else:
            response_json = json.dumps(response_body)
        
        row = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "dataset_id": BRIGHTDATA_DATASET_ID,
            "cities": ["brisbane", "sydney", "melbourne"],
            "keyword": "product management",
            "brightdata_response": response_json,
            "status": str(status),  # Convert status to string
            "gcs_prefix": f"raw/{request_id}/",
        }
        
        errors = bq.insert_rows_json(table_id, [row])
        if errors:
            print(f"BigQuery insert errors: {errors}")
        else:
            print(f"Successfully logged request to BigQuery: {row['request_id']}")
    except Exception as e:
        print(f"Failed to log to BigQuery: {e}")
