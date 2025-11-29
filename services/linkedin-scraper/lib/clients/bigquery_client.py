import json
import uuid
from datetime import datetime
from typing import List, Optional
from google.cloud import bigquery
from lib.gcloud_env_client import (
    BRIGHTDATA_DATASET_ID,
)


bq = bigquery.Client()

def get_unscraped_queries(limit: int = 10) -> List[dict]:
    """
    Fetch unscraped queries from request_queries table.
    
    Args:
        limit: Maximum number of queries to fetch
        
    Returns:
        List of query dictionaries with query_id and search parameters
    """
    try:
        query = f"""
        SELECT 
            query_id,
            location,
            keyword,
            country,
            time_range,
            job_type,
            remote,
            experience_level,
            company,
            location_radius
        FROM `sylvan-replica-478802-p4.brightdata_jobs.request_queries`
        WHERE scraped = FALSE
          AND (scheduled_for IS NULL OR scheduled_for <= CURRENT_TIMESTAMP())
        ORDER BY created_at ASC
        LIMIT {limit}
        """
        
        query_job = bq.query(query)
        results = query_job.result()
        
        queries = []
        for row in results:
            queries.append({
                "query_id": row.query_id,
                "location": row.location,
                "keyword": row.keyword,
                "country": row.country or "",
                "time_range": row.time_range or "",
                "job_type": row.job_type or "",
                "remote": row.remote or "",
                "experience_level": row.experience_level or "",
                "company": row.company or "",
                "location_radius": row.location_radius or "",
            })
        
        print(f"Found {len(queries)} unscraped queries")
        return queries
    except Exception as e:
        print(f"Failed to fetch unscraped queries: {e}")
        return []


def mark_queries_scraped(query_ids: List[str], scrape_request_id: str):
    """
    Mark queries as scraped in request_queries table.
    
    Args:
        query_ids: List of query IDs that were scraped
        scrape_request_id: The request_id from scraper_execution_logs
    """
    try:
        if not query_ids:
            return
        
        query_ids_str = "', '".join(query_ids)
        update_query = f"""
        UPDATE `sylvan-replica-478802-p4.brightdata_jobs.request_queries`
        SET 
            scraped = TRUE,
            scraped_at = CURRENT_TIMESTAMP(),
            scrape_request_id = '{scrape_request_id}'
        WHERE query_id IN ('{query_ids_str}')
        """
        
        bq.query(update_query).result()
        print(f"Marked {len(query_ids)} queries as scraped (request_id: {scrape_request_id})")
    except Exception as e:
        print(f"Failed to mark queries as scraped: {e}")


def log_request_to_bigquery(response_body, status, request_id):
    """
    Log scraper execution to BigQuery.
    
    Args:
        response_body: API response body
        status: HTTP status code
        request_id: Unique request identifier
    """
    try:
        table_id = "sylvan-replica-478802-p4.brightdata_jobs.scraper_execution_logs"
        
        if isinstance(response_body, str):
            response_json = response_body
        else:
            response_json = json.dumps(response_body)
        
        row = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "dataset_id": BRIGHTDATA_DATASET_ID,
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
        
        print(f"Successfully logged scrape execution to BigQuery: {row['request_id']}")
    except Exception as e:
        print(f"Failed to log scrape execution to BigQuery: {e}")