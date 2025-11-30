#!/usr/bin/env python3
"""
Reset and re-seed the request_queries table.

This script:
1. Deletes all existing rows from the table
2. Re-seeds with fresh queries from SEED_QUERIES

WARNING: This will delete ALL existing data in the table!
"""

from google.cloud import bigquery
from datetime import datetime
import uuid

PROJECT_ID = "sylvan-replica-478802-p4"
DATASET_ID = "brightdata_jobs"
TABLE_ID = "request_queries"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Initial seed queries - Product Management roles in Australian cities
SEED_QUERIES = [
    {"location": "brisbane", "keyword": '"product management"', "country": "AU"},
    {"location": "sydney", "keyword": '"product management"', "country": "AU"},
    {"location": "melbourne", "keyword": '"product management"', "country": "AU"},
]

def main():
    client = bigquery.Client(project=PROJECT_ID)
    
    print("="*60)
    print("RESET AND RE-SEED Request Queries Table")
    print("="*60)
    
    # Check if table exists
    try:
        table = client.get_table(FULL_TABLE_ID)
        print(f"\n✓ Table exists: {FULL_TABLE_ID}")
        print(f"  Current rows: {table.num_rows}")
    except Exception as e:
        print(f"\n✗ Table doesn't exist: {e}")
        print("\nPlease run migrate_request_queries_table.py first!")
        return
    
    # Show current data before deletion
    if table.num_rows > 0:
        query = f"""
        SELECT 
            COUNT(*) as total,
            COUNTIF(scraped = TRUE) as scraped,
            COUNTIF(scraped = FALSE) as unscraped
        FROM `{FULL_TABLE_ID}`
        """
        result = list(client.query(query).result())[0]
        print(f"\n  Current data:")
        print(f"    Total: {result['total']}")
        print(f"    Scraped: {result['scraped']}")
        print(f"    Unscraped: {result['unscraped']}")
    
    # Confirm deletion
    print("\n⚠️  WARNING: This will DELETE ALL existing data!")
    response = input("  Type 'YES' to continue: ")
    
    if response != "YES":
        print("\n✗ Operation cancelled.")
        return
    
    # Step 1: Delete all existing rows
    print(f"\n  Deleting all rows from table...")
    delete_query = f"DELETE FROM `{FULL_TABLE_ID}` WHERE TRUE"
    delete_job = client.query(delete_query)
    delete_job.result()
    
    print(f"  ✓ All rows deleted")
    
    # Step 2: Insert new seed data
    timestamp = datetime.utcnow().isoformat()
    rows_to_insert = []
    
    for query in SEED_QUERIES:
        row = {
            "query_id": str(uuid.uuid4()),
            "location": query["location"],
            "keyword": query["keyword"],
            "country": query.get("country"),
            "time_range": query.get("time_range"),
            "job_type": query.get("job_type"),
            "remote": query.get("remote"),
            "experience_level": query.get("experience_level"),
            "company": query.get("company"),
            "location_radius": query.get("location_radius"),
            "created_at": timestamp,
            "created_by": "reset_script",
            "scheduled_for": None,
            "scraped": False,
            "scraped_at": None,
            "scrape_request_id": None,
            "last_error": None,
            "retry_count": 0,
        }
        rows_to_insert.append(row)
    
    print(f"\n  Inserting {len(rows_to_insert)} fresh queries...")
    
    # Insert rows
    errors = client.insert_rows_json(FULL_TABLE_ID, rows_to_insert)
    
    if errors:
        print(f"\n✗ Errors occurred during insertion:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n✓ Successfully inserted {len(rows_to_insert)} queries!")
        
        # Show what was inserted
        print("\n  Inserted queries:")
        for row in rows_to_insert:
            print(f"    - {row['location']}: {row['keyword']}")
    
    # Verify final state
    verify_query = f"""
    SELECT 
        COUNT(*) as total,
        COUNTIF(scraped = FALSE) as unscraped
    FROM `{FULL_TABLE_ID}`
    """
    result = list(client.query(verify_query).result())[0]
    
    print(f"\n  Final state:")
    print(f"    Total rows: {result['total']}")
    print(f"    Unscraped: {result['unscraped']}")
    
    print("\n" + "="*60)
    print("✓ Reset and re-seed complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Test the scraper: cd services/linkedin-scraper && python main.py")
    print("  2. Monitor execution: Check scraper_execution_logs table")
    print("  3. Check results: Query request_queries WHERE scraped = TRUE")

if __name__ == "__main__":
    main()
