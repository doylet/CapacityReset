"""
Create BigQuery table for job clustering results.
"""

from google.cloud import bigquery

def create_clusters_table(project_id: str = "sylvan-replica-478802-p4"):
    """Create job_clusters table for storing clustering results."""
    client = bigquery.Client(project=project_id)
    dataset_id = f"{project_id}.brightdata_jobs"
    
    table_id = f"{dataset_id}.job_clusters"
    schema = [
        bigquery.SchemaField("cluster_assignment_id", "STRING", mode="REQUIRED", description="UUID for this cluster assignment"),
        bigquery.SchemaField("job_posting_id", "STRING", mode="REQUIRED", description="Reference to job_postings table"),
        bigquery.SchemaField("enrichment_id", "STRING", mode="REQUIRED", description="Reference to job_enrichments table"),
        bigquery.SchemaField("cluster_id", "INTEGER", mode="REQUIRED", description="Cluster number (0 to n_clusters-1)"),
        bigquery.SchemaField("cluster_name", "STRING", mode="REQUIRED", description="Human-readable cluster name from keywords"),
        bigquery.SchemaField("cluster_keywords", "JSON", mode="NULLABLE", description="Top keywords defining this cluster with TF-IDF scores"),
        bigquery.SchemaField("cluster_size", "INTEGER", mode="NULLABLE", description="Total number of jobs in this cluster"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="When clustering was performed"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.clustering_fields = ["cluster_id", "job_posting_id"]
    
    table = client.create_table(table, exists_ok=True)
    print(f"Created table {table_id}")
    
    print("\n✅ Job clusters table created successfully!")
    print("\nExample query to see clusters:")
    print("""
    SELECT 
        cluster_id,
        cluster_name,
        cluster_size,
        COUNT(DISTINCT job_posting_id) as jobs_in_cluster,
        ARRAY_AGG(DISTINCT jp.job_title LIMIT 5) as sample_titles
    FROM `brightdata_jobs.job_clusters` jc
    JOIN `brightdata_jobs.job_postings` jp
        ON jc.job_posting_id = jp.job_posting_id
    GROUP BY cluster_id, cluster_name, cluster_size
    ORDER BY cluster_size DESC
    """)

if __name__ == "__main__":
    create_clusters_table()
