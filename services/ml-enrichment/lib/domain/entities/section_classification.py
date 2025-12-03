"""
SectionClassification Entity

Represents classification result for a section of a job posting.
Used for section-aware skills extraction.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid


@dataclass
class SectionClassification:
    """
    Classification of a job posting section for skills relevance.
    
    Attributes:
        classification_id: Unique identifier (UUID)
        job_posting_id: Reference to the source job posting
        section_text: The section content
        section_header: Header if identifiable
        section_index: Order in document (0-based)
        is_skills_relevant: Binary classification result
        relevance_probability: Confidence in the classification (0.0-1.0)
        classifier_version: Version of classifier used
        classification_method: Method used ("rule_based" or "ml_model")
        detected_keywords: Keywords that triggered classification
        created_at: Classification timestamp
    """
    
    # Required fields
    section_text: str
    is_skills_relevant: bool
    relevance_probability: float
    classifier_version: str
    classification_method: str
    
    # Auto-generated fields
    classification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # References (set during storage)
    job_posting_id: Optional[str] = None
    
    # Section details
    section_header: Optional[str] = None
    section_index: int = 0
    
    # Additional metadata
    section_word_count: Optional[int] = None
    section_char_count: Optional[int] = None
    detected_keywords: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Training data labeling (optional)
    human_label: Optional[bool] = None
    labeled_by: Optional[str] = None
    labeled_at: Optional[datetime] = None
    
    # Validation constants
    VALID_METHODS = {"rule_based", "ml_model"}
    MIN_SECTION_LENGTH = 10
    
    def __post_init__(self):
        """Validate classification after initialization."""
        self._validate()
        self._compute_counts()
    
    def _validate(self):
        """Validate all fields."""
        # Validate section_text
        if not self.section_text or not self.section_text.strip():
            raise ValueError("section_text cannot be empty")
        
        # Validate relevance_probability
        if not (0.0 <= self.relevance_probability <= 1.0):
            raise ValueError("relevance_probability must be between 0.0 and 1.0")
        
        # Validate section_index
        if self.section_index < 0:
            raise ValueError("section_index must be >= 0")
        
        # Validate classification_method
        if self.classification_method not in self.VALID_METHODS:
            raise ValueError(f"classification_method must be one of: {self.VALID_METHODS}")
    
    def _compute_counts(self):
        """Compute word and character counts if not provided."""
        if self.section_char_count is None:
            self.section_char_count = len(self.section_text)
        if self.section_word_count is None:
            self.section_word_count = len(self.section_text.split())
    
    def add_human_label(self, is_relevant: bool, labeled_by: str):
        """
        Add a human label for training data.
        
        Args:
            is_relevant: Human-provided relevance label
            labeled_by: User who provided the label
        """
        self.human_label = is_relevant
        self.labeled_by = labeled_by
        self.labeled_at = datetime.utcnow()
    
    def is_correctly_classified(self) -> Optional[bool]:
        """
        Check if the model prediction matches human label.
        
        Returns:
            True if matches, False if not, None if no human label
        """
        if self.human_label is None:
            return None
        return self.is_skills_relevant == self.human_label
    
    def get_confidence_category(self) -> str:
        """
        Get confidence category for the classification.
        
        Returns:
            "high", "medium", or "low"
        """
        if self.relevance_probability >= 0.8:
            return "high"
        elif self.relevance_probability >= 0.5:
            return "medium"
        else:
            return "low"
    
    def add_detected_keyword(self, keyword: str):
        """Add a keyword that triggered classification."""
        if keyword and keyword not in self.detected_keywords:
            self.detected_keywords.append(keyword)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'classification_id': self.classification_id,
            'job_posting_id': self.job_posting_id,
            'section_text': self.section_text,
            'section_header': self.section_header,
            'section_index': self.section_index,
            'is_skills_relevant': self.is_skills_relevant,
            'relevance_probability': self.relevance_probability,
            'classifier_version': self.classifier_version,
            'classification_method': self.classification_method,
            'section_word_count': self.section_word_count,
            'section_char_count': self.section_char_count,
            'detected_keywords': self.detected_keywords,
            'created_at': self.created_at.isoformat(),
            'human_label': self.human_label,
            'labeled_by': self.labeled_by,
            'labeled_at': self.labeled_at.isoformat() if self.labeled_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SectionClassification':
        """Create from dictionary."""
        return cls(
            classification_id=data.get('classification_id', str(uuid.uuid4())),
            job_posting_id=data.get('job_posting_id'),
            section_text=data['section_text'],
            section_header=data.get('section_header'),
            section_index=data.get('section_index', 0),
            is_skills_relevant=data['is_skills_relevant'],
            relevance_probability=data['relevance_probability'],
            classifier_version=data['classifier_version'],
            classification_method=data['classification_method'],
            section_word_count=data.get('section_word_count'),
            section_char_count=data.get('section_char_count'),
            detected_keywords=data.get('detected_keywords', []),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow(),
            human_label=data.get('human_label'),
            labeled_by=data.get('labeled_by'),
            labeled_at=datetime.fromisoformat(data['labeled_at']) if data.get('labeled_at') else None
        )
    
    def __repr__(self):
        """String representation."""
        header = self.section_header or f"Section {self.section_index}"
        relevant = "relevant" if self.is_skills_relevant else "not relevant"
        return f"SectionClassification('{header}', {relevant}, prob={self.relevance_probability:.2f})"
