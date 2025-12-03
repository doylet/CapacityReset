"""
EvaluationResultRepository Interface

Defines the port for evaluation result storage operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from ..entities import EvaluationResult


class EvaluationResultRepository(ABC):
    """
    Abstract interface for evaluation result storage.
    
    This is a port in the hexagonal architecture - implementations
    (adapters) provide concrete storage mechanisms.
    """
    
    @abstractmethod
    def save(self, result: EvaluationResult) -> None:
        """
        Save an evaluation result.
        
        Args:
            result: The EvaluationResult to save
        """
        pass
    
    @abstractmethod
    def find_by_id(self, evaluation_id: str) -> Optional[EvaluationResult]:
        """
        Find an evaluation result by ID.
        
        Args:
            evaluation_id: The evaluation ID
            
        Returns:
            EvaluationResult if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_by_model(
        self,
        model_id: str,
        model_version: Optional[str] = None,
        limit: int = 10
    ) -> List[EvaluationResult]:
        """
        Find evaluation results for a model.
        
        Args:
            model_id: The model identifier
            model_version: Optional specific version
            limit: Maximum number of results
            
        Returns:
            List of EvaluationResult objects, newest first
        """
        pass
    
    @abstractmethod
    def find_latest(self, model_id: str) -> Optional[EvaluationResult]:
        """
        Find the most recent evaluation for a model.
        
        Args:
            model_id: The model identifier
            
        Returns:
            Most recent EvaluationResult or None
        """
        pass
    
    @abstractmethod
    def find_by_date_range(
        self,
        model_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[EvaluationResult]:
        """
        Find evaluations within a date range.
        
        Args:
            model_id: The model identifier
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of EvaluationResult objects
        """
        pass
    
    @abstractmethod
    def find_ci_runs(
        self,
        model_id: Optional[str] = None,
        limit: int = 50
    ) -> List[EvaluationResult]:
        """
        Find CI pipeline evaluation runs.
        
        Args:
            model_id: Optional filter by model
            limit: Maximum number of results
            
        Returns:
            List of CI evaluation results
        """
        pass
    
    @abstractmethod
    def get_metric_trends(
        self,
        model_id: str,
        metric: str = 'f1',
        days: int = 30
    ) -> List[Dict]:
        """
        Get metric trends over time.
        
        Args:
            model_id: The model identifier
            metric: Metric to track ('precision', 'recall', 'f1')
            days: Number of days to look back
            
        Returns:
            List of dictionaries with date and metric value
        """
        pass
    
    @abstractmethod
    def compare_versions(
        self,
        model_id: str,
        version_a: str,
        version_b: str
    ) -> Optional[Dict]:
        """
        Compare evaluation results between two versions.
        
        Args:
            model_id: The model identifier
            version_a: First version
            version_b: Second version
            
        Returns:
            Dictionary with comparison metrics or None
        """
        pass
    
    @abstractmethod
    def get_category_breakdown(
        self,
        evaluation_id: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Get per-category metrics for an evaluation.
        
        Args:
            evaluation_id: The evaluation ID
            
        Returns:
            Dictionary mapping category to metrics
        """
        pass
    
    @abstractmethod
    def delete(self, evaluation_id: str) -> bool:
        """
        Delete an evaluation result.
        
        Args:
            evaluation_id: The evaluation ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
