import json
import uuid
from datetime import datetime
from typing import List, Optional
from google.cloud import bigquery
from lib.gcloud_env_client import (
    BRIGHTDATA_DATASET_ID,
)


bq = bigquery.Client()

def log_queries_to_bigquery(
    queries: List[dict],
    response_body,
    status,
    request_id: str
):
    """
    Log individual query records to BigQuery.
    
    Args:
        queries: List of query dictionaries from JobSearchQuery.to_dict()
        response_body: API response body
        status: HTTP status code
        request_id: Unique request identifier
    """
    try:
        table_id = "sylvan-replica-478802-p4.brightdata_jobs.request_queries"
        
        # Convert response_body to JSON string
        if isinstance(response_body, str):
            response_json = response_body
        else:
            response_json = json.dumps(response_body)
        
        timestamp = datetime.utcnow().isoformat()
        gcs_prefix = f"raw/{request_id}/"
        
        # Create a row for each query
        rows = []
        for idx, query in enumerate(queries):
            row = {
                "request_id": request_id,
                "query_index": idx,
                "timestamp": timestamp,
                "location": query.get("location", ""),
                "keyword": query.get("keyword", ""),
                "country": query.get("country", ""),
                "time_range": query.get("time_range", ""),
                "job_type": query.get("job_type", ""),
                "remote": query.get("remote", ""),
                "experience_level": query.get("experience_level", ""),
                "company": query.get("company", ""),
                "location_radius": query.get("location_radius", ""),
                "dataset_id": BRIGHTDATA_DATASET_ID,
                "gcs_prefix": gcs_prefix,
                "brightdata_response": response_json,
                "status": str(status),
                "processed": False,
            }
            rows.append(row)
        
        # Use load_table_from_json with WRITE_APPEND for immediate queryability
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        
        load_job = bq.load_table_from_json(rows, table_id, job_config=job_config)
        load_job.result()  # Wait for job to complete
        
        print(f"Successfully logged {len(rows)} queries to BigQuery: {request_id}")
    except Exception as e:
        print(f"Failed to log queries to BigQuery: {e}")


def log_request_to_bigquery(response_body, status, request_id, queries: Optional[List[dict]] = None):
    """
    Legacy function for backward compatibility. Logs to the old execution_logs table.
    
    Args:
        response_body: API response body
        status: HTTP status code
        request_id: Unique request identifier
        queries: Optional list of query dictionaries (for new table logging)
    """
    # If queries are provided, log to new table
    if queries:
        log_queries_to_bigquery(queries, response_body, status, request_id)
    
    # Also log to legacy table for backward compatibility
    try:
        table_id = "sylvan-replica-478802-p4.brightdata_jobs.scraper_execution_logs"
        
        # Keep response_body as JSON string for the JSON column type
        if isinstance(response_body, str):
            response_json = response_body
        else:
            response_json = json.dumps(response_body)
        
        # Extract cities and keyword from queries if provided, otherwise use defaults
        if queries:
            cities = list(set(q.get("location", "") for q in queries if q.get("location")))
            keywords = list(set(q.get("keyword", "") for q in queries if q.get("keyword")))
            keyword = keywords[0] if keywords else "product management"
        else:
            cities = ["brisbane", "sydney", "melbourne"]
            keyword = "product management"
        
        row = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "dataset_id": BRIGHTDATA_DATASET_ID,
            "cities": cities,
            "keyword": keyword,
            "brightdata_response": response_json,
            "status": str(status),
            "gcs_prefix": f"raw/{request_id}/",
            "processed": False,
        }
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )
        
        load_job = bq.load_table_from_json([row], table_id, job_config=job_config)
        load_job.result()
        
        print(f"Successfully logged request to BigQuery (legacy table): {row['request_id']}")
    except Exception as e:
        print(f"Failed to log to BigQuery (legacy table): {e}")
