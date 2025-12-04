"""
Skills Evaluator Module

Evaluates ML model performance against labeled test data.
Calculates precision, recall, F1 and per-category metrics.
"""

import logging
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Set, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# Try to import sklearn for metrics
try:
    from sklearn.metrics import precision_recall_fscore_support, multilabel_confusion_matrix
    from sklearn.preprocessing import MultiLabelBinarizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ..domain.entities import EvaluationResult
from ..enrichment.skills import UnifiedSkillsExtractor, UnifiedSkillsConfig

logger = logging.getLogger(__name__)


@dataclass
class EvaluationSample:
    """A single evaluation sample with job text and labeled skills."""
    job_id: str
    text: str
    skills: Set[str]
    categories: Optional[Dict[str, Set[str]]] = None


class SkillsEvaluator:
    """
    Evaluates skills extraction model performance.
    
    Supports:
    - Running evaluation against labeled JSONL datasets
    - Computing precision, recall, F1 metrics
    - Per-category metric breakdown
    - CI/CD integration with threshold gating
    - Storing results in BigQuery
    """
    
    def __init__(
        self,
        model_id: str = "skills_extractor",
        extractor: Optional[UnifiedSkillsExtractor] = None,
        repository=None
    ):
        """
        Initialize evaluator.
        
        Args:
            model_id: Identifier for the model being evaluated
            extractor: Optional pre-configured extractor (for testing)
            repository: Optional BigQueryEvaluationRepository for storing results
        """
        self.model_id = model_id
        self.extractor = extractor or UnifiedSkillsExtractor(
            enable_semantic=False,
            enable_patterns=True
        )
        self.model_version = self.extractor.get_version()
        self._repository = repository
    
    @property
    def repository(self):
        """Lazy-load repository to avoid import issues."""
        if self._repository is None:
            try:
                from ..adapters.bigquery import BigQueryEvaluationRepository
                self._repository = BigQueryEvaluationRepository()
            except Exception as e:
                logger.warning(f"Could not initialize repository: {e}")
                self._repository = None
        return self._repository
    
    def evaluate(
        self,
        dataset_path: Optional[str] = None,
        dataset: Optional[List[EvaluationSample]] = None,
        sample_limit: Optional[int] = None,
        categories: Optional[List[str]] = None,
        save_results: bool = False
    ) -> EvaluationResult:
        """
        Run evaluation on a dataset.
        
        Args:
            dataset_path: Path to JSONL dataset file (local or GCS)
            dataset: Pre-loaded list of EvaluationSample objects
            sample_limit: Maximum samples to evaluate
            categories: Limit evaluation to specific categories
            save_results: Whether to save results to BigQuery
            
        Returns:
            EvaluationResult with metrics
        """
        start_time = time.time()
        
        # Load dataset
        if dataset is None and dataset_path:
            samples = self._load_dataset(dataset_path, sample_limit)
        elif dataset is not None:
            samples = dataset[:sample_limit] if sample_limit else dataset
        else:
            raise ValueError("Either dataset_path or dataset must be provided")
        
        if not samples:
            raise ValueError("No evaluation samples found")
        
        logger.info(f"Evaluating {len(samples)} samples")
        
        # Extract skills for each sample
        predictions = []
        actuals = []
        
        for sample in samples:
            result = self.extractor.extract_skills(
                job_summary=sample.text[:500],  # Use first 500 chars as summary
                job_description=sample.text,
                job_id=sample.job_id
            )
            
            # Get predicted skill names (lowercase for comparison)
            predicted_skills = set(
                s['text'].lower() for s in result.get('skills', [])
            )
            predictions.append(predicted_skills)
            
            # Get actual skills (lowercase for comparison)
            actual_skills = set(s.lower() for s in sample.skills)
            actuals.append(actual_skills)
        
        # Calculate metrics
        metrics = self._calculate_metrics(predictions, actuals)
        
        # Calculate per-category metrics if categories available
        category_metrics = {}
        if categories:
            category_metrics = self._calculate_category_metrics(
                predictions, actuals, samples, categories
            )
        
        execution_time = time.time() - start_time
        
        # Create result
        result = EvaluationResult(
            evaluation_id=str(uuid.uuid4()),
            model_id=self.model_id,
            model_version=self.model_version,
            dataset_version=self._get_dataset_version(dataset_path),
            dataset_path=dataset_path,
            sample_count=len(samples),
            overall_precision=metrics['precision'],
            overall_recall=metrics['recall'],
            overall_f1=metrics['f1'],
            category_metrics=category_metrics,
            evaluation_date=datetime.utcnow(),
            execution_time_seconds=execution_time
        )
        
        logger.info(
            f"Evaluation complete: precision={metrics['precision']:.3f}, "
            f"recall={metrics['recall']:.3f}, f1={metrics['f1']:.3f}"
        )
        
        # Save results to BigQuery if requested
        if save_results and self.repository:
            try:
                self.repository.save(result)
                logger.info(f"Saved evaluation result: {result.evaluation_id}")
            except Exception as e:
                logger.warning(f"Failed to save evaluation result: {e}")
        
        return result
    
    def evaluate_quick(
        self,
        dataset_path: str,
        threshold_f1: float = 0.7,
        sample_limit: int = 50,
        ci_build_id: Optional[str] = None
    ) -> EvaluationResult:
        """
        Run quick evaluation for CI/CD pipelines.
        
        Args:
            dataset_path: Path to evaluation dataset
            threshold_f1: Minimum F1 score to pass
            sample_limit: Maximum samples (default 50 for speed)
            ci_build_id: Optional CI build identifier
            
        Returns:
            EvaluationResult with threshold_passed flag
        """
        result = self.evaluate(
            dataset_path=dataset_path,
            sample_limit=sample_limit
        )
        
        # Set CI-specific fields
        result.is_ci_run = True
        result.ci_build_id = ci_build_id
        result.threshold_f1 = threshold_f1
        result.threshold_passed = result.overall_f1 >= threshold_f1
        
        status = "PASS" if result.threshold_passed else "FAIL"
        logger.info(
            f"Quick evaluation {status}: F1={result.overall_f1:.3f} "
            f"(threshold={threshold_f1})"
        )
        
        return result
    
    def _load_dataset(
        self,
        path: str,
        limit: Optional[int] = None
    ) -> List[EvaluationSample]:
        """
        Load dataset from JSONL file.
        
        Expected format:
        {"job_id": "...", "text": "...", "skills": ["Python", "Django", ...]}
        
        Args:
            path: Path to JSONL file (local or gs://)
            limit: Maximum samples to load
            
        Returns:
            List of EvaluationSample objects
        """
        samples = []
        
        # Handle GCS paths
        if path.startswith('gs://'):
            samples = self._load_from_gcs(path, limit)
        else:
            # Local file
            samples = self._load_from_local(path, limit)
        
        return samples
    
    def _load_from_local(
        self,
        path: str,
        limit: Optional[int] = None
    ) -> List[EvaluationSample]:
        """Load from local JSONL file."""
        samples = []
        
        try:
            with open(path, 'r') as f:
                for i, line in enumerate(f):
                    if limit and i >= limit:
                        break
                    
                    data = json.loads(line.strip())
                    samples.append(EvaluationSample(
                        job_id=data.get('job_id', f'sample-{i}'),
                        text=data.get('text', ''),
                        skills=set(data.get('skills', []))
                    ))
        except FileNotFoundError:
            logger.warning(f"Dataset file not found: {path}")
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
        
        return samples
    
    def _load_from_gcs(
        self,
        gcs_path: str,
        limit: Optional[int] = None
    ) -> List[EvaluationSample]:
        """Load from GCS bucket."""
        samples = []
        
        try:
            from google.cloud import storage
            from google.auth.exceptions import DefaultCredentialsError
            
            # Parse GCS path
            path_parts = gcs_path.replace('gs://', '').split('/', 1)
            bucket_name = path_parts[0]
            blob_name = path_parts[1] if len(path_parts) > 1 else ''
            
            try:
                client = storage.Client()
            except DefaultCredentialsError as e:
                logger.error(
                    f"GCS authentication failed. Ensure GOOGLE_APPLICATION_CREDENTIALS "
                    f"is set or run 'gcloud auth application-default login'. Error: {e}"
                )
                return samples
            
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            content = blob.download_as_text()
            
            for i, line in enumerate(content.strip().split('\n')):
                if limit and i >= limit:
                    break
                
                data = json.loads(line)
                samples.append(EvaluationSample(
                    job_id=data.get('job_id', f'sample-{i}'),
                    text=data.get('text', ''),
                    skills=set(data.get('skills', []))
                ))
                
        except ImportError:
            logger.error("google-cloud-storage package not installed")
        except Exception as e:
            logger.error(f"Error loading from GCS: {e}")
        
        return samples
    
    def _calculate_metrics(
        self,
        predictions: List[Set[str]],
        actuals: List[Set[str]]
    ) -> Dict[str, float]:
        """
        Calculate overall precision, recall, F1.
        
        Uses set-based metrics where:
        - True Positive: skill in both predicted and actual
        - False Positive: skill in predicted but not actual
        - False Negative: skill in actual but not predicted
        """
        total_tp = 0
        total_fp = 0
        total_fn = 0
        
        for pred, actual in zip(predictions, actuals):
            tp = len(pred & actual)
            fp = len(pred - actual)
            fn = len(actual - pred)
            
            total_tp += tp
            total_fp += fp
            total_fn += fn
        
        # Calculate metrics
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'true_positives': total_tp,
            'false_positives': total_fp,
            'false_negatives': total_fn
        }
    
    def _calculate_category_metrics(
        self,
        predictions: List[Set[str]],
        actuals: List[Set[str]],
        samples: List[EvaluationSample],
        categories: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate metrics per skill category."""
        category_metrics = {}
        
        # This would require category information in the samples
        # For now, return empty if no category data available
        
        for category in categories:
            category_metrics[category] = {
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'support': 0
            }
        
        return category_metrics
    
    def _get_dataset_version(self, path: Optional[str]) -> str:
        """Extract dataset version from path or generate one."""
        if not path:
            return f"inline-{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Try to extract version from filename
        filename = Path(path).stem if not path.startswith('gs://') else path.split('/')[-1]
        
        # Look for version pattern
        if '_v' in filename:
            return filename.split('_v')[-1].replace('.jsonl', '')
        
        return filename


def run_cli_evaluation():
    """
    CLI entry point for running evaluation.
    
    Usage:
        python -m lib.evaluation.evaluator --dataset path/to/data.jsonl --threshold 0.75
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run skills extraction evaluation')
    parser.add_argument('--dataset', required=True, help='Path to evaluation dataset (JSONL)')
    parser.add_argument('--threshold', type=float, default=0.7, help='F1 threshold for CI gate')
    parser.add_argument('--limit', type=int, help='Maximum samples to evaluate')
    parser.add_argument('--ci-build-id', help='CI build identifier')
    parser.add_argument('--output', help='Output path for results JSON')
    
    args = parser.parse_args()
    
    evaluator = SkillsEvaluator()
    
    result = evaluator.evaluate_quick(
        dataset_path=args.dataset,
        threshold_f1=args.threshold,
        sample_limit=args.limit,
        ci_build_id=args.ci_build_id
    )
    
    # Output results
    print(f"\n{'='*50}")
    print(f"Evaluation Results for {result.model_id} {result.model_version}")
    print(f"{'='*50}")
    print(f"Samples:    {result.sample_count}")
    print(f"Precision:  {result.overall_precision:.4f}")
    print(f"Recall:     {result.overall_recall:.4f}")
    print(f"F1 Score:   {result.overall_f1:.4f}")
    print(f"Threshold:  {args.threshold}")
    print(f"Status:     {'✓ PASS' if result.threshold_passed else '✗ FAIL'}")
    print(f"Time:       {result.execution_time_seconds:.2f}s")
    print(f"{'='*50}\n")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        print(f"Results saved to {args.output}")
    
    # Exit with appropriate code for CI
    import sys
    sys.exit(0 if result.threshold_passed else 1)


if __name__ == "__main__":
    run_cli_evaluation()
