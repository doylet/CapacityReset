#!/usr/bin/env python3
"""
One-time script to insert sample BrightData response into BigQuery for ETL testing.
"""
import json
from google.cloud import bigquery
from datetime import datetime
import uuid

# Read the JSON file
with open('/Users/thomasdoyle/Downloads/bd_20251122_014543_0.json', 'r') as f:
    brightdata_response = json.load(f)

# Create BigQuery client
client = bigquery.Client()

# Prepare row data
request_id = str(uuid.uuid4())
row = {
    "request_id": request_id,
    "timestamp": datetime.utcnow().isoformat(),
    "dataset_id": "gd_l7q7dkp244hwjntr0",  # Your BrightData dataset ID
    "cities": ["Brisbane, Queensland, Australia", "Sydney, New South Wales, Australia", "Melbourne, Victoria, Australia"],
    "keyword": "product management",
    "brightdata_response": brightdata_response,  # The full JSON array
    "status": "200",
    "gcs_prefix": f"raw/{request_id}/"
}

# Insert into BigQuery
table_id = "sylvan-replica-478802-p4.brightdata_jobs.scrape_requests"
errors = client.insert_rows_json(table_id, [row])

if errors:
    print(f"Errors occurred: {errors}")
else:
    print(f"Successfully inserted test data with request_id: {request_id}")
    print(f"You can now run the ETL: curl -X POST https://brightdata-etl-e3b7ctuuxa-ts.a.run.app")
