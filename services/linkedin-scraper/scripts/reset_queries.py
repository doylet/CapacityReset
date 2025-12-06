#!/usr/bin/env python3
"""
Reset existing queries to unscraped status
"""
from google.cloud import bigquery

def reset_queries_to_unscraped():
    client = bigquery.Client(project='sylvan-replica-478802-p4')
    
    # Reset the existing queries to unscraped status
    query = """
    UPDATE `sylvan-replica-478802-p4.brightdata_jobs.request_queries`
    SET 
        scraped = FALSE,
        scraped_at = NULL,
        scrape_request_id = NULL,
        last_error = NULL
    WHERE scraped = TRUE
    """
    
    job = client.query(query)
    result = job.result()
    
    print(f'Successfully reset {job.num_dml_affected_rows} queries to unscraped status')
    
    # Show what queries are now available
    check_query = """
    SELECT query_id, location, keyword, scraped 
    FROM `sylvan-replica-478802-p4.brightdata_jobs.request_queries`
    ORDER BY created_at DESC
    """
    
    results = client.query(check_query).result()
    print('\nAvailable queries:')
    for row in results:
        status = '✓ scraped' if row.scraped else '○ unscraped'
        print(f'  {status} {row.location}: {row.keyword}')

if __name__ == "__main__":
    reset_queries_to_unscraped()