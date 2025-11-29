#!/usr/bin/env python3
"""
Migration script to update request_queries table structure.

This script:
1. Checks if the table exists
2. If it has old schema, backs it up and recreates with new schema
3. If it doesn't exist, creates it with new schema

New schema includes:
- query_id (primary key instead of request_id+query_index)
- scraped, created_at, scheduled_for, scraped_at, scrape_request_id fields
"""

from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "sylvan-replica-478802-p4"
DATASET_ID = "brightdata_jobs"
TABLE_ID = "request_queries"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

def main():
    client = bigquery.Client(project=PROJECT_ID)
    
    print("="*60)
    print("Request Queries Table Migration")
    print("="*60)
    
    # Check if table exists
    try:
        table = client.get_table(FULL_TABLE_ID)
        print(f"\n✓ Table exists: {FULL_TABLE_ID}")
        print(f"  Created: {table.created}")
        print(f"  Rows: {table.num_rows}")
        
        # Check schema
        schema_fields = {field.name: field.field_type for field in table.schema}
        print("\n  Current fields:", ", ".join(sorted(schema_fields.keys())))
        
        has_query_id = "query_id" in schema_fields
        has_scraped = "scraped" in schema_fields
        
        if has_query_id and has_scraped:
            print("\n✓ Table already has correct schema!")
            return
        
        print("\n⚠ Table needs migration")
        
        # Backup old table if it has data
        if table.num_rows > 0:
            backup_table_id = f"{FULL_TABLE_ID}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"\n  Creating backup: {backup_table_id}")
            
            job = client.copy_table(FULL_TABLE_ID, backup_table_id)
            job.result()
            print(f"  ✓ Backup created")
        
        # Drop old table
        print(f"\n  Dropping old table...")
        client.delete_table(FULL_TABLE_ID)
        print(f"  ✓ Old table dropped")
        
    except Exception as e:
        if "Not found" in str(e):
            print(f"\n✓ Table doesn't exist yet: {FULL_TABLE_ID}")
        else:
            print(f"\n✗ Error checking table: {e}")
            return
    
    # Create new table with correct schema
    print(f"\n  Creating table with new schema...")
    
    schema = [
        # Primary key
        bigquery.SchemaField("query_id", "STRING", mode="REQUIRED", description="Unique identifier for this query"),
        
        # Search parameters
        bigquery.SchemaField("location", "STRING", mode="REQUIRED", description="Job location"),
        bigquery.SchemaField("keyword", "STRING", mode="REQUIRED", description="Search keyword"),
        bigquery.SchemaField("country", "STRING", mode="NULLABLE", description="Country code"),
        bigquery.SchemaField("time_range", "STRING", mode="NULLABLE", description="Time range for job postings"),
        bigquery.SchemaField("job_type", "STRING", mode="NULLABLE", description="Job type filter"),
        bigquery.SchemaField("remote", "STRING", mode="NULLABLE", description="Remote work filter"),
        bigquery.SchemaField("experience_level", "STRING", mode="NULLABLE", description="Experience level filter"),
        bigquery.SchemaField("company", "STRING", mode="NULLABLE", description="Company filter"),
        bigquery.SchemaField("location_radius", "STRING", mode="NULLABLE", description="Location search radius"),
        
        # Metadata
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="When query was created"),
        bigquery.SchemaField("created_by", "STRING", mode="NULLABLE", description="Who/what created this query"),
        
        # Scheduling
        bigquery.SchemaField("scheduled_for", "TIMESTAMP", mode="NULLABLE", description="When to scrape this query"),
        
        # Scraping status
        bigquery.SchemaField("scraped", "BOOLEAN", mode="REQUIRED", description="Whether this query has been scraped"),
        bigquery.SchemaField("scraped_at", "TIMESTAMP", mode="NULLABLE", description="When query was scraped"),
        bigquery.SchemaField("scrape_request_id", "STRING", mode="NULLABLE", description="Request ID from scraper_execution_logs"),
        
        # Error tracking
        bigquery.SchemaField("last_error", "STRING", mode="NULLABLE", description="Last error message if scraping failed"),
        bigquery.SchemaField("retry_count", "INTEGER", mode="NULLABLE", description="Number of retry attempts"),
    ]
    
    table = bigquery.Table(FULL_TABLE_ID, schema=schema)
    
    # Add partitioning and clustering
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="created_at"
    )
    table.clustering_fields = ["scraped", "location", "keyword"]
    
    table = client.create_table(table)
    
    print(f"  ✓ Table created successfully!")
    print(f"\n  Schema:")
    for field in table.schema:
        print(f"    - {field.name}: {field.field_type} ({'REQUIRED' if field.mode == 'REQUIRED' else 'NULLABLE'})")
    
    print(f"\n  Partitioning: {table.time_partitioning.field} (DAY)")
    print(f"  Clustering: {', '.join(table.clustering_fields)}")
    
    print("\n" + "="*60)
    print("✓ Migration complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Run seed_request_queries.py to populate with initial queries")
    print("  2. Test the scraper with: cd services/linkedin-scraper && python main.py")

if __name__ == "__main__":
    main()
