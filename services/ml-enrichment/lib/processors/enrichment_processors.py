"""
Processing orchestrators for different enrichment types.

Coordinates enrichment modules with logging and error handling.
"""

from typing import List, Dict, Any
from lib.utils.enrichment_utils import log_enrichment, get_logger


logger = get_logger()


def process_skills_extraction(jobs: List[Dict[str, Any]], skills_extractor) -> Dict[str, Any]:
    """
    Extract skills from job postings.
    
    Args:
        jobs: List of job records
        skills_extractor: SkillsExtractor instance
        
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


def process_embeddings(jobs: List[Dict[str, Any]], embeddings_generator) -> Dict[str, Any]:
    """
    Generate vector embeddings for job descriptions.
    
    Args:
        jobs: List of job records
        embeddings_generator: EmbeddingsGenerator instance
        
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


def process_clustering(job_clusterer, n_clusters: int = 10, method: str = "kmeans") -> Dict[str, Any]:
    """
    Cluster all jobs with embeddings and extract keywords.
    
    Args:
        job_clusterer: JobClusterer instance
        n_clusters: Number of clusters for kmeans
        method: Clustering method ('kmeans' or 'dbscan')
        
    Returns:
        Statistics: total_jobs, clusters_created, keywords_extracted
    """
    try:
        # Perform clustering
        cluster_results = job_clusterer.cluster_jobs(
            method=method,
            n_clusters=n_clusters
        )
        
        if cluster_results:
            # Log successful enrichment
            enrichment_id = log_enrichment(
                job_posting_id="ALL",  # Clustering applies to all jobs
                enrichment_type='job_clustering',
                enrichment_version=job_clusterer.get_version(),
                status='success',
                metadata={
                    'n_clusters': n_clusters,
                    'method': method,
                    'jobs_clustered': len(cluster_results)
                }
            )
            
            # Store cluster assignments
            job_clusterer.store_clusters(
                cluster_results=cluster_results,
                enrichment_id=enrichment_id
            )
            
            # Count unique clusters
            unique_clusters = len(set(r['cluster_id'] for r in cluster_results))
            
            return {
                'total_jobs': len(cluster_results),
                'clusters_created': unique_clusters,
                'method': method
            }
        else:
            return {
                'total_jobs': 0,
                'clusters_created': 0,
                'method': method
            }
            
    except Exception as e:
        logger.log_text(
            f"Job clustering failed: {str(e)}",
            severity="ERROR"
        )
        log_enrichment(
            job_posting_id="ALL",
            enrichment_type='job_clustering',
            enrichment_version=job_clusterer.get_version(),
            status='failed',
            error_message=str(e)
        )
        raise
