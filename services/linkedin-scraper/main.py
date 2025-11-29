import functions_framework
from lib import call_brightdata, JobSearchQuery
from lib.clients.bigquery_client import (
    get_unscraped_queries,
    mark_queries_scraped,
    log_request_to_bigquery,
)


@functions_framework.http
def main(request):
    """
    HTTP Cloud Function to scrape LinkedIn jobs via BrightData.
    
    Workflow:
    1. Get unscraped queries from request_queries table
    2. Call BrightData API with those queries
    3. Log execution to scraper_execution_logs
    4. Mark queries as scraped in request_queries
    """
    # Get unscraped queries from BigQuery
    query_records = get_unscraped_queries(limit=10)
    
    if not query_records:
        return {"message": "No unscraped queries found"}, 200, {"Content-Type": "application/json"}
    
    # Convert to JobSearchQuery objects
    queries = [
        JobSearchQuery(
            location=q["location"],
            keyword=q["keyword"],
            country=q.get("country", ""),
            time_range=q.get("time_range", ""),
            job_type=q.get("job_type", ""),
            remote=q.get("remote", ""),
            experience_level=q.get("experience_level", ""),
            company=q.get("company", ""),
            location_radius=q.get("location_radius", ""),
        )
        for q in query_records
    ]
    
    # Extract query_ids for later
    query_ids = [q["query_id"] for q in query_records]
    
    # Call BrightData API
    body, status, request_id, queries_dict = call_brightdata(queries=queries)
    
    # Log the scrape execution to BigQuery
    log_request_to_bigquery(body, status, request_id)
    
    # Mark queries as scraped
    mark_queries_scraped(query_ids, request_id)
    
    return body, status, {"Content-Type": "application/json"}
