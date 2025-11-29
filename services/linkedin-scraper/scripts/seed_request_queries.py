#!/usr/bin/env python3
"""
Seed the request_queries table with initial search queries.

This populates the table with a set of starter queries that the scraper
will process automatically.
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
    print("Seeding Request Queries Table")
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
    
    # Prepare rows to insert
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
            "created_by": "seed_script",
            "scheduled_for": None,
            "scraped": False,
            "scraped_at": None,
            "scrape_request_id": None,
            "last_error": None,
            "retry_count": 0,
        }
        rows_to_insert.append(row)
    
    print(f"\n  Inserting {len(rows_to_insert)} queries...")
    
    # Insert rows
    errors = client.insert_rows_json(FULL_TABLE_ID, rows_to_insert)
    
    if errors:
        print(f"\n✗ Errors occurred:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n✓ Successfully inserted {len(rows_to_insert)} queries!")
        
        # Show sample of what was inserted
        print("\n  Sample queries:")
        for row in rows_to_insert[:3]:
            print(f"    - {row['location']}: {row['keyword']}")
        if len(rows_to_insert) > 3:
            print(f"    ... and {len(rows_to_insert) - 3} more")
    
    # Verify
    query = f"SELECT COUNT(*) as count FROM `{FULL_TABLE_ID}` WHERE scraped = FALSE"
    result = list(client.query(query).result())[0]
    
    print(f"\n  Unscraped queries in table: {result['count']}")
    
    print("\n" + "="*60)
    print("✓ Seeding complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Test the scraper: cd services/linkedin-scraper && python main.py")
    print("  2. Monitor execution: Check scraper_execution_logs table")
    print("  3. Check results: Query request_queries WHERE scraped = TRUE")

if __name__ == "__main__":
    main()
