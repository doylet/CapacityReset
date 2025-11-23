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
        table_id = "sylvan-replica-478802-p4.brightdata_jobs.scraper_execution_logs"
        
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
            "processed": False,  # Explicitly set as boolean
        }
        
        # Use load_table_from_json with WRITE_APPEND for immediate queryability
        # This bypasses the streaming buffer
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        
        load_job = bq.load_table_from_json([row], table_id, job_config=job_config)
        load_job.result()  # Wait for job to complete
        
        print(f"Successfully logged request to BigQuery (immediately queryable): {row['request_id']}")
    except Exception as e:
        print(f"Failed to log to BigQuery: {e}")
