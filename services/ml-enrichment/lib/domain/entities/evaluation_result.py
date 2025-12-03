"""
EvaluationResult Entity

Represents results from ML model evaluation against labeled data.
Used for tracking model performance over time and CI/CD integration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


@dataclass
class EvaluationResult:
    """
    Results from evaluating an ML model against labeled data.
    
    Attributes:
        evaluation_id: Unique identifier (UUID)
        model_id: Which model was evaluated
        model_version: Specific version evaluated
        dataset_version: Version of evaluation dataset
        dataset_path: GCS path to dataset
        sample_count: Number of samples evaluated
        overall_precision: Macro precision (0.0-1.0)
        overall_recall: Macro recall (0.0-1.0)
        overall_f1: Macro F1 score (0.0-1.0)
        category_metrics: Per-category breakdown
        evaluation_date: When evaluation was run
        execution_time_seconds: How long evaluation took
        is_ci_run: Whether this was a CI pipeline run
        ci_build_id: CI build identifier
        threshold_passed: Did it meet threshold?
    """
    
    # Required fields
    model_id: str
    model_version: str
    dataset_version: str
    sample_count: int
    overall_precision: float
    overall_recall: float
    overall_f1: float
    
    # Auto-generated fields
    evaluation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evaluation_date: datetime = field(default_factory=datetime.utcnow)
    
    # Dataset information
    dataset_path: Optional[str] = None
    
    # Per-category breakdown
    # Example: {"programming_languages": {"precision": 0.85, "recall": 0.90, "f1": 0.87, "support": 50}}
    category_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Execution information
    execution_time_seconds: float = 0.0
    
    # CI/CD integration
    is_ci_run: bool = False
    ci_build_id: Optional[str] = None
    ci_pipeline_name: Optional[str] = None
    threshold_f1: Optional[float] = None
    threshold_passed: Optional[bool] = None
    
    # Additional metrics
    overall_accuracy: Optional[float] = None
    
    # Metadata
    notes: Optional[str] = None
    environment: str = "production"
    gcp_project: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate evaluation result after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate all fields."""
        # Validate model_id
        if not self.model_id or not self.model_id.strip():
            raise ValueError("model_id cannot be empty")
        
        # Validate model_version
        if not self.model_version or not self.model_version.strip():
            raise ValueError("model_version cannot be empty")
        
        # Validate sample_count
        if self.sample_count <= 0:
            raise ValueError("sample_count must be > 0")
        
        # Validate metric ranges
        for metric_name, metric_value in [
            ('overall_precision', self.overall_precision),
            ('overall_recall', self.overall_recall),
            ('overall_f1', self.overall_f1)
        ]:
            if not (0.0 <= metric_value <= 1.0):
                raise ValueError(f"{metric_name} must be between 0.0 and 1.0")
        
        # Validate optional accuracy if provided
        if self.overall_accuracy is not None:
            if not (0.0 <= self.overall_accuracy <= 1.0):
                raise ValueError("overall_accuracy must be between 0.0 and 1.0")
        
        # Validate execution_time_seconds
        if self.execution_time_seconds < 0:
            raise ValueError("execution_time_seconds must be >= 0")
        
        # Validate category_metrics
        for category, metrics in self.category_metrics.items():
            for key in ['precision', 'recall', 'f1']:
                if key in metrics:
                    if not (0.0 <= metrics[key] <= 1.0):
                        raise ValueError(f"{category}.{key} must be between 0.0 and 1.0")
    
    def passed_threshold(self, threshold: float) -> bool:
        """
        Check if the evaluation passed a given F1 threshold.
        
        Args:
            threshold: Minimum F1 score required
            
        Returns:
            True if overall_f1 >= threshold
        """
        return self.overall_f1 >= threshold
    
    def get_category_f1(self, category: str) -> Optional[float]:
        """Get F1 score for a specific category."""
        if category in self.category_metrics:
            return self.category_metrics[category].get('f1')
        return None
    
    def get_weakest_category(self) -> Optional[tuple]:
        """
        Get the category with the lowest F1 score.
        
        Returns:
            Tuple of (category_name, f1_score) or None
        """
        if not self.category_metrics:
            return None
        
        weakest = None
        lowest_f1 = 1.0
        
        for category, metrics in self.category_metrics.items():
            f1 = metrics.get('f1', 1.0)
            if f1 < lowest_f1:
                lowest_f1 = f1
                weakest = (category, f1)
        
        return weakest
    
    def get_strongest_category(self) -> Optional[tuple]:
        """
        Get the category with the highest F1 score.
        
        Returns:
            Tuple of (category_name, f1_score) or None
        """
        if not self.category_metrics:
            return None
        
        strongest = None
        highest_f1 = 0.0
        
        for category, metrics in self.category_metrics.items():
            f1 = metrics.get('f1', 0.0)
            if f1 > highest_f1:
                highest_f1 = f1
                strongest = (category, f1)
        
        return strongest
    
    def compare_to(self, other: 'EvaluationResult') -> Dict[str, float]:
        """
        Compare this evaluation to another.
        
        Args:
            other: Another EvaluationResult to compare against
            
        Returns:
            Dictionary with metric differences (positive = improvement)
        """
        return {
            'precision_diff': self.overall_precision - other.overall_precision,
            'recall_diff': self.overall_recall - other.overall_recall,
            'f1_diff': self.overall_f1 - other.overall_f1
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'evaluation_id': self.evaluation_id,
            'model_id': self.model_id,
            'model_version': self.model_version,
            'dataset_version': self.dataset_version,
            'dataset_path': self.dataset_path,
            'sample_count': self.sample_count,
            'overall_precision': self.overall_precision,
            'overall_recall': self.overall_recall,
            'overall_f1': self.overall_f1,
            'overall_accuracy': self.overall_accuracy,
            'category_metrics': self.category_metrics,
            'evaluation_date': self.evaluation_date.isoformat(),
            'execution_time_seconds': self.execution_time_seconds,
            'is_ci_run': self.is_ci_run,
            'ci_build_id': self.ci_build_id,
            'ci_pipeline_name': self.ci_pipeline_name,
            'threshold_f1': self.threshold_f1,
            'threshold_passed': self.threshold_passed,
            'notes': self.notes,
            'environment': self.environment,
            'gcp_project': self.gcp_project,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EvaluationResult':
        """Create from dictionary."""
        return cls(
            evaluation_id=data.get('evaluation_id', str(uuid.uuid4())),
            model_id=data['model_id'],
            model_version=data['model_version'],
            dataset_version=data['dataset_version'],
            dataset_path=data.get('dataset_path'),
            sample_count=data['sample_count'],
            overall_precision=data['overall_precision'],
            overall_recall=data['overall_recall'],
            overall_f1=data['overall_f1'],
            overall_accuracy=data.get('overall_accuracy'),
            category_metrics=data.get('category_metrics', {}),
            evaluation_date=datetime.fromisoformat(data['evaluation_date']) if data.get('evaluation_date') else datetime.utcnow(),
            execution_time_seconds=data.get('execution_time_seconds', 0.0),
            is_ci_run=data.get('is_ci_run', False),
            ci_build_id=data.get('ci_build_id'),
            ci_pipeline_name=data.get('ci_pipeline_name'),
            threshold_f1=data.get('threshold_f1'),
            threshold_passed=data.get('threshold_passed'),
            notes=data.get('notes'),
            environment=data.get('environment', 'production'),
            gcp_project=data.get('gcp_project'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow()
        )
    
    def __repr__(self):
        """String representation."""
        passed = "PASS" if self.threshold_passed else ("FAIL" if self.threshold_passed is False else "N/A")
        return f"EvaluationResult(model={self.model_id} v{self.model_version}, F1={self.overall_f1:.3f}, {passed})"
