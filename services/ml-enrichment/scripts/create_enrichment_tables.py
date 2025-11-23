"""
Create BigQuery tables for ML enrichment tracking and storage.

This script creates:
1. job_enrichments - Polymorphic tracking table for all enrichment types
2. job_skills - Extracted skills, tools, technologies from job postings
3. job_embeddings - Vector embeddings for semantic search
"""

from google.cloud import bigquery

def create_enrichment_tables(project_id: str = "sylvan-replica-478802-p4"):
    """Create all ML enrichment tables with proper schemas."""
    client = bigquery.Client(project=project_id)
    dataset_id = f"{project_id}.brightdata_jobs"
    
    # 1. Polymorphic enrichment tracking table
    enrichments_table_id = f"{dataset_id}.job_enrichments"
    enrichments_schema = [
        bigquery.SchemaField("enrichment_id", "STRING", mode="REQUIRED", description="UUID for this enrichment record"),
        bigquery.SchemaField("job_posting_id", "STRING", mode="REQUIRED", description="Reference to job_postings table"),
        bigquery.SchemaField("enrichment_type", "STRING", mode="REQUIRED", description="Type: skills_extraction, embeddings, salary_prediction, etc."),
        bigquery.SchemaField("enrichment_version", "STRING", mode="REQUIRED", description="Version/model identifier for reprocessing tracking"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="When enrichment was performed"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED", description="success, failed, partial"),
        bigquery.SchemaField("metadata", "JSON", mode="NULLABLE", description="Type-specific metadata (model, confidence, errors, etc.)"),
        bigquery.SchemaField("error_message", "STRING", mode="NULLABLE", description="Error details if status=failed"),
    ]
    
    enrichments_table = bigquery.Table(enrichments_table_id, schema=enrichments_schema)
    enrichments_table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="created_at"
    )
    enrichments_table.clustering_fields = ["enrichment_type", "job_posting_id", "status"]
    
    enrichments_table = client.create_table(enrichments_table, exists_ok=True)
    print(f"Created table {enrichments_table_id}")
    
    # 2. Skills extraction results table
    skills_table_id = f"{dataset_id}.job_skills"
    skills_schema = [
        bigquery.SchemaField("skill_id", "STRING", mode="REQUIRED", description="UUID for this skill record"),
        bigquery.SchemaField("job_posting_id", "STRING", mode="REQUIRED", description="Reference to job_postings table"),
        bigquery.SchemaField("enrichment_id", "STRING", mode="REQUIRED", description="Reference to job_enrichments table"),
        bigquery.SchemaField("skill_name", "STRING", mode="REQUIRED", description="Normalized skill name"),
        bigquery.SchemaField("skill_category", "STRING", mode="NULLABLE", description="Category: programming_language, framework, tool, soft_skill, etc."),
        bigquery.SchemaField("source_field", "STRING", mode="REQUIRED", description="Where extracted from: job_summary, job_description_formatted, etc."),
        bigquery.SchemaField("confidence_score", "FLOAT64", mode="NULLABLE", description="Extraction confidence 0.0-1.0"),
        bigquery.SchemaField("context_snippet", "STRING", mode="NULLABLE", description="Surrounding text for verification"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="When skill was extracted"),
    ]
    
    skills_table = bigquery.Table(skills_table_id, schema=skills_schema)
    skills_table.clustering_fields = ["job_posting_id", "skill_category", "skill_name"]
    
    skills_table = client.create_table(skills_table, exists_ok=True)
    print(f"Created table {skills_table_id}")
    
    # 3. Vector embeddings table
    embeddings_table_id = f"{dataset_id}.job_embeddings"
    embeddings_schema = [
        bigquery.SchemaField("embedding_id", "STRING", mode="REQUIRED", description="UUID for this embedding record"),
        bigquery.SchemaField("job_posting_id", "STRING", mode="REQUIRED", description="Reference to job_postings table"),
        bigquery.SchemaField("enrichment_id", "STRING", mode="REQUIRED", description="Reference to job_enrichments table"),
        bigquery.SchemaField("chunk_id", "INTEGER", mode="REQUIRED", description="Chunk sequence number for this job"),
        bigquery.SchemaField("chunk_type", "STRING", mode="REQUIRED", description="Type: full_description, responsibilities, requirements, benefits, etc."),
        bigquery.SchemaField("content", "STRING", mode="REQUIRED", description="The text that was embedded"),
        bigquery.SchemaField("content_tokens", "INTEGER", mode="NULLABLE", description="Approximate token count"),
        bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED", description="Vector embedding (768 dimensions for text-embedding-004)"),
        bigquery.SchemaField("model_version", "STRING", mode="REQUIRED", description="Embedding model used: text-embedding-004, etc."),
        bigquery.SchemaField("metadata", "JSON", mode="NULLABLE", description="Job context: title, company, location for filtering"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="When embedding was generated"),
    ]
    
    embeddings_table = bigquery.Table(embeddings_table_id, schema=embeddings_schema)
    embeddings_table.clustering_fields = ["job_posting_id", "chunk_type"]
    
    embeddings_table = client.create_table(embeddings_table, exists_ok=True)
    print(f"Created table {embeddings_table_id}")
    
    print("\n✅ All enrichment tables created successfully!")
    print("\nBenefits of this architecture:")
    print("- job_postings remains clean and independent")
    print("- Track multiple enrichment versions per job")
    print("- Easy to reprocess with new models")
    print("- Query enrichment status without joining large tables")
    print("- Add new enrichment types without schema changes")
    print("\nExample query to find jobs needing skills extraction:")
    print("""
    SELECT jp.job_posting_id, jp.job_title, jp.company_name
    FROM `brightdata_jobs.job_postings` jp
    LEFT JOIN `brightdata_jobs.job_enrichments` je
      ON jp.job_posting_id = je.job_posting_id
      AND je.enrichment_type = 'skills_extraction'
      AND je.status = 'success'
    WHERE je.enrichment_id IS NULL
    LIMIT 100
    """)

if __name__ == "__main__":
    create_enrichment_tables()
