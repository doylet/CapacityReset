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
import gc
import psutil
import os
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

# Get logger
logger = get_logger()

def log_memory_usage(stage):
    """Log current memory usage for monitoring."""
    try:
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.log_text(f"Memory usage at {stage}: {memory_mb:.1f} MB", severity="INFO")
    except Exception:
        # Skip memory logging if psutil unavailable
        pass

def force_garbage_collection():
    """Force garbage collection to free memory."""
    gc.collect()
    log_memory_usage("after garbage collection")

# Lazy-load enrichment modules to speed up cold start
_skills_extractor = None
_embeddings_generator = None
_job_clusterer = None
_brand_analyzer = None
_content_generator = None

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


def get_brand_analyzer():
    """Lazy load brand analyzer for professional brand analysis."""
    global _brand_analyzer
    if _brand_analyzer is None:
        from lib.brand_analyzer import BrandAnalyzer
        _brand_analyzer = BrandAnalyzer()
        logger.log_text("BrandAnalyzer initialized for professional brand analysis", severity="INFO")
    return _brand_analyzer


def get_content_generator():
    """Lazy load content generator for cross-surface professional content generation."""
    global _content_generator
    if _content_generator is None:
        from lib.content_generator import ContentGenerator
        _content_generator = ContentGenerator()
        logger.log_text("ContentGenerator initialized for cross-surface content generation", severity="INFO")
    return _content_generator


@functions_framework.http
def main(request):
    """
    HTTP Cloud Function to run ML enrichment on job postings.
    
    Request body (optional):
        {
            "enrichment_types": ["skills_extraction", "embeddings", "clustering"],  # defaults to all except clustering
            "batch_size": 25,  # for skills and embeddings (reduced for memory efficiency)
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
        batch_size = request_json.get('batch_size', 25)
        n_clusters = request_json.get('n_clusters', 10)
        clustering_method = request_json.get('clustering_method', 'kmeans')
        
        logger.log_text(
            f"Starting ML enrichment: types={enrichment_types}, batch_size={batch_size}",
            severity="INFO"
        )
        
        log_memory_usage("enrichment start")
        
        results = {}
        
        # Process skills extraction
        if 'skills_extraction' in enrichment_types:
            log_memory_usage("before skills extraction")
            
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
                # Add extractor version to response
                skills_stats['extractor_version'] = extractor.get_version()
                
                # Add alias resolution statistics
                try:
                    from lib.config import get_alias_resolver
                    resolver = get_alias_resolver()
                    all_aliases = resolver.get_all_aliases()
                    skills_stats['alias_resolution'] = {
                        'aliases_loaded': len(all_aliases),
                        'resolver_available': True
                    }
                except Exception as e:
                    skills_stats['alias_resolution'] = {
                        'aliases_loaded': 0,
                        'resolver_available': False,
                        'error': str(e)
                    }
                
                results['skills_extraction'] = skills_stats
                logger.log_text(f"Skills extraction complete: {skills_stats}", severity="INFO")
                
                # Force garbage collection after skills extraction
                force_garbage_collection()
            else:
                results['skills_extraction'] = {
                    'processed': 0, 
                    'failed': 0, 
                    'total_skills': 0,
                    'extractor_version': extractor.get_version(),
                    'alias_resolution': {
                        'aliases_loaded': 0,
                        'resolver_available': True
                    }
                }
        
        # Process embeddings
        if 'embeddings' in enrichment_types:
            log_memory_usage("before embeddings generation")
            
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
                
                # Force garbage collection after embeddings
                force_garbage_collection()
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
            # Add clusterer version and run ID to response
            clustering_stats['cluster_model_id'] = clusterer.get_version()
            clustering_stats['cluster_run_id'] = clusterer.get_current_run_id()
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


@functions_framework.http
def evaluate(request):
    """
    HTTP Cloud Function to run model evaluation.
    
    Request body:
        {
            "dataset_path": "gs://bucket/evaluation_data.jsonl",  # or local path
            "sample_limit": 100,  # optional
            "categories": ["programming_languages", "web_frameworks"]  # optional
        }
    
    Response:
        {
            "status": "success",
            "evaluation_id": "eval-uuid",
            "model_id": "skills_extractor",
            "model_version": "v4.0-enhanced",
            "sample_count": 100,
            "overall_precision": 0.85,
            "overall_recall": 0.90,
            "overall_f1": 0.87,
            "category_metrics": {...},
            "execution_time_seconds": 45.2
        }
    """
    start_time = datetime.utcnow()
    
    try:
        from lib.evaluation.evaluator import SkillsEvaluator
        
        # Parse request
        request_json = request.get_json(silent=True) or {}
        dataset_path = request_json.get('dataset_path')
        sample_limit = request_json.get('sample_limit')
        categories = request_json.get('categories')
        
        if not dataset_path:
            return {
                'status': 'error',
                'error': 'dataset_path is required'
            }, 400
        
        logger.log_text(f"Starting evaluation with dataset: {dataset_path}", severity="INFO")
        
        # Run evaluation
        evaluator = SkillsEvaluator()
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
            'evaluation_id': result.evaluation_id,
            'model_id': result.model_id,
            'model_version': result.model_version,
            'dataset_version': result.dataset_version,
            'sample_count': result.sample_count,
            'overall_precision': result.overall_precision,
            'overall_recall': result.overall_recall,
            'overall_f1': result.overall_f1,
            'category_metrics': result.category_metrics,
            'execution_time_seconds': result.execution_time_seconds
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
    
    Request body:
        {
            "dataset_path": "gs://bucket/eval_small.jsonl",
            "threshold_f1": 0.7,
            "sample_limit": 50,
            "ci_build_id": "build-123"  # optional
        }
    
    Response:
        {
            "status": "success",
            "threshold_passed": true,
            "overall_f1": 0.82,
            "threshold_f1": 0.7,
            "sample_count": 50,
            "execution_time_seconds": 12.5
        }
    """
    try:
        from lib.evaluation.evaluator import SkillsEvaluator
        
        # Parse request
        request_json = request.get_json(silent=True) or {}
        dataset_path = request_json.get('dataset_path')
        threshold_f1 = request_json.get('threshold_f1', 0.7)
        sample_limit = request_json.get('sample_limit', 50)
        ci_build_id = request_json.get('ci_build_id')
        
        if not dataset_path:
            return {
                'status': 'error',
                'error': 'dataset_path is required'
            }, 400
        
        logger.log_text(
            f"Starting quick evaluation: dataset={dataset_path}, threshold={threshold_f1}",
            severity="INFO"
        )
        
        # Run quick evaluation
        evaluator = SkillsEvaluator()
        result = evaluator.evaluate_quick(
            dataset_path=dataset_path,
            threshold_f1=threshold_f1,
            sample_limit=sample_limit,
            ci_build_id=ci_build_id
        )
        
        status_msg = "PASS" if result.threshold_passed else "FAIL"
        logger.log_text(
            f"Quick evaluation {status_msg}: F1={result.overall_f1:.3f} (threshold={threshold_f1})",
            severity="INFO"
        )
        
        return {
            'status': 'success',
            'threshold_passed': result.threshold_passed,
            'overall_f1': result.overall_f1,
            'overall_precision': result.overall_precision,
            'overall_recall': result.overall_recall,
            'threshold_f1': threshold_f1,
            'sample_count': result.sample_count,
            'model_version': result.model_version,
            'execution_time_seconds': result.execution_time_seconds,
            'ci_build_id': ci_build_id
        }, 200
        
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
    
    Request body:
        {
            "model_id": "skills_extractor",  # optional
            "limit": 20  # optional
        }
    
    Response:
        {
            "status": "success",
            "results": [
                {
                    "evaluation_id": "...",
                    "model_version": "v4.0-enhanced",
                    "overall_f1": 0.87,
                    "evaluation_date": "2025-12-03T10:00:00Z"
                },
                ...
            ]
        }
    """
    try:
        from lib.adapters.bigquery import BigQueryEvaluationRepository
        
        # Parse request
        request_json = request.get_json(silent=True) or {}
        model_id = request_json.get('model_id', 'skills_extractor')
        limit = request_json.get('limit', 20)
        
        logger.log_text(
            f"Fetching evaluation results: model={model_id}, limit={limit}",
            severity="INFO"
        )
        
        # Fetch results
        repository = BigQueryEvaluationRepository()
        results = repository.find_by_model(model_id=model_id, limit=limit)
        
        # Format response
        formatted_results = [
            {
                'evaluation_id': r.evaluation_id,
                'model_id': r.model_id,
                'model_version': r.model_version,
                'dataset_version': r.dataset_version,
                'sample_count': r.sample_count,
                'overall_precision': r.overall_precision,
                'overall_recall': r.overall_recall,
                'overall_f1': r.overall_f1,
                'evaluation_date': r.evaluation_date.isoformat(),
                'is_ci_run': r.is_ci_run,
                'threshold_passed': r.threshold_passed
            }
            for r in results
        ]
        
        return {
            'status': 'success',
            'count': len(formatted_results),
            'results': formatted_results
        }, 200
        
    except Exception as e:
        logger.log_text(f"Failed to fetch evaluation results: {str(e)}", severity="ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }, 500


@functions_framework.http
def classify_sections(request):
    """
    HTTP Cloud Function to classify job posting sections.
    
    Request body:
        {
            "job_posting_id": "job-123",  # optional
            "text": "Full job posting text..."
        }
    
    Response:
        {
            "status": "success",
            "sections": [
                {
                    "header": "Requirements",
                    "is_skills_relevant": true,
                    "relevance_probability": 0.9,
                    "detected_keywords": ["python", "experience with"]
                },
                ...
            ],
            "classifier_version": "v1.0-rule-based"
        }
    """
    try:
        from lib.enrichment.section_classifier import SectionClassifier
        
        # Parse request
        request_json = request.get_json(silent=True) or {}
        job_posting_id = request_json.get('job_posting_id')
        text = request_json.get('text', '')
        
        if not text:
            return {
                'status': 'error',
                'error': 'text is required'
            }, 400
        
        logger.log_text(
            f"Classifying sections for job: {job_posting_id or 'unknown'}",
            severity="INFO"
        )
        
        # Classify sections
        classifier = SectionClassifier()
        classifications = classifier.classify_sections(text, job_posting_id)
        
        # Format response
        formatted_sections = [
            {
                'section_index': c.section_index,
                'header': c.section_header,
                'text_preview': c.section_text[:200] + '...' if len(c.section_text) > 200 else c.section_text,
                'is_skills_relevant': c.is_skills_relevant,
                'relevance_probability': c.relevance_probability,
                'detected_keywords': c.detected_keywords
            }
            for c in classifications
        ]
        
        return {
            'status': 'success',
            'section_count': len(formatted_sections),
            'sections': formatted_sections,
            'classifier_version': classifier.get_version(),
            'relevant_section_count': sum(1 for c in classifications if c.is_skills_relevant)
        }, 200
        
    except Exception as e:
        logger.log_text(f"Section classification failed: {str(e)}", severity="ERROR")
        return {
            'status': 'error',
            'error': str(e)
        }, 500


@functions_framework.http
def health(request):
    """
    Health check endpoint for LLM integration status.
    
    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "services": {
                "vertex_ai": {"status": "available", "model": "gemini-flash"},
                "bigquery": {"status": "available"},
                "skills_extractor": {"status": "available", "version": "..."}
            },
            "llm_integration": {
                "status": "ready",
                "model": "gemini-flash",
                "fallback_enabled": true
            }
        }
    """
    import os
    
    status = "healthy"
    services = {}
    
    # Check Vertex AI availability
    try:
        from lib.adapters.vertex_ai_adapter import VERTEX_AI_AVAILABLE, get_vertex_client
        
        vertex_status = "available" if VERTEX_AI_AVAILABLE else "unavailable"
        if VERTEX_AI_AVAILABLE:
            client = get_vertex_client()
            vertex_status = "available" if client else "not_initialized"
        
        services["vertex_ai"] = {
            "status": vertex_status,
            "model": os.getenv("GEMINI_MODEL_NAME", "gemini-flash"),
            "project": os.getenv("VERTEX_AI_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT", "not_set")),
            "location": os.getenv("VERTEX_AI_LOCATION", "us-central1")
        }
        
        if vertex_status == "unavailable":
            status = "degraded"
            
    except Exception as e:
        services["vertex_ai"] = {"status": "error", "error": str(e)}
        status = "degraded"
    
    # Check Skills Extractor
    try:
        extractor = get_skills_extractor()
        services["skills_extractor"] = {
            "status": "available",
            "version": extractor.get_version(),
            "enhanced_mode": extractor.enhanced_mode
        }
    except Exception as e:
        services["skills_extractor"] = {"status": "error", "error": str(e)}
        status = "degraded"
    
    # Check BigQuery
    try:
        from google.cloud import bigquery
        client = bigquery.Client()
        services["bigquery"] = {
            "status": "available",
            "project": client.project
        }
    except Exception as e:
        services["bigquery"] = {"status": "error", "error": str(e)}
        status = "unhealthy"
    
    # LLM Integration Summary
    llm_integration = {
        "status": "ready" if services.get("vertex_ai", {}).get("status") == "available" else "fallback_only",
        "model": os.getenv("GEMINI_MODEL_NAME", "gemini-flash"),
        "fallback_enabled": True,
        "cache_enabled": bool(os.getenv("LLM_CACHE_TTL")),
        "max_retries": int(os.getenv("LLM_MAX_RETRIES", "3"))
    }
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": services,
        "llm_integration": llm_integration
    }, 200


