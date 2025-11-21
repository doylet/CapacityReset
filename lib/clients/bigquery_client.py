import json
import uuid
from datetime import datetime
from google.cloud import bigquery
from lib.gcloud_env_client import (
    BRIGHTDATA_DATASET_ID,
)


bq = bigquery.Client()

def log_request_to_bigquery(response_body, status):
    try:
        table_id = "sylvan-replica-478802-p4.brightdata_jobs.scrape_requests"
        
        # Parse response body if it's a string
        if isinstance(response_body, str):
            response_data = json.loads(response_body)
        else:
            response_data = response_body
        
        row = {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "dataset_id": BRIGHTDATA_DATASET_ID,
            "cities": ["brisbane", "sydney", "melbourne"],
            "keyword": "product management",
            "brightdata_response": response_data,
            "status": status
        }
        
        errors = bq.insert_rows_json(table_id, [row])
        if errors:
            print(f"BigQuery insert errors: {errors}")
        else:
            print(f"Successfully logged request to BigQuery: {row['request_id']}")
    except Exception as e:
        print(f"Failed to log to BigQuery: {e}")
