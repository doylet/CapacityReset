#!/usr/bin/env python3
"""Create etl_execution_logs table in BigQuery"""

from google.cloud import bigquery

client = bigquery.Client()

schema = [
    bigquery.SchemaField("log_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("execution_timestamp", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("status", "STRING", mode="REQUIRED"),  # success, error, partial
    bigquery.SchemaField("requests_processed", "INTEGER"),
    bigquery.SchemaField("requests_failed", "INTEGER"),
    bigquery.SchemaField("jobs_affected", "INTEGER"),
    bigquery.SchemaField("duration_seconds", "FLOAT64"),
    bigquery.SchemaField("error_message", "STRING"),
    bigquery.SchemaField("processed_request_ids", "STRING", mode="REPEATED"),
    bigquery.SchemaField("failed_request_ids", "STRING", mode="REPEATED"),
]

table_id = "sylvan-replica-478802-p4.brightdata_jobs.etl_execution_logs"

table = bigquery.Table(table_id, schema=schema)
table.time_partitioning = bigquery.TimePartitioning(
    type_=bigquery.TimePartitioningType.DAY,
    field="execution_timestamp",
)

table = client.create_table(table)
print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
