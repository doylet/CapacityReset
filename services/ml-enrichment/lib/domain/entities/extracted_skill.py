"""
ExtractedSkill Entity

Represents a skill extracted from a job posting with enhanced metadata.
Extended from the base job_skills model to include source tracking and confidence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class ExtractedSkill:
    """
    Skill identified from a job posting with extraction details.
    
    Attributes:
        skill_id: Unique identifier (UUID)
        job_posting_id: Reference to the source job posting
        enrichment_id: Reference to the enrichment record
        skill_name: Canonical skill name (normalized)
        skill_category: Category classification
        confidence_score: Final computed confidence (0.0-1.0)
        source_strategies: Which extraction strategies found this skill
        section_relevance_score: Relevance of the section where skill was found
        extracted_from_section: Section name if identified
        context_snippet: Surrounding text context
        position_in_text: Character offset in original text
        created_at: Extraction timestamp
    """
    
    # Required fields
    skill_name: str
    skill_category: str
    confidence_score: float
    
    # Auto-generated fields
    skill_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # References (set during storage)
    job_posting_id: Optional[str] = None
    enrichment_id: Optional[str] = None
    
    # Provenance tracking
    source_strategies: List[str] = field(default_factory=list)
    
    # Section relevance (Phase 2 - Section-Aware Extraction)
    section_relevance_score: Optional[float] = None
    extracted_from_section: Optional[str] = None
    
    # Context information
    context_snippet: Optional[str] = None
    position_in_text: Optional[int] = None
    
    # Original text (before normalization)
    original_text: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Approval status
    is_approved: Optional[bool] = None  # None = pending, True = approved, False = rejected
    
    # Version tracking
    enrichment_version: Optional[str] = None
    
    # Validation constants
    MAX_SKILL_NAME_LENGTH = 100
    MAX_CONTEXT_LENGTH = 500
    VALID_STRATEGIES = {
        "lexicon", "semantic", "pattern", "ner", "noun_chunk", 
        "alias", "ml_model", "manual"
    }
    
    def __post_init__(self):
        """Validate skill after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate all fields."""
        # Validate skill_name
        if not self.skill_name or not self.skill_name.strip():
            raise ValueError("skill_name cannot be empty")
        if len(self.skill_name) > self.MAX_SKILL_NAME_LENGTH:
            raise ValueError(f"skill_name exceeds max length of {self.MAX_SKILL_NAME_LENGTH}")
        
        # Validate skill_category
        if not self.skill_category or not self.skill_category.strip():
            raise ValueError("skill_category cannot be empty")
        
        # Validate confidence_score
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        
        # Validate source_strategies
        if self.source_strategies:
            for strategy in self.source_strategies:
                if strategy not in self.VALID_STRATEGIES:
                    raise ValueError(f"Invalid strategy '{strategy}'. Valid: {self.VALID_STRATEGIES}")
        
        # Validate section_relevance_score if provided
        if self.section_relevance_score is not None:
            if not (0.0 <= self.section_relevance_score <= 1.0):
                raise ValueError("section_relevance_score must be between 0.0 and 1.0")
        
        # Truncate context if too long
        if self.context_snippet and len(self.context_snippet) > self.MAX_CONTEXT_LENGTH:
            self.context_snippet = self.context_snippet[:self.MAX_CONTEXT_LENGTH]
    
    def add_strategy(self, strategy: str):
        """Add an extraction strategy that found this skill."""
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(f"Invalid strategy '{strategy}'")
        if strategy not in self.source_strategies:
            self.source_strategies.append(strategy)
    
    def set_section_relevance(self, score: float, section_name: Optional[str] = None):
        """Set section relevance information."""
        if not (0.0 <= score <= 1.0):
            raise ValueError("score must be between 0.0 and 1.0")
        self.section_relevance_score = score
        self.extracted_from_section = section_name
    
    def approve(self):
        """Mark this skill as approved."""
        self.is_approved = True
    
    def reject(self):
        """Mark this skill as rejected."""
        self.is_approved = False
    
    def get_combined_confidence(self) -> float:
        """
        Get combined confidence score considering section relevance.
        
        If section relevance is set, combines with base confidence.
        """
        if self.section_relevance_score is not None:
            # Weight section relevance into final confidence
            return self.confidence_score * 0.7 + self.section_relevance_score * 0.3
        return self.confidence_score
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'skill_id': self.skill_id,
            'job_posting_id': self.job_posting_id,
            'enrichment_id': self.enrichment_id,
            'skill_name': self.skill_name,
            'skill_category': self.skill_category,
            'confidence_score': self.confidence_score,
            'source_strategies': self.source_strategies,
            'section_relevance_score': self.section_relevance_score,
            'extracted_from_section': self.extracted_from_section,
            'context_snippet': self.context_snippet,
            'position_in_text': self.position_in_text,
            'original_text': self.original_text,
            'created_at': self.created_at.isoformat(),
            'is_approved': self.is_approved,
            'enrichment_version': self.enrichment_version
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExtractedSkill':
        """Create from dictionary."""
        return cls(
            skill_id=data.get('skill_id', str(uuid.uuid4())),
            job_posting_id=data.get('job_posting_id'),
            enrichment_id=data.get('enrichment_id'),
            skill_name=data['skill_name'],
            skill_category=data['skill_category'],
            confidence_score=data['confidence_score'],
            source_strategies=data.get('source_strategies', []),
            section_relevance_score=data.get('section_relevance_score'),
            extracted_from_section=data.get('extracted_from_section'),
            context_snippet=data.get('context_snippet'),
            position_in_text=data.get('position_in_text'),
            original_text=data.get('original_text'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow(),
            is_approved=data.get('is_approved'),
            enrichment_version=data.get('enrichment_version')
        )
    
    def __eq__(self, other):
        """Check equality based on skill_name (case-insensitive)."""
        if not isinstance(other, ExtractedSkill):
            return False
        return self.skill_name.lower() == other.skill_name.lower()
    
    def __hash__(self):
        """Hash based on lowercase skill_name."""
        return hash(self.skill_name.lower())
    
    def __repr__(self):
        """String representation."""
        strategies = ', '.join(self.source_strategies) if self.source_strategies else 'unknown'
        return f"ExtractedSkill('{self.skill_name}', category='{self.skill_category}', confidence={self.confidence_score:.2f}, strategies=[{strategies}])"
