"""
JobEnrichment Entity

Tracks enrichment status with version information.
Extended to include model version tracking for all enrichment types.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import json


@dataclass
class JobEnrichment:
    """
    Tracks enrichment status with version information.
    
    Attributes:
        enrichment_id: Unique identifier (UUID)
        job_posting_id: Reference to the source job posting
        enrichment_type: Type of enrichment performed
        status: Current status of the enrichment
        model_id: Model identifier used
        model_version: Model version string
        enrichment_version: Denormalized version for queries
        metadata: Type-specific metadata
        error_message: Error details if failed
        processing_time_ms: Time taken to process
        retry_count: Number of retry attempts
        created_at: When enrichment was created
        updated_at: Last update timestamp
    """
    
    # Required fields
    job_posting_id: str
    enrichment_type: str
    status: str
    
    # Auto-generated fields
    enrichment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Version tracking (NEW)
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    enrichment_version: Optional[str] = None  # Denormalized: "{model_id}_{model_version}"
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    
    # Error handling
    error_message: Optional[str] = None
    
    # Processing metrics
    processing_time_ms: Optional[int] = None
    retry_count: int = 0
    
    # Validation constants
    VALID_ENRICHMENT_TYPES = {
        'skills_extraction',
        'embeddings',
        'clustering',
        'section_classification'
    }
    VALID_STATUSES = {'pending', 'processing', 'success', 'failed'}
    
    def __post_init__(self):
        """Validate enrichment after initialization."""
        self._validate()
        self._set_enrichment_version()
    
    def _validate(self):
        """Validate all fields."""
        # Validate job_posting_id
        if not self.job_posting_id or not self.job_posting_id.strip():
            raise ValueError("job_posting_id cannot be empty")
        
        # Validate enrichment_type
        if self.enrichment_type not in self.VALID_ENRICHMENT_TYPES:
            raise ValueError(f"enrichment_type must be one of: {self.VALID_ENRICHMENT_TYPES}")
        
        # Validate status
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"status must be one of: {self.VALID_STATUSES}")
        
        # Validate timestamps
        if self.created_at > self.updated_at:
            raise ValueError("created_at must be <= updated_at")
        
        # Validate retry_count
        if self.retry_count < 0:
            raise ValueError("retry_count must be >= 0")
    
    def _set_enrichment_version(self):
        """Set denormalized enrichment_version if not provided."""
        if self.enrichment_version is None and self.model_id and self.model_version:
            self.enrichment_version = f"{self.model_id}_{self.model_version}"
    
    def set_version(self, model_id: str, model_version: str):
        """
        Set version information.
        
        Args:
            model_id: The model identifier
            model_version: The model version string
        """
        self.model_id = model_id
        self.model_version = model_version
        self.enrichment_version = f"{model_id}_{model_version}"
        self.updated_at = datetime.utcnow()
    
    def mark_processing(self):
        """Mark enrichment as processing."""
        self.status = 'processing'
        self.updated_at = datetime.utcnow()
    
    def mark_success(self, metadata: Optional[Dict[str, Any]] = None, processing_time_ms: Optional[int] = None):
        """
        Mark enrichment as successful.
        
        Args:
            metadata: Optional metadata about the enrichment
            processing_time_ms: Time taken to process
        """
        self.status = 'success'
        if metadata:
            self.metadata = metadata
        if processing_time_ms is not None:
            self.processing_time_ms = processing_time_ms
        self.error_message = None
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str):
        """
        Mark enrichment as failed.
        
        Args:
            error_message: Description of the error
        """
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.updated_at = datetime.utcnow()
    
    def reset_for_retry(self):
        """Reset enrichment for a retry attempt."""
        self.status = 'pending'
        self.error_message = None
        self.updated_at = datetime.utcnow()
    
    def is_complete(self) -> bool:
        """Check if enrichment is in a terminal state."""
        return self.status in {'success', 'failed'}
    
    def needs_reprocessing(self, target_version: str) -> bool:
        """
        Check if this enrichment needs reprocessing for a target version.
        
        Args:
            target_version: The version to compare against
            
        Returns:
            True if reprocessing is needed
        """
        if self.status != 'success':
            return True
        if not self.enrichment_version:
            return True
        return self.enrichment_version != target_version
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'enrichment_id': self.enrichment_id,
            'job_posting_id': self.job_posting_id,
            'enrichment_type': self.enrichment_type,
            'status': self.status,
            'model_id': self.model_id,
            'model_version': self.model_version,
            'enrichment_version': self.enrichment_version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': json.dumps(self.metadata) if self.metadata else None,
            'error_message': self.error_message,
            'processing_time_ms': self.processing_time_ms,
            'retry_count': self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'JobEnrichment':
        """Create from dictionary."""
        metadata = data.get('metadata')
        if metadata and isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = None
        
        return cls(
            enrichment_id=data.get('enrichment_id', str(uuid.uuid4())),
            job_posting_id=data['job_posting_id'],
            enrichment_type=data['enrichment_type'],
            status=data['status'],
            model_id=data.get('model_id'),
            model_version=data.get('model_version'),
            enrichment_version=data.get('enrichment_version'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.utcnow(),
            metadata=metadata,
            error_message=data.get('error_message'),
            processing_time_ms=data.get('processing_time_ms'),
            retry_count=data.get('retry_count', 0)
        )
    
    def __repr__(self):
        """String representation."""
        version = self.enrichment_version or "no version"
        return f"JobEnrichment(job={self.job_posting_id}, type={self.enrichment_type}, status={self.status}, version={version})"
