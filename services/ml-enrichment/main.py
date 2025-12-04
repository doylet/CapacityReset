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
from lib.enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig

from lib.enrichment.embeddings_generator import EmbeddingsGenerator
from lib.enrichment.job_clusterer import JobClusterer
from lib.utils.enrichment_utils import get_jobs_needing_enrichment, get_logger
from lib.processors.enrichment_processors import (
    process_skills_extraction,
    process_embeddings,
    process_clustering
)
from lib.config import get_alias_resolver

# Get logger
logger = get_logger()

# Lazy-load enrichment modules to speed up cold start
_skills_extractor = None
_embeddings_generator = None
_job_clusterer = None

def get_skills_extractor():
    """Get unified skills extractor that automatically handles enhanced/original fallback."""
    global _skills_extractor
    if _skills_extractor is None:
        # Use unified extractor with automatic enhanced/original fallback
        _skills_extractor = UnifiedSkillsExtractor(
            config=UnifiedSkillsConfig(),
            enable_semantic=True,  # Enable semantic similarity if available
            enable_patterns=True   # Enable pattern extraction if available
        )
        
        # Log which mode is being used
        version = _skills_extractor.get_version()
        mode = "Enhanced" if _skills_extractor.enhanced_mode else "Original"
        logger.log_text(f"Using {mode} Skills Extractor {version}", severity="INFO")
        
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
            
            # Reset alias resolver stats for this batch
            alias_resolver = get_alias_resolver()
            alias_resolver.reset_stats()
            
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
                # Add extractor version to response
                skills_stats['extractor_version'] = extractor.get_version()
                
                # Add alias resolution statistics
                alias_stats = alias_resolver.get_stats()
                skills_stats['alias_resolution'] = {
                    'total_lookups': alias_stats.get('total_lookups', 0),
                    'successful_resolutions': alias_stats.get('successful_resolutions', 0),
                    'resolution_rate': alias_stats.get('resolution_rate', 0.0),
                    'total_aliases_available': alias_stats.get('total_aliases_loaded', 0)
                }
                
                results['skills_extraction'] = skills_stats
                logger.log_text(f"Skills extraction complete: {skills_stats}", severity="INFO")
            else:
                # Cache stats to avoid redundant computation
                empty_alias_stats = alias_resolver.get_stats()
                results['skills_extraction'] = {
                    'processed': 0, 
                    'failed': 0, 
                    'total_skills': 0,
                    'extractor_version': extractor.get_version(),
                    'alias_resolution': {
                        'total_lookups': 0,
                        'successful_resolutions': 0,
                        'resolution_rate': 0.0,
                        'total_aliases_available': empty_alias_stats.get('total_aliases_loaded', 0)
                    }
                }
        
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
                # Add generator version to response
                embeddings_stats['generator_version'] = generator.get_version()
                results['embeddings'] = embeddings_stats
                logger.log_text(f"Embeddings generation complete: {embeddings_stats}", severity="INFO")
            else:
                results['embeddings'] = {
                    'processed': 0, 
                    'failed': 0, 
                    'total_embeddings': 0,
                    'generator_version': generator.get_version()
                }
        
        # Process clustering (operates on all jobs with embeddings)
        if 'clustering' in enrichment_types:
            clusterer = get_job_clusterer()
            logger.log_text(f"Starting job clustering: method={clustering_method}, n_clusters={n_clusters}", severity="INFO")
            clustering_stats = process_clustering(
                job_clusterer=clusterer,
                n_clusters=n_clusters,
                method=clustering_method
            )
            # Add clusterer version to response
            clustering_stats['cluster_model_id'] = clusterer.get_version()
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


# Lazy-load evaluator
_skills_evaluator = None

def get_skills_evaluator():
    """Get skills evaluator instance."""
    global _skills_evaluator
    if _skills_evaluator is None:
        from lib.evaluation.evaluator import SkillsEvaluator
        extractor = get_skills_extractor()
        _skills_evaluator = SkillsEvaluator(
            model_id="skills_extractor",
            extractor=extractor
        )
    return _skills_evaluator


@functions_framework.http
def evaluate(request):
    """
    HTTP Cloud Function to evaluate skills extraction model.
    
    POST /evaluate
    Request body:
        {
            "dataset_path": "gs://bucket/path/to/data.jsonl",  # or local path
            "sample_limit": 100,  # optional, limit samples
            "categories": ["programming_languages", "cloud_platforms"]  # optional
        }
    
    Response:
        {
            "status": "success",
            "evaluation": {
                "model_id": "skills_extractor",
                "model_version": "v4.0-enhanced",
                "overall_precision": 0.85,
                "overall_recall": 0.90,
                "overall_f1": 0.87,
                "sample_count": 100,
                "execution_time_seconds": 5.5,
                "category_metrics": {...}
            }
        }
    """
    try:
        request_json = request.get_json(silent=True) or {}
        
        dataset_path = request_json.get('dataset_path')
        sample_limit = request_json.get('sample_limit')
        categories = request_json.get('categories')
        
        if not dataset_path:
            return {
                'status': 'error',
                'error': 'dataset_path is required'
            }, 400
        
        evaluator = get_skills_evaluator()
        
        logger.log_text(
            f"Starting evaluation: dataset={dataset_path}, limit={sample_limit}",
            severity="INFO"
        )
        
        result = evaluator.evaluate(
            dataset_path=dataset_path,
            sample_limit=sample_limit,
            categories=categories
        )
        
        logger.log_text(
            f"Evaluation complete: F1={result.overall_f1:.3f}, samples={result.sample_count}",
            severity="INFO"
        )
        
        return {
            'status': 'success',
            'evaluation': result.to_dict()
        }, 200
        
    except Exception as e:
        logger.log_text(f"Evaluation failed: {str(e)}", severity="ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }, 500


@functions_framework.http
def evaluate_quick(request):
    """
    HTTP Cloud Function for quick CI/CD evaluation.
    
    POST /evaluate/quick
    Request body:
        {
            "dataset_path": "gs://bucket/path/to/data.jsonl",
            "threshold": 0.75,  # F1 threshold
            "sample_limit": 50,  # default: 50 for speed
            "ci_build_id": "build-12345"  # optional
        }
    
    Response:
        {
            "status": "success",
            "passed": true,
            "evaluation": {
                "overall_f1": 0.82,
                "threshold": 0.75,
                "threshold_passed": true,
                "execution_time_seconds": 2.5
            }
        }
    
    Exit codes for CI:
        200: Passed threshold
        400: Bad request
        417: Failed threshold (Expectation Failed)
        500: Server error
    """
    try:
        request_json = request.get_json(silent=True) or {}
        
        dataset_path = request_json.get('dataset_path')
        threshold = request_json.get('threshold', 0.7)
        sample_limit = request_json.get('sample_limit', 50)
        ci_build_id = request_json.get('ci_build_id')
        
        if not dataset_path:
            return {
                'status': 'error',
                'error': 'dataset_path is required'
            }, 400
        
        evaluator = get_skills_evaluator()
        
        logger.log_text(
            f"Starting quick evaluation: threshold={threshold}, limit={sample_limit}",
            severity="INFO"
        )
        
        result = evaluator.evaluate_quick(
            dataset_path=dataset_path,
            threshold_f1=threshold,
            sample_limit=sample_limit,
            ci_build_id=ci_build_id
        )
        
        status_code = 200 if result.threshold_passed else 417
        status_str = "PASS" if result.threshold_passed else "FAIL"
        
        logger.log_text(
            f"Quick evaluation {status_str}: F1={result.overall_f1:.3f} (threshold={threshold})",
            severity="INFO" if result.threshold_passed else "WARNING"
        )
        
        return {
            'status': 'success',
            'passed': result.threshold_passed,
            'evaluation': {
                'model_version': result.model_version,
                'overall_f1': result.overall_f1,
                'overall_precision': result.overall_precision,
                'overall_recall': result.overall_recall,
                'threshold': threshold,
                'threshold_passed': result.threshold_passed,
                'sample_count': result.sample_count,
                'execution_time_seconds': result.execution_time_seconds,
                'ci_build_id': ci_build_id
            }
        }, status_code
        
    except Exception as e:
        logger.log_text(f"Quick evaluation failed: {str(e)}", severity="ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }, 500


@functions_framework.http
def evaluate_results(request):
    """
    HTTP Cloud Function to retrieve historical evaluation results.
    
    GET /evaluate/results
    Query params:
        model_id: Filter by model ID (optional)
        limit: Number of results (default: 10)
    
    Response:
        {
            "status": "success",
            "results": [
                {
                    "evaluation_id": "...",
                    "model_version": "v4.0-enhanced",
                    "overall_f1": 0.87,
                    "evaluation_date": "2024-01-15T10:30:00",
                    ...
                },
                ...
            ]
        }
    """
    try:
        from lib.adapters.bigquery import BigQueryEvaluationRepository
        
        model_id = request.args.get('model_id', 'skills_extractor')
        limit = int(request.args.get('limit', 10))
        
        repo = BigQueryEvaluationRepository()
        results = repo.get_recent_results(model_id=model_id, limit=limit)
        
        return {
            'status': 'success',
            'count': len(results),
            'results': [r.to_dict() for r in results]
        }, 200
        
    except Exception as e:
        logger.log_text(f"Failed to fetch evaluation results: {str(e)}", severity="ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }, 500


