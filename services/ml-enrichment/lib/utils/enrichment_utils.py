"""
Enrichment utilities for ML service.

Handles querying jobs, logging enrichments, and orchestrating processing.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.cloud import bigquery, logging as cloud_logging

# Initialize clients
bigquery_client = bigquery.Client()
logging_client = cloud_logging.Client()
logger = logging_client.logger("ml-enrichment")

PROJECT_ID = "sylvan-replica-478802-p4"
DATASET_ID = f"{PROJECT_ID}.brightdata_jobs"


def get_jobs_needing_enrichment(enrichment_type: str, limit: int = 50, enrichment_version: str = None) -> List[Dict[str, Any]]:
    """
    Query jobs that need enrichment of specified type and version.
    
    Args:
        enrichment_type: 'skills_extraction', 'embeddings', or 'job_clustering'
        limit: Maximum number of jobs to process
        enrichment_version: Optional version to check (e.g., 'v2.0-unsupervised-ner-lexicon')
                          If None, checks for any successful enrichment of that type
        
    Returns:
        List of job records with job_posting_id, job_title, job_summary, job_description_formatted
    """
    # Build version filter if specified
    version_filter = f"AND je.enrichment_version = '{enrichment_version}'" if enrichment_version else ""
    
    query = f"""
    SELECT 
        jp.job_posting_id,
        jp.job_title,
        jp.company_name,
        jp.job_location,
        jp.job_summary,
        jp.job_description_formatted,
        jp.job_posted_date
    FROM `{DATASET_ID}.job_postings` jp
    LEFT JOIN `{DATASET_ID}.job_enrichments` je
        ON jp.job_posting_id = je.job_posting_id
        AND je.enrichment_type = '{enrichment_type}'
        AND je.status = 'success'
        {version_filter}
    WHERE je.enrichment_id IS NULL
        AND jp.job_summary IS NOT NULL
        AND jp.job_description_formatted IS NOT NULL
    ORDER BY jp.job_posted_date DESC
    LIMIT {limit}
    """
    
    query_job = bigquery_client.query(query)
    results = query_job.result()
    
    jobs = []
    for row in results:
        jobs.append({
            'job_posting_id': row['job_posting_id'],
            'job_title': row['job_title'],
            'company_name': row['company_name'],
            'job_location': row['job_location'],
            'job_summary': row['job_summary'],
            'job_description_formatted': row['job_description_formatted'],
            'job_posted_date': row['job_posted_date']
        })
    
    return jobs


def log_enrichment(
    job_posting_id: str,
    enrichment_type: str,
    enrichment_version: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> str:
    """
    Log enrichment to job_enrichments table.
    
    Args:
        job_posting_id: Reference to job
        enrichment_type: Type of enrichment
        enrichment_version: Model/version identifier
        status: 'success', 'failed', or 'partial'
        metadata: Type-specific metadata
        error_message: Error details if failed
        
    Returns:
        enrichment_id UUID
    """
    enrichment_id = str(uuid.uuid4())
    
    row = {
        'enrichment_id': enrichment_id,
        'job_posting_id': job_posting_id,
        'enrichment_type': enrichment_type,
        'enrichment_version': enrichment_version,
        'created_at': datetime.utcnow().isoformat(),
        'status': status,
        'metadata': json.dumps(metadata) if metadata else None,
        'error_message': error_message
    }
    
    table_id = f"{DATASET_ID}.job_enrichments"
    errors = bigquery_client.insert_rows_json(table_id, [row])
    
    if errors:
        logger.log_text(f"Failed to log enrichment: {errors}", severity="ERROR")
        raise Exception(f"Failed to log enrichment: {errors}")
    
    return enrichment_id


def get_jobs_needing_reenrichment(
    enrichment_type: str,
    current_version: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Query jobs that have older enrichment versions and need re-enrichment.
    
    This finds jobs that have been enriched with an older version and need
    to be re-processed with the current model version.
    
    Args:
        enrichment_type: 'skills_extraction', 'embeddings', or 'job_clustering'
        current_version: The current model version (e.g., 'v4.0-unified-config-enhanced')
        limit: Maximum number of jobs to return
        
    Returns:
        List of job records with old enrichment info
    """
    query = f"""
    SELECT 
        jp.job_posting_id,
        jp.job_title,
        jp.company_name,
        jp.job_location,
        jp.job_summary,
        jp.job_description_formatted,
        jp.job_posted_date,
        je.enrichment_version AS old_version,
        je.created_at AS enriched_at
    FROM `{DATASET_ID}.job_postings` jp
    INNER JOIN `{DATASET_ID}.job_enrichments` je
        ON jp.job_posting_id = je.job_posting_id
        AND je.enrichment_type = '{enrichment_type}'
        AND je.status = 'success'
    WHERE je.enrichment_version != '{current_version}'
        AND je.enrichment_version IS NOT NULL
        AND jp.job_summary IS NOT NULL
        AND jp.job_description_formatted IS NOT NULL
    ORDER BY jp.job_posted_date DESC
    LIMIT {limit}
    """
    
    query_job = bigquery_client.query(query)
    results = query_job.result()
    
    jobs = []
    for row in results:
        jobs.append({
            'job_posting_id': row['job_posting_id'],
            'job_title': row['job_title'],
            'company_name': row['company_name'],
            'job_location': row['job_location'],
            'job_summary': row['job_summary'],
            'job_description_formatted': row['job_description_formatted'],
            'job_posted_date': row['job_posted_date'],
            'old_version': row['old_version'],
            'enriched_at': row['enriched_at']
        })
    
    return jobs


def get_enrichment_version_stats(enrichment_type: str) -> Dict[str, Any]:
    """
    Get statistics about enrichment versions in use.
    
    Args:
        enrichment_type: 'skills_extraction', 'embeddings', or 'job_clustering'
        
    Returns:
        Dictionary with version counts and statistics
    """
    query = f"""
    SELECT 
        COALESCE(enrichment_version, 'legacy') AS version,
        COUNT(*) AS count,
        MIN(created_at) AS first_enriched,
        MAX(created_at) AS last_enriched
    FROM `{DATASET_ID}.job_enrichments`
    WHERE enrichment_type = '{enrichment_type}'
        AND status = 'success'
    GROUP BY version
    ORDER BY count DESC
    """
    
    query_job = bigquery_client.query(query)
    results = query_job.result()
    
    versions = []
    total = 0
    for row in results:
        versions.append({
            'version': row['version'],
            'count': row['count'],
            'first_enriched': row['first_enriched'],
            'last_enriched': row['last_enriched']
        })
        total += row['count']
    
    return {
        'enrichment_type': enrichment_type,
        'total_enrichments': total,
        'versions': versions
    }


def get_logger():
    """Get Cloud Logging logger instance."""
    return logger
