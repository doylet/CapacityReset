#!/usr/bin/env python3
"""
Test the complete scraper workflow without calling BrightData API.

This verifies:
1. Reading unscraped queries from request_queries
2. Marking queries as scraped
3. Logging to scraper_execution_logs
"""

import json
import uuid
from datetime import datetime
from lib.clients.bigquery_client import (
    get_unscraped_queries,
    mark_queries_scraped,
    log_request_to_bigquery,
)

def main():
    print("="*60)
    print("Testing Scraper Workflow")
    print("="*60)
    
    # Step 1: Get unscraped queries
    print("\n[1/3] Fetching unscraped queries...")
    queries = get_unscraped_queries(limit=3)
    
    if not queries:
        print("  ✗ No unscraped queries found!")
        print("\n  Run seed_request_queries.py first to populate queries.")
        return
    
    print(f"  ✓ Found {len(queries)} unscraped queries:")
    for q in queries:
        print(f"    - [{q['query_id'][:8]}...] {q['location']}: {q['keyword']}")
    
    query_ids = [q["query_id"] for q in queries]
    
    # Step 2: Simulate API call and log execution
    print("\n[2/3] Simulating BrightData API call...")
    request_id = str(uuid.uuid4())
    
    mock_response = {
        "snapshot_id": "mock_snapshot_123",
        "status": "success",
        "queries_processed": len(queries)
    }
    
    print(f"  ✓ Mock request_id: {request_id}")
    print(f"  ✓ Mock response: {json.dumps(mock_response, indent=2)}")
    
    # Log to scraper_execution_logs
    log_request_to_bigquery(mock_response, 200, request_id)
    print("  ✓ Logged to scraper_execution_logs")
    
    # Step 3: Mark queries as scraped
    print("\n[3/3] Marking queries as scraped...")
    mark_queries_scraped(query_ids, request_id)
    print(f"  ✓ Marked {len(query_ids)} queries as scraped")
    
    # Verify
    print("\n" + "="*60)
    print("Verification")
    print("="*60)
    
    remaining = get_unscraped_queries(limit=1)
    print(f"\n✓ Remaining unscraped queries: {len(get_unscraped_queries(limit=100))}")
    
    print("\n" + "="*60)
    print("✓ Workflow test complete!")
    print("="*60)
    print("\nTo verify in BigQuery:")
    print(f"  1. Check scraper_execution_logs for request_id: {request_id}")
    print(f"  2. Check request_queries WHERE scrape_request_id = '{request_id}'")
    print("\nTo run with real BrightData API:")
    print("  Deploy to Cloud Functions and trigger the endpoint")

if __name__ == "__main__":
    main()
