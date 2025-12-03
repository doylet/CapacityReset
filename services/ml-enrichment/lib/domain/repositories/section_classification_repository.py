"""
SectionClassificationRepository Interface

Defines the port for section classification storage operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from ..entities import SectionClassification


class SectionClassificationRepository(ABC):
    """
    Abstract interface for section classification storage.
    
    This is a port in the hexagonal architecture - implementations
    (adapters) provide concrete storage mechanisms.
    """
    
    @abstractmethod
    def save(self, classification: SectionClassification) -> None:
        """
        Save a section classification.
        
        Args:
            classification: The SectionClassification to save
        """
        pass
    
    @abstractmethod
    def save_batch(self, classifications: List[SectionClassification]) -> int:
        """
        Save multiple section classifications in a batch.
        
        Args:
            classifications: List of SectionClassification objects
            
        Returns:
            Number of successfully saved classifications
        """
        pass
    
    @abstractmethod
    def find_by_job(self, job_posting_id: str) -> List[SectionClassification]:
        """
        Find all classifications for a job posting.
        
        Args:
            job_posting_id: The job posting ID
            
        Returns:
            List of SectionClassification objects, ordered by section_index
        """
        pass
    
    @abstractmethod
    def find_relevant_sections(
        self,
        job_posting_id: str,
        min_probability: float = 0.5
    ) -> List[SectionClassification]:
        """
        Find skills-relevant sections for a job posting.
        
        Args:
            job_posting_id: The job posting ID
            min_probability: Minimum relevance probability
            
        Returns:
            List of relevant SectionClassification objects
        """
        pass
    
    @abstractmethod
    def find_by_classifier_version(
        self,
        classifier_version: str,
        limit: int = 100
    ) -> List[SectionClassification]:
        """
        Find classifications by classifier version.
        
        Args:
            classifier_version: The classifier version
            limit: Maximum number of results
            
        Returns:
            List of SectionClassification objects
        """
        pass
    
    @abstractmethod
    def get_training_data(
        self,
        limit: int = 1000
    ) -> List[SectionClassification]:
        """
        Get labeled classifications for training.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of SectionClassification objects with human labels
        """
        pass
    
    @abstractmethod
    def add_human_label(
        self,
        classification_id: str,
        is_relevant: bool,
        labeled_by: str
    ) -> None:
        """
        Add a human label to a classification.
        
        Args:
            classification_id: The classification ID
            is_relevant: The human-provided label
            labeled_by: User who provided the label
        """
        pass
    
    @abstractmethod
    def get_classifier_stats(
        self,
        classifier_version: Optional[str] = None
    ) -> List[Dict]:
        """
        Get classification statistics.
        
        Args:
            classifier_version: Optional filter by version
            
        Returns:
            List of dictionaries with stats per version
        """
        pass
    
    @abstractmethod
    def get_header_patterns(self, min_count: int = 10) -> List[Dict]:
        """
        Get section header patterns with relevance rates.
        
        Args:
            min_count: Minimum occurrence count
            
        Returns:
            List of dictionaries with header patterns and stats
        """
        pass
    
    @abstractmethod
    def get_accuracy_metrics(
        self,
        classifier_version: str
    ) -> Optional[Dict]:
        """
        Get accuracy metrics for a classifier version.
        
        Compares model predictions to human labels.
        
        Args:
            classifier_version: The classifier version
            
        Returns:
            Dictionary with accuracy, precision, recall, f1 or None
        """
        pass
    
    @abstractmethod
    def delete_by_job(self, job_posting_id: str) -> int:
        """
        Delete all classifications for a job posting.
        
        Args:
            job_posting_id: The job posting ID
            
        Returns:
            Number of deleted classifications
        """
        pass
