#!/usr/bin/env python3
"""
Reset existing queries to unscraped status to trigger the scraper
"""
from google.cloud import bigquery
from datetime import datetime

def reset_queries_to_unscraped():
    client = bigquery.Client(project='sylvan-replica-478802-p4')
    
    # Reset the existing queries to unscraped status
    reset_query = """
    UPDATE `sylvan-replica-478802-p4.brightdata_jobs.request_queries`
    SET 
        scraped = FALSE,
        scraped_at = NULL,
        scrape_request_id = NULL,
        last_error = NULL,
        retry_count = 0
    WHERE scraped = TRUE
    """
    
    print("Resetting scraped queries to unscraped status...")
    job = client.query(reset_query)
    job.result()  # Wait for completion
    
    print(f"✓ Reset {job.num_dml_affected_rows} queries to unscraped status")
    
    # Verify the reset
    check_query = """
    SELECT 
        COUNT(*) as total_queries,
        COUNT(CASE WHEN scraped = FALSE THEN 1 END) as unscraped_queries,
        COUNT(CASE WHEN scraped = TRUE THEN 1 END) as scraped_queries
    FROM `sylvan-replica-478802-p4.brightdata_jobs.request_queries`
    """
    
    results = client.query(check_query).result()
    for row in results:
        print(f"Total queries: {row.total_queries}")
        print(f"Unscraped: {row.unscraped_queries}")
        print(f"Scraped: {row.scraped_queries}")

if __name__ == "__main__":
    reset_queries_to_unscraped()