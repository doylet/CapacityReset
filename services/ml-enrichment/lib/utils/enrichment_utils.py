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


def get_logger():
    """Get Cloud Logging logger instance."""
    return logger


def get_jobs_by_version(
    enrichment_type: str,
    enrichment_version: str,
    limit: int = 100,
    status: str = 'success'
) -> List[Dict[str, Any]]:
    """
    Query jobs that have a specific enrichment version.
    
    This function supports version-based analysis and comparison workflows.
    
    Args:
        enrichment_type: Type of enrichment ('skills_extraction', 'embeddings', etc.)
        enrichment_version: The version to filter by
        limit: Maximum number of jobs to return
        status: Enrichment status to filter by (default: 'success')
        
    Returns:
        List of job records with their enrichment metadata
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
        je.enrichment_id,
        je.enrichment_version,
        je.status,
        je.created_at AS enrichment_date,
        je.metadata
    FROM `{DATASET_ID}.job_postings` jp
    INNER JOIN `{DATASET_ID}.job_enrichments` je
        ON jp.job_posting_id = je.job_posting_id
        AND je.enrichment_type = '{enrichment_type}'
        AND je.status = '{status}'
        AND je.enrichment_version = '{enrichment_version}'
    ORDER BY je.created_at DESC
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
            'enrichment_id': row['enrichment_id'],
            'enrichment_version': row['enrichment_version'],
            'enrichment_date': row['enrichment_date'],
            'metadata': row['metadata']
        })
    
    return jobs


def get_version_distribution(enrichment_type: str) -> List[Dict[str, Any]]:
    """
    Get distribution of enrichment versions for a type.
    
    Args:
        enrichment_type: Type of enrichment to analyze
        
    Returns:
        List of version counts with statistics
    """
    query = f"""
    SELECT 
        COALESCE(enrichment_version, 'legacy') AS version,
        COUNT(*) AS enrichment_count,
        COUNTIF(status = 'success') AS success_count,
        COUNTIF(status = 'failed') AS failed_count,
        MIN(created_at) AS first_enriched,
        MAX(created_at) AS last_enriched
    FROM `{DATASET_ID}.job_enrichments`
    WHERE enrichment_type = '{enrichment_type}'
    GROUP BY enrichment_version
    ORDER BY enrichment_count DESC
    """
    
    query_job = bigquery_client.query(query)
    results = query_job.result()
    
    distribution = []
    for row in results:
        distribution.append({
            'version': row['version'],
            'enrichment_count': row['enrichment_count'],
            'success_count': row['success_count'],
            'failed_count': row['failed_count'],
            'first_enriched': row['first_enriched'],
            'last_enriched': row['last_enriched']
        })
    
    return distribution


def get_jobs_needing_reenrichment(
    enrichment_type: str,
    target_version: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Query jobs that need re-enrichment for a target version.
    
    Returns jobs that either:
    1. Have no enrichment of the specified type
    2. Have enrichment with a different version
    3. Have failed enrichment
    
    Args:
        enrichment_type: Type of enrichment to check
        target_version: The target version to re-enrich to
        limit: Maximum number of jobs to return
        
    Returns:
        List of job records needing re-enrichment
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
        je.enrichment_version AS current_version,
        je.status AS current_status,
        je.created_at AS last_enriched_at
    FROM `{DATASET_ID}.job_postings` jp
    LEFT JOIN `{DATASET_ID}.job_enrichments` je
        ON jp.job_posting_id = je.job_posting_id
        AND je.enrichment_type = '{enrichment_type}'
        AND je.status = 'success'
        AND je.enrichment_version = '{target_version}'
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
            'job_posted_date': row['job_posted_date'],
            'current_version': row['current_version'],
            'current_status': row['current_status'],
            'last_enriched_at': row['last_enriched_at']
        })
    
    return jobs


def add_enrichment_version_field(
    enrichment_data: Dict[str, Any],
    model_id: str,
    model_version: str
) -> Dict[str, Any]:
    """
    Add version tracking fields to enrichment data.
    
    This helper function ensures consistent version field naming
    and format across all enrichment storage operations.
    
    Args:
        enrichment_data: The enrichment data dictionary to augment
        model_id: The model identifier (e.g., 'skills_extractor')
        model_version: The model version string (e.g., 'v4.0-unified-config-enhanced')
        
    Returns:
        Enrichment data with version fields added
    """
    enrichment_data['model_id'] = model_id
    enrichment_data['model_version'] = model_version
    enrichment_data['enrichment_version'] = f"{model_id}_{model_version}"
    
    return enrichment_data
