"""
ClusterAssignment Entity

Represents a job's cluster assignment with version tracking.
Extended to support cluster stability analysis across runs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid


@dataclass
class ClusterAssignment:
    """
    Assignment of a job to a cluster with version tracking.
    
    Attributes:
        cluster_assignment_id: Unique identifier (UUID)
        job_posting_id: Reference to the job posting
        enrichment_id: Reference to the enrichment record
        cluster_id: Cluster number within run
        cluster_name: Human-readable cluster name
        cluster_keywords: Top keywords with scores
        cluster_size: Total jobs in this cluster
        cluster_run_id: UUID for this clustering execution
        cluster_model_id: Model version used
        cluster_version: Incrementing version per job
        is_active: Whether this is the current assignment
        created_at: Assignment timestamp
    """
    
    # Required fields
    cluster_id: int
    cluster_name: str
    
    # Auto-generated fields
    cluster_assignment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # References (set during storage)
    job_posting_id: Optional[str] = None
    enrichment_id: Optional[str] = None
    
    # Cluster metadata
    cluster_keywords: List[Dict[str, Any]] = field(default_factory=list)
    cluster_size: int = 0
    
    # Version tracking (NEW)
    cluster_run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cluster_model_id: str = "v1.0-kmeans-tfidf"
    cluster_version: int = 1
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional: similarity score to cluster centroid
    similarity_score: Optional[float] = None
    
    # Optional: job metadata for display
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate assignment after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate all fields."""
        # Validate cluster_id
        if self.cluster_id < 0:
            raise ValueError("cluster_id must be >= 0")
        
        # Validate cluster_name
        if not self.cluster_name or not self.cluster_name.strip():
            raise ValueError("cluster_name cannot be empty")
        
        # Validate cluster_version
        if self.cluster_version < 1:
            raise ValueError("cluster_version must be >= 1")
        
        # Validate cluster_size
        if self.cluster_size < 0:
            raise ValueError("cluster_size must be >= 0")
        
        # Validate similarity_score if provided
        if self.similarity_score is not None:
            if not (0.0 <= self.similarity_score <= 1.0):
                raise ValueError("similarity_score must be between 0.0 and 1.0")
    
    def deactivate(self):
        """Mark this assignment as inactive (superseded by newer assignment)."""
        self.is_active = False
    
    def get_top_keywords(self, n: int = 5) -> List[str]:
        """
        Get top N keywords for this cluster.
        
        Args:
            n: Number of keywords to return
            
        Returns:
            List of keyword terms
        """
        sorted_keywords = sorted(
            self.cluster_keywords,
            key=lambda x: x.get('score', 0),
            reverse=True
        )
        return [kw.get('term', '') for kw in sorted_keywords[:n]]
    
    def get_keyword_score(self, keyword: str) -> Optional[float]:
        """Get the score for a specific keyword."""
        for kw in self.cluster_keywords:
            if kw.get('term', '').lower() == keyword.lower():
                return kw.get('score')
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'cluster_assignment_id': self.cluster_assignment_id,
            'job_posting_id': self.job_posting_id,
            'enrichment_id': self.enrichment_id,
            'cluster_id': self.cluster_id,
            'cluster_name': self.cluster_name,
            'cluster_keywords': self.cluster_keywords,
            'cluster_size': self.cluster_size,
            'cluster_run_id': self.cluster_run_id,
            'cluster_model_id': self.cluster_model_id,
            'cluster_version': self.cluster_version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'similarity_score': self.similarity_score,
            'job_title': self.job_title,
            'company_name': self.company_name
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClusterAssignment':
        """Create from dictionary."""
        return cls(
            cluster_assignment_id=data.get('cluster_assignment_id', str(uuid.uuid4())),
            job_posting_id=data.get('job_posting_id'),
            enrichment_id=data.get('enrichment_id'),
            cluster_id=data['cluster_id'],
            cluster_name=data['cluster_name'],
            cluster_keywords=data.get('cluster_keywords', []),
            cluster_size=data.get('cluster_size', 0),
            cluster_run_id=data.get('cluster_run_id', str(uuid.uuid4())),
            cluster_model_id=data.get('cluster_model_id', 'v1.0-kmeans-tfidf'),
            cluster_version=data.get('cluster_version', 1),
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow(),
            similarity_score=data.get('similarity_score'),
            job_title=data.get('job_title'),
            company_name=data.get('company_name')
        )
    
    def __eq__(self, other):
        """Check equality based on job_posting_id and cluster_run_id."""
        if not isinstance(other, ClusterAssignment):
            return False
        return (self.job_posting_id == other.job_posting_id and 
                self.cluster_run_id == other.cluster_run_id)
    
    def __hash__(self):
        """Hash based on job_posting_id and cluster_run_id."""
        return hash((self.job_posting_id, self.cluster_run_id))
    
    def __repr__(self):
        """String representation."""
        active = "active" if self.is_active else "inactive"
        return f"ClusterAssignment(job={self.job_posting_id}, cluster='{self.cluster_name}', v{self.cluster_version}, {active})"
