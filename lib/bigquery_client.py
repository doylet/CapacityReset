import json
import uuid
from datetime import datetime
from google.cloud import bigquery
from lib.gcloud_env_client import (
    BRIGHTDATA_DATASET_ID,
)


bq = bigquery.Client()

def log_request_to_bigquery(response_body, status):
    table = "sylvan-replica-478802-p4.brightdata_jobs.scrape_requests"
    
    row = {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "dataset_id": BRIGHTDATA_DATASET_ID,
        "cities": ["brisbane", "sydney", "melbourne"],
        "keyword": "product management",
        "brightdata_response": json.loads(response_body),
        "status": status
    }
    
    bq.insert_rows_json(table, [row])
