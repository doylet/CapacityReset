"""
Domain Entities - Core business objects (Hexagon Core)

These are framework-agnostic, pure Python classes representing
the business domain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class SkillType(str, Enum):
    """Skill type classification."""
    GENERAL = "general"
    SPECIALISED = "specialised"
    TRANSFERRABLE = "transferrable"


@dataclass
class Skill:
    """Extracted skill from a job posting."""
    skill_id: str
    job_posting_id: str
    skill_name: str
    skill_category: str
    confidence_score: float
    context_snippet: str
    extraction_method: str
    skill_type: Optional[SkillType] = None  # User-editable metadata
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate skill data."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0 and 1")
        if not self.skill_name.strip():
            raise ValueError("Skill name cannot be empty")


@dataclass
class Cluster:
    """Job cluster assignment."""
    cluster_id: int
    cluster_name: str
    cluster_keywords: List[Dict[str, Any]]  # List of {"score": float, "term": str}
    cluster_size: int


@dataclass
class Job:
    """Job posting with enrichments."""
    job_posting_id: str
    job_title: str
    company_name: str
    job_location: str
    job_summary: str
    job_description_formatted: str
    job_posted_date: datetime
    company_url: Optional[str] = None
    company_logo: Optional[str] = None
    job_url: Optional[str] = None
    skills: List[Skill] = field(default_factory=list)
    cluster: Optional[Cluster] = None
    skills_count: int = 0  # Precomputed count from database
    
    def add_skill(self, skill: Skill) -> None:
        """Add a skill to this job."""
        if skill.job_posting_id != self.job_posting_id:
            raise ValueError("Skill does not belong to this job")
        self.skills.append(skill)
    
    def get_skills_by_category(self, category: str) -> List[Skill]:
        """Get all skills in a specific category."""
        return [s for s in self.skills if s.skill_category == category]
    
    def get_high_confidence_skills(self, threshold: float = 0.7) -> List[Skill]:
        """Get skills above confidence threshold."""
        return [s for s in self.skills if s.confidence_score >= threshold]


@dataclass
class SkillLexiconEntry:
    """Entry in the skills lexicon for model reinforcement."""
    skill_name: str
    skill_category: str
    skill_type: SkillType
    added_by_user: bool = False
    usage_count: int = 0
    created_at: Optional[datetime] = None
