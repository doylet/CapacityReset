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

