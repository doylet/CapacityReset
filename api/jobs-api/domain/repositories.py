"""
Repository Ports - Interfaces for data access (Hexagon Boundaries)

These define the contracts that adapters must implement.
The domain layer depends on these abstractions, not concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from domain.entities import (
    Job, Skill, Cluster, SkillLexiconEntry, SkillType, SectionAnnotation,
    BrandRepresentation, ProfessionalTheme, ProfessionalSurface,
    ContentGeneration, BrandLearningEvent
)


class JobRepository(ABC):
    """Port for job data access."""
    
    @abstractmethod
    async def list_jobs(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Job]:
        """List jobs with optional filters."""
        pass
    
    @abstractmethod
    async def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get a single job with all enrichments."""
        pass
    
    @abstractmethod
    async def get_jobs_by_ids(self, job_ids: List[str]) -> List[Job]:
        """Get multiple jobs for report generation."""
        pass


class SkillRepository(ABC):
    """Port for skill data access."""
    
    @abstractmethod
    async def get_skills_for_job(self, job_id: str) -> List[Skill]:
        """Get all skills extracted for a job."""
        pass
    
    @abstractmethod
    async def update_skill(self, skill: Skill) -> Skill:
        """Update skill metadata (e.g., skill_type)."""
        pass
    
    @abstractmethod
    async def add_skill_to_job(self, job_id: str, skill: Skill) -> Skill:
        """Add a new user-defined skill to a job."""
        pass
    
    @abstractmethod
    async def delete_skill(self, skill_id: str) -> bool:
        """Remove a skill from a job."""
        pass
    
    @abstractmethod
    async def approve_skill(self, skill_id: str) -> Skill:
        """Approve a suggested skill (sets is_approved=True)."""
        pass
    
    @abstractmethod
    async def reject_skill(self, skill_id: str) -> bool:
        """Reject a suggested skill (sets is_approved=False or deletes)."""
        pass
    
    @abstractmethod
    async def unapprove_skill(self, skill_id: str) -> Skill:
        """Unapprove a skill (sets is_approved=null to return to pending)."""
        pass


class SkillLexiconRepository(ABC):
    """Port for skills lexicon management."""
    
    @abstractmethod
    async def get_lexicon(self) -> List[SkillLexiconEntry]:
        """Get all skills in the lexicon."""
        pass
    
    @abstractmethod
    async def add_to_lexicon(self, entry: SkillLexiconEntry) -> SkillLexiconEntry:
        """Add a new skill to the lexicon."""
        pass
    
    @abstractmethod
    async def update_lexicon_entry(self, entry: SkillLexiconEntry) -> SkillLexiconEntry:
        """Update an existing lexicon entry."""
        pass
    
    @abstractmethod
    async def get_lexicon_by_category(self, category: str) -> List[SkillLexiconEntry]:
        """Get lexicon entries for a specific category."""
        pass


class ClusterRepository(ABC):
    """Port for cluster data access."""
    
    @abstractmethod
    async def get_cluster_for_job(self, job_id: str) -> Optional[Cluster]:
        """Get cluster assignment for a job."""
        pass
    
    @abstractmethod
    async def list_all_clusters(self) -> List[Cluster]:
        """Get all available clusters."""
        pass


class SectionAnnotationRepository(ABC):
    """Port for section annotation data access."""
    
    @abstractmethod
    async def create_annotation(self, annotation: SectionAnnotation) -> SectionAnnotation:
        """Store a new section annotation."""
        pass
    
    @abstractmethod
    async def get_annotation_by_id(self, annotation_id: str) -> Optional[SectionAnnotation]:
        """Get a single annotation."""
        pass
    
    @abstractmethod
    async def list_annotations(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[SectionAnnotation]:
        """List all annotations with pagination."""
        pass
    
    @abstractmethod
    async def get_annotations_for_job(self, job_id: str) -> List[SectionAnnotation]:
        """Get all annotations for a specific job."""
        pass
    
    @abstractmethod
    async def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        pass
    
    @abstractmethod
    async def export_training_data(self) -> List[Dict[str, Any]]:
        """Export all annotations as training data format."""
        pass


# === AI Brand Roadmap Repository Interfaces ===

class BrandRepository(ABC):
    """Port for brand representation data access."""
    
    @abstractmethod
    async def save_brand_representation(self, brand: BrandRepresentation) -> str:
        """Store brand representation, return brand_id."""
        pass
    
    @abstractmethod
    async def get_brand_by_id(self, brand_id: str) -> Optional[BrandRepresentation]:
        """Retrieve brand representation by ID."""
        pass
    
    @abstractmethod
    async def get_brand_by_user(self, user_id: str) -> Optional[BrandRepresentation]:
        """Retrieve user's current brand representation."""
        pass
    
    @abstractmethod
    async def update_brand_themes(self, brand_id: str, themes: List[ProfessionalTheme]) -> bool:
        """Update themes for existing brand."""
        pass
    
    @abstractmethod
    async def update_brand(self, brand: BrandRepresentation) -> BrandRepresentation:
        """Update an existing brand representation."""
        pass
    
    @abstractmethod
    async def get_brand_history(self, brand_id: str) -> List[BrandRepresentation]:
        """Retrieve brand evolution history."""
        pass


class ContentGenerationRepository(ABC):
    """Port for content generation data access."""
    
    @abstractmethod
    async def save_generation(self, generation: ContentGeneration) -> str:
        """Store generated content, return generation_id."""
        pass
    
    @abstractmethod
    async def get_generation_by_id(self, generation_id: str) -> Optional[ContentGeneration]:
        """Retrieve content generation by ID."""
        pass
    
    @abstractmethod
    async def get_generations_by_brand(self, brand_id: str) -> List[ContentGeneration]:
        """Retrieve all content for a brand."""
        pass
    
    @abstractmethod
    async def get_active_generation(self, brand_id: str, surface_id: str) -> Optional[ContentGeneration]:
        """Get current active content for surface."""
        pass
    
    @abstractmethod
    async def archive_generation(self, generation_id: str) -> bool:
        """Archive old generation when regenerating."""
        pass
    
    @abstractmethod
    async def update_generation(self, generation: ContentGeneration) -> ContentGeneration:
        """Update an existing content generation."""
        pass


class LearningRepository(ABC):
    """Port for brand learning event data access."""
    
    @abstractmethod
    async def save_learning_event(self, event: BrandLearningEvent) -> str:
        """Store user interaction event."""
        pass
    
    @abstractmethod
    async def get_unprocessed_events(self, brand_id: str) -> List[BrandLearningEvent]:
        """Retrieve events needing integration."""
        pass
    
    @abstractmethod
    async def mark_event_processed(self, event_id: str) -> bool:
        """Mark event as integrated into learning."""
        pass
    
    @abstractmethod
    async def get_learning_patterns(self, brand_id: str) -> Dict[str, Any]:
        """Analyze user patterns for improvement."""
        pass


class ProfessionalSurfaceRepository(ABC):
    """Port for professional surface data access."""
    
    @abstractmethod
    async def get_all_surfaces(self) -> List[ProfessionalSurface]:
        """Get all available professional surfaces."""
        pass
    
    @abstractmethod
    async def get_surface_by_id(self, surface_id: str) -> Optional[ProfessionalSurface]:
        """Get a specific surface by ID."""
        pass
    
    @abstractmethod
    async def get_surface_by_type(self, surface_type: str) -> Optional[ProfessionalSurface]:
        """Get a specific surface by type."""
        pass
    
    @abstractmethod
    async def get_active_surfaces(self) -> List[ProfessionalSurface]:
        """Get all active surfaces available for generation."""
        pass
