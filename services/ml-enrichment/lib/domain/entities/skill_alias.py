"""
SkillAlias Entity

Represents a mapping from skill alias to canonical skill name.
Used for skill normalization during extraction.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class SkillAlias:
    """
    Mapping from skill alias to canonical name.
    
    Attributes:
        alias_id: Unique identifier (UUID)
        alias_text: The abbreviated or alternate name (e.g., "K8s", "GCP")
        canonical_name: The standardized canonical skill name
        skill_category: Category of the canonical skill
        source: Origin of the alias ("manual", "user_feedback", "auto_detected")
        confidence: Confidence in this mapping (0.0-1.0)
        created_at: When this alias was created
        created_by: User who added the alias (if manual)
        is_active: Whether this alias is currently active
        usage_count: How many times this alias was resolved
        last_used_at: Last time this alias was used
    """
    
    # Required fields
    alias_text: str
    canonical_name: str
    skill_category: str
    
    # Auto-generated fields
    alias_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Metadata
    source: str = "manual"  # "manual" | "user_feedback" | "auto_detected"
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Usage tracking
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    
    # Validation constants
    MAX_ALIAS_LENGTH = 50
    MAX_CANONICAL_LENGTH = 100
    VALID_SOURCES = {"manual", "user_feedback", "auto_detected"}
    
    def __post_init__(self):
        """Validate alias after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate all fields."""
        # Validate alias_text
        if not self.alias_text or not self.alias_text.strip():
            raise ValueError("alias_text cannot be empty")
        if len(self.alias_text) > self.MAX_ALIAS_LENGTH:
            raise ValueError(f"alias_text exceeds max length of {self.MAX_ALIAS_LENGTH}")
        
        # Validate canonical_name
        if not self.canonical_name or not self.canonical_name.strip():
            raise ValueError("canonical_name cannot be empty")
        if len(self.canonical_name) > self.MAX_CANONICAL_LENGTH:
            raise ValueError(f"canonical_name exceeds max length of {self.MAX_CANONICAL_LENGTH}")
        
        # Validate skill_category
        if not self.skill_category or not self.skill_category.strip():
            raise ValueError("skill_category cannot be empty")
        
        # Validate confidence
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        
        # Validate source
        if self.source not in self.VALID_SOURCES:
            raise ValueError(f"source must be one of: {self.VALID_SOURCES}")
    
    def record_usage(self):
        """Record that this alias was used for resolution."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate this alias without deletion."""
        self.is_active = False
    
    def activate(self):
        """Reactivate this alias."""
        self.is_active = True
    
    def update_confidence(self, new_confidence: float):
        """Update the confidence score."""
        if not (0.0 <= new_confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        self.confidence = new_confidence
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'alias_id': self.alias_id,
            'alias_text': self.alias_text,
            'canonical_name': self.canonical_name,
            'skill_category': self.skill_category,
            'source': self.source,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SkillAlias':
        """Create from dictionary."""
        return cls(
            alias_id=data.get('alias_id', str(uuid.uuid4())),
            alias_text=data['alias_text'],
            canonical_name=data['canonical_name'],
            skill_category=data['skill_category'],
            source=data.get('source', 'manual'),
            confidence=data.get('confidence', 1.0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow(),
            created_by=data.get('created_by'),
            is_active=data.get('is_active', True),
            usage_count=data.get('usage_count', 0),
            last_used_at=datetime.fromisoformat(data['last_used_at']) if data.get('last_used_at') else None
        )
    
    def __eq__(self, other):
        """Check equality based on alias_text (case-insensitive)."""
        if not isinstance(other, SkillAlias):
            return False
        return self.alias_text.lower() == other.alias_text.lower()
    
    def __hash__(self):
        """Hash based on lowercase alias_text."""
        return hash(self.alias_text.lower())
    
    def __repr__(self):
        """String representation."""
        return f"SkillAlias('{self.alias_text}' -> '{self.canonical_name}', category='{self.skill_category}')"
