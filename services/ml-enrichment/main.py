"""
ML Enrichment Service for LinkedIn Job Postings

This Cloud Run service enriches job postings with:
1. Skills extraction (from job_summary and job_description_formatted)
2. Vector embeddings (for semantic search)

Architecture:
- Reads unenriched jobs from job_postings
- Tracks enrichment status in job_enrichments (polymorphic)
- Stores results in job_skills and job_embeddings
- Maintains loose coupling with job_postings table
"""

import functions_framework
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.cloud import bigquery, logging as cloud_logging
from lib.enrichment.skills_extractor import SkillsExtractor
from lib.enrichment.embeddings_generator import EmbeddingsGenerator

# Initialize clients
bigquery_client = bigquery.Client()
logging_client = cloud_logging.Client()
logger = logging_client.logger("ml-enrichment")

# Initialize enrichment modules
skills_extractor = SkillsExtractor()
embeddings_generator = EmbeddingsGenerator()

PROJECT_ID = "sylvan-replica-478802-p4"
DATASET_ID = f"{PROJECT_ID}.brightdata_jobs"


def get_jobs_needing_enrichment(enrichment_type: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Query jobs that need enrichment of specified type.
    
    Args:
        enrichment_type: 'skills_extraction' or 'embeddings'
        limit: Maximum number of jobs to process
        
    Returns:
        List of job records with job_posting_id, job_title, job_summary, job_description_formatted
    """
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


def process_skills_extraction(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract skills from job postings.
    
    Args:
        jobs: List of job records
        
    Returns:
        Statistics: processed, failed, total_skills
    """
    processed = 0
    failed = 0
    total_skills = 0
    
    for job in jobs:
        try:
            # Extract skills from both job_summary and job_description_formatted
            skills = skills_extractor.extract_skills(
                job_summary=job['job_summary'],
                job_description=job['job_description_formatted']
            )
            
            if skills:
                # Log successful enrichment
                enrichment_id = log_enrichment(
                    job_posting_id=job['job_posting_id'],
                    enrichment_type='skills_extraction',
                    enrichment_version=skills_extractor.get_version(),
                    status='success',
                    metadata={
                        'skills_count': len(skills),
                        'source_fields': ['job_summary', 'job_description_formatted']
                    }
                )
                
                # Store skills in job_skills table
                skills_extractor.store_skills(
                    job_posting_id=job['job_posting_id'],
                    enrichment_id=enrichment_id,
                    skills=skills
                )
                
                processed += 1
                total_skills += len(skills)
            else:
                # Log as partial - no skills found
                log_enrichment(
                    job_posting_id=job['job_posting_id'],
                    enrichment_type='skills_extraction',
                    enrichment_version=skills_extractor.get_version(),
                    status='partial',
                    metadata={'skills_count': 0, 'reason': 'no_skills_found'}
                )
                processed += 1
                
        except Exception as e:
            logger.log_text(
                f"Skills extraction failed for job {job['job_posting_id']}: {str(e)}",
                severity="ERROR"
            )
            log_enrichment(
                job_posting_id=job['job_posting_id'],
                enrichment_type='skills_extraction',
                enrichment_version=skills_extractor.get_version(),
                status='failed',
                error_message=str(e)
            )
            failed += 1
    
    return {
        'processed': processed,
        'failed': failed,
        'total_skills': total_skills
    }


def process_embeddings(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate vector embeddings for job descriptions.
    
    Args:
        jobs: List of job records
        
    Returns:
        Statistics: processed, failed, total_embeddings
    """
    processed = 0
    failed = 0
    total_embeddings = 0
    
    for job in jobs:
        try:
            # Generate embeddings with intelligent chunking
            embeddings = embeddings_generator.generate_embeddings(
                job_posting_id=job['job_posting_id'],
                job_description=job['job_description_formatted'],
                metadata={
                    'job_title': job['job_title'],
                    'company_name': job['company_name'],
                    'job_location': job['job_location']
                }
            )
            
            if embeddings:
                # Log successful enrichment
                enrichment_id = log_enrichment(
                    job_posting_id=job['job_posting_id'],
                    enrichment_type='embeddings',
                    enrichment_version=embeddings_generator.get_version(),
                    status='success',
                    metadata={
                        'chunks_count': len(embeddings),
                        'model': embeddings_generator.get_model_name()
                    }
                )
                
                # Store embeddings in job_embeddings table
                embeddings_generator.store_embeddings(
                    job_posting_id=job['job_posting_id'],
                    enrichment_id=enrichment_id,
                    embeddings=embeddings
                )
                
                processed += 1
                total_embeddings += len(embeddings)
            else:
                # Log as failed - no embeddings generated
                log_enrichment(
                    job_posting_id=job['job_posting_id'],
                    enrichment_type='embeddings',
                    enrichment_version=embeddings_generator.get_version(),
                    status='failed',
                    error_message='No embeddings generated'
                )
                failed += 1
                
        except Exception as e:
            logger.log_text(
                f"Embeddings generation failed for job {job['job_posting_id']}: {str(e)}",
                severity="ERROR"
            )
            log_enrichment(
                job_posting_id=job['job_posting_id'],
                enrichment_type='embeddings',
                enrichment_version=embeddings_generator.get_version(),
                status='failed',
                error_message=str(e)
            )
            failed += 1
    
    return {
        'processed': processed,
        'failed': failed,
        'total_embeddings': total_embeddings
    }


@functions_framework.http
def main(request):
    """
    HTTP Cloud Function to run ML enrichment on job postings.
    
    Request body (optional):
        {
            "enrichment_types": ["skills_extraction", "embeddings"],  # defaults to both
            "batch_size": 50  # defaults to 50
        }
    
    Response:
        {
            "status": "success",
            "skills_extraction": {"processed": 10, "failed": 0, "total_skills": 45},
            "embeddings": {"processed": 10, "failed": 0, "total_embeddings": 30},
            "execution_time_seconds": 12.5
        }
    """
    start_time = datetime.utcnow()
    
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        enrichment_types = request_json.get('enrichment_types', ['skills_extraction', 'embeddings'])
        batch_size = request_json.get('batch_size', 50)
        
        logger.log_text(
            f"Starting ML enrichment: types={enrichment_types}, batch_size={batch_size}",
            severity="INFO"
        )
        
        results = {}
        
        # Process skills extraction
        if 'skills_extraction' in enrichment_types:
            jobs = get_jobs_needing_enrichment('skills_extraction', batch_size)
            logger.log_text(f"Found {len(jobs)} jobs needing skills extraction", severity="INFO")
            
            if jobs:
                skills_stats = process_skills_extraction(jobs)
                results['skills_extraction'] = skills_stats
                logger.log_text(f"Skills extraction complete: {skills_stats}", severity="INFO")
            else:
                results['skills_extraction'] = {'processed': 0, 'failed': 0, 'total_skills': 0}
        
        # Process embeddings
        if 'embeddings' in enrichment_types:
            jobs = get_jobs_needing_enrichment('embeddings', batch_size)
            logger.log_text(f"Found {len(jobs)} jobs needing embeddings", severity="INFO")
            
            if jobs:
                embeddings_stats = process_embeddings(jobs)
                results['embeddings'] = embeddings_stats
                logger.log_text(f"Embeddings generation complete: {embeddings_stats}", severity="INFO")
            else:
                results['embeddings'] = {'processed': 0, 'failed': 0, 'total_embeddings': 0}
        
        # Calculate execution time
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        response = {
            'status': 'success',
            **results,
            'execution_time_seconds': execution_time
        }
        
        logger.log_text(f"ML enrichment complete: {response}", severity="INFO")
        
        return json.dumps(response), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        logger.log_text(f"ML enrichment failed: {str(e)}", severity="ERROR")
        return json.dumps({
            'status': 'error',
            'error': str(e)
        }), 500, {'Content-Type': 'application/json'}
