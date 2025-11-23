#!/usr/bin/env python3
"""Rename scrape_requests to scraper_execution_logs"""

from google.cloud import bigquery

client = bigquery.Client()
project_id = "sylvan-replica-478802-p4"

# Copy table
source_table = f"{project_id}.brightdata_jobs.scrape_requests"
dest_table = f"{project_id}.brightdata_jobs.scraper_execution_logs"

print(f"Copying {source_table} to {dest_table}...")
job = client.copy_table(source_table, dest_table)
job.result()

print(f"Successfully copied table")
print(f"Old table {source_table} still exists - delete manually after verification")
