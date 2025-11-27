"""
ML Enrichment Service for LinkedIn Job Postings

This Cloud Run service enriches job postings with:
1. Skills extraction (from job_summary and job_description_formatted)
2. Vector embeddings (for semantic search)
3. Job clustering (grouping similar jobs with keyword extraction)

Architecture:
- Reads unenriched jobs from job_postings
- Tracks enrichment status in job_enrichments (polymorphic)
- Stores results in job_skills, job_embeddings, and job_clusters
- Maintains loose coupling with job_postings table
"""

import functions_framework
import json
from datetime import datetime
from lib.enrichment.skills import SkillsExtractor, SkillsConfig
from lib.enrichment.embeddings_generator import EmbeddingsGenerator
from lib.enrichment.job_clusterer import JobClusterer
from lib.utils.enrichment_utils import get_jobs_needing_enrichment, get_logger
from lib.processors.enrichment_processors import (
    process_skills_extraction,
    process_embeddings,
    process_clustering
)

# Get logger
logger = get_logger()

# Lazy-load enrichment modules to speed up cold start
_skills_extractor = None
_embeddings_generator = None
_job_clusterer = None

def get_skills_extractor():
    """Lazy load skills extractor."""
    global _skills_extractor
    if _skills_extractor is None:
        _skills_extractor = SkillsExtractor()
    return _skills_extractor

def get_embeddings_generator():
    """Lazy load embeddings generator."""
    global _embeddings_generator
    if _embeddings_generator is None:
        _embeddings_generator = EmbeddingsGenerator()
    return _embeddings_generator

def get_job_clusterer():
    """Lazy load job clusterer."""
    global _job_clusterer
    if _job_clusterer is None:
        _job_clusterer = JobClusterer()
    return _job_clusterer


@functions_framework.http
def main(request):
    """
    HTTP Cloud Function to run ML enrichment on job postings.
    
    Request body (optional):
        {
            "enrichment_types": ["skills_extraction", "embeddings", "clustering"],  # defaults to all except clustering
            "batch_size": 50,  # for skills and embeddings
            "n_clusters": 10,  # for clustering only
            "clustering_method": "kmeans"  # 'kmeans' or 'dbscan'
        }
    
    Response:
        {
            "status": "success",
            "skills_extraction": {"processed": 10, "failed": 0, "total_skills": 45},
            "embeddings": {"processed": 10, "failed": 0, "total_embeddings": 30},
            "clustering": {"total_jobs": 64, "clusters_created": 10, "method": "kmeans"},
            "execution_time_seconds": 12.5
        }
    """
    start_time = datetime.utcnow()
    
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        enrichment_types = request_json.get('enrichment_types', ['skills_extraction', 'embeddings'])
        batch_size = request_json.get('batch_size', 50)
        n_clusters = request_json.get('n_clusters', 10)
        clustering_method = request_json.get('clustering_method', 'kmeans')
        
        logger.log_text(
            f"Starting ML enrichment: types={enrichment_types}, batch_size={batch_size}",
            severity="INFO"
        )
        
        results = {}
        
        # Process skills extraction
        if 'skills_extraction' in enrichment_types:
            extractor = get_skills_extractor()
            jobs = get_jobs_needing_enrichment(
                'skills_extraction', 
                batch_size,
                enrichment_version=extractor.get_version()
            )
            logger.log_text(f"Found {len(jobs)} jobs needing skills extraction v{extractor.get_version()}", severity="INFO")
            
            if jobs:
                skills_stats = process_skills_extraction(
                    jobs=jobs,
                    extractor=extractor
                )
                results['skills_extraction'] = skills_stats
                logger.log_text(f"Skills extraction complete: {skills_stats}", severity="INFO")
            else:
                results['skills_extraction'] = {'processed': 0, 'failed': 0, 'total_skills': 0}
        
        # Process embeddings
        if 'embeddings' in enrichment_types:
            generator = get_embeddings_generator()
            jobs = get_jobs_needing_enrichment(
                'embeddings', 
                batch_size,
                enrichment_version=generator.get_version()
            )
            logger.log_text(f"Found {len(jobs)} jobs needing embeddings v{generator.get_version()}", severity="INFO")
            
            if jobs:
                embeddings_stats = process_embeddings(
                    jobs=jobs,
                    generator=generator
                )
                results['embeddings'] = embeddings_stats
                logger.log_text(f"Embeddings generation complete: {embeddings_stats}", severity="INFO")
            else:
                results['embeddings'] = {'processed': 0, 'failed': 0, 'total_embeddings': 0}
        
        # Process clustering (operates on all jobs with embeddings)
        if 'clustering' in enrichment_types:
            logger.log_text(f"Starting job clustering: method={clustering_method}, n_clusters={n_clusters}", severity="INFO")
            clustering_stats = process_clustering(
                job_clusterer=get_job_clusterer(),
                n_clusters=n_clusters,
                method=clustering_method
            )
            results['clustering'] = clustering_stats
            logger.log_text(f"Job clustering complete: {clustering_stats}", severity="INFO")
        
        # Calculate execution time
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        return {
            'status': 'success',
            'execution_time_seconds': execution_time,
            **results
        }, 200
        
    except Exception as e:
        logger.log_text(f"ML enrichment failed: {str(e)}", severity="ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }, 500

