"""
Use Cases - Application layer business logic (Hexagon Application)

These orchestrate domain entities and call repositories through ports.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from domain.entities import Job, Skill, SkillLexiconEntry, SkillType, SectionAnnotation, AnnotationLabel
from domain.repositories import JobRepository, SkillRepository, SkillLexiconRepository, ClusterRepository, SectionAnnotationRepository


class ListJobsUseCase:
    """Use case: List and filter job postings."""
    
    def __init__(self, job_repo: JobRepository, cluster_repo: ClusterRepository):
        self.job_repo = job_repo
        self.cluster_repo = cluster_repo
    
    async def execute(
        self,
        limit: int = 100,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        location: Optional[str] = None,
        cluster_id: Optional[int] = None,
        skill_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List jobs with filters.
        
        Returns:
            {
                'jobs': List[Job],
                'total': int,
                'has_more': bool
            }
        """
        filters = {}
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        if location:
            filters['location'] = location
        if cluster_id:
            filters['cluster_id'] = cluster_id
        if skill_name:
            filters['skill_name'] = skill_name
        
        jobs = await self.job_repo.list_jobs(limit=limit + 1, offset=offset, filters=filters)
        
        has_more = len(jobs) > limit
        if has_more:
            jobs = jobs[:limit]
        
        return {
            'jobs': jobs,
            'total': len(jobs),
            'has_more': has_more
        }


class GetJobDetailUseCase:
    """Use case: Get detailed job information with skills."""
    
    def __init__(
        self,
        job_repo: JobRepository,
        skill_repo: SkillRepository,
        cluster_repo: ClusterRepository
    ):
        self.job_repo = job_repo
        self.skill_repo = skill_repo
        self.cluster_repo = cluster_repo
    
    async def execute(self, job_id: str) -> Optional[Job]:
        """Get job with all enrichments (skills, cluster)."""
        job = await self.job_repo.get_job_by_id(job_id)
        if not job:
            return None
        
        # Load skills
        skills = await self.skill_repo.get_skills_for_job(job_id)
        job.skills = skills
        
        # Load cluster
        cluster = await self.cluster_repo.get_cluster_for_job(job_id)
        job.cluster = cluster
        
        return job


class UpdateSkillUseCase:
    """Use case: Update skill metadata (e.g., skill type)."""
    
    def __init__(self, skill_repo: SkillRepository):
        self.skill_repo = skill_repo
    
    async def execute(
        self,
        skill_id: str,
        skill_type: Optional[SkillType] = None
    ) -> Skill:
        """Update skill metadata."""
        # In a real implementation, we'd fetch the skill first
        # For now, assume we're passed the full skill object
        skill = Skill(
            skill_id=skill_id,
            job_posting_id="",  # Would be fetched
            skill_name="",
            skill_category="",
            confidence_score=0.0,
            context_snippet="",
            extraction_method="",
            skill_type=skill_type
        )
        
        return await self.skill_repo.update_skill(skill)


class AddSkillToJobUseCase:
    """Use case: Add user-defined skill to a job."""
    
    def __init__(self, skill_repo: SkillRepository, lexicon_repo: SkillLexiconRepository):
        self.skill_repo = skill_repo
        self.lexicon_repo = lexicon_repo
    
    async def execute(
        self,
        job_id: str,
        skill_name: str,
        skill_category: str,
        skill_type: SkillType,
        context_snippet: str
    ) -> Skill:
        """
        Add a new skill to a job and optionally to the lexicon.
        
        This reinforces the extraction model by teaching it new skills.
        """
        import uuid
        
        # Create new skill
        skill = Skill(
            skill_id=str(uuid.uuid4()),
            job_posting_id=job_id,
            skill_name=skill_name,
            skill_category=skill_category,
            confidence_score=1.0,  # User-defined = high confidence
            context_snippet=context_snippet,
            extraction_method='user_defined',
            skill_type=skill_type,
            is_approved=True,  # User-defined skills are automatically approved
            created_at=datetime.utcnow()
        )
        
        # Add to job
        saved_skill = await self.skill_repo.add_skill_to_job(job_id, skill)
        
        # Add to lexicon for model reinforcement
        lexicon_entry = SkillLexiconEntry(
            skill_name=skill_name,
            skill_category=skill_category,
            skill_type=skill_type,
            added_by_user=True,
            usage_count=1,
            created_at=datetime.utcnow()
        )
        await self.lexicon_repo.add_to_lexicon(lexicon_entry)
        
        return saved_skill


class GenerateJobsReportUseCase:
    """Use case: Generate ML analysis report for selected jobs."""
    
    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo
    
    async def execute(self, job_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze multiple jobs and generate insights report.
        
        Returns aggregate statistics, common skills, trends, etc.
        """
        jobs = await self.job_repo.get_jobs_by_ids(job_ids)
        
        # Aggregate statistics
        total_jobs = len(jobs)
        all_skills = [skill for job in jobs for skill in job.skills]
        unique_skills = len(set(s.skill_name for s in all_skills))
        
        # Top skills across selected jobs
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill.skill_name] = skill_counts.get(skill.skill_name, 0) + 1
        
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Category distribution
        category_counts = {}
        for skill in all_skills:
            category_counts[skill.skill_category] = category_counts.get(skill.skill_category, 0) + 1
        
        # Companies
        companies = list(set(job.company_name for job in jobs))
        
        return {
            'total_jobs': total_jobs,
            'total_skills': len(all_skills),
            'unique_skills': unique_skills,
            'top_skills': [{'skill': name, 'count': count} for name, count in top_skills],
            'categories': category_counts,
            'companies': companies,
            'date_range': {
                'from': min(job.job_posted_date for job in jobs) if jobs else None,
                'to': max(job.job_posted_date for job in jobs) if jobs else None
            }
        }


class ReinforceLexiconUseCase:
    """Use case: Manage and update the skills lexicon."""
    
    def __init__(self, lexicon_repo: SkillLexiconRepository):
        self.lexicon_repo = lexicon_repo
    
    async def execute(self) -> List[SkillLexiconEntry]:
        """Get current lexicon for review/editing."""
        return await self.lexicon_repo.get_lexicon()
    
    async def add_skill(
        self,
        skill_name: str,
        skill_category: str,
        skill_type: SkillType
    ) -> SkillLexiconEntry:
        """Add new skill to lexicon."""
        entry = SkillLexiconEntry(
            skill_name=skill_name,
            skill_category=skill_category,
            skill_type=skill_type,
            added_by_user=True,
            usage_count=0,
            created_at=datetime.utcnow()
        )
        return await self.lexicon_repo.add_to_lexicon(entry)
    
    async def get_lexicon(self) -> List[SkillLexiconEntry]:
        """Get all lexicon entries."""
        return await self.lexicon_repo.get_lexicon()


class ApproveSkillUseCase:
    """Use case: Approve ML-suggested skill and add to lexicon."""
    
    def __init__(self, skill_repo: SkillRepository, lexicon_repo: SkillLexiconRepository):
        self.skill_repo = skill_repo
        self.lexicon_repo = lexicon_repo
    
    async def execute(self, skill_id: str) -> Skill:
        """
        Approve a suggested skill and reinforce the lexicon.
        
        This teaches the ML model that this extraction was correct.
        """
        # Approve the skill (sets is_approved=True)
        skill = await self.skill_repo.approve_skill(skill_id)
        
        # Add to lexicon for model reinforcement
        lexicon_entry = SkillLexiconEntry(
            skill_name=skill.skill_name,
            skill_category=skill.skill_category,
            skill_type=skill.skill_type,
            added_by_user=False,  # ML-extracted, human-approved
            usage_count=1,
            created_at=datetime.utcnow()
        )
        await self.lexicon_repo.add_to_lexicon(lexicon_entry)
        
        return skill


class RejectSkillUseCase:
    """Use case: Reject ML-suggested skill and remove it."""
    
    def __init__(self, skill_repo: SkillRepository):
        self.skill_repo = skill_repo
    
    async def execute(self, skill_id: str) -> bool:
        """
        Reject a suggested skill and remove it.
        
        This teaches the ML model that this extraction was incorrect.
        """
        return await self.skill_repo.reject_skill(skill_id)


class UnapproveSkillUseCase:
    """Use case: Return an approved skill to pending state."""
    
    def __init__(self, skill_repo: SkillRepository):
        self.skill_repo = skill_repo
    
    async def execute(self, skill_id: str) -> Skill:
        """
        Unapprove a skill by setting is_approved back to null.
        
        This returns the skill to pending state for re-review.
        """
        return await self.skill_repo.unapprove_skill(skill_id)


class CreateAnnotationUseCase:
    """Use case: Create a new section annotation for ML training."""
    
    def __init__(
        self,
        annotation_repo: SectionAnnotationRepository,
        job_repo: JobRepository
    ):
        self.annotation_repo = annotation_repo
        self.job_repo = job_repo
    
    async def execute(
        self,
        job_id: str,
        section_text: str,
        section_start_index: int,
        section_end_index: int,
        label: AnnotationLabel,
        annotator_id: str,
        notes: Optional[str] = None
    ) -> SectionAnnotation:
        """Create and store a new annotation."""
        
        # Validate job exists
        job = await self.job_repo.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Determine if this section should be used for skill extraction
        contains_skills = label in [
            AnnotationLabel.SKILLS_SECTION,
            AnnotationLabel.RESPONSIBILITIES,
            AnnotationLabel.QUALIFICATIONS,
            AnnotationLabel.REQUIREMENTS,
            AnnotationLabel.EXPERIENCE,
            AnnotationLabel.NICE_TO_HAVE
        ]
        
        # Create annotation
        annotation = SectionAnnotation(
            annotation_id=str(uuid.uuid4()),
            job_posting_id=job_id,
            section_text=section_text,
            section_start_index=section_start_index,
            section_end_index=section_end_index,
            label=label,
            contains_skills=contains_skills,
            annotator_id=annotator_id,
            notes=notes
        )
        
        return await self.annotation_repo.create_annotation(annotation)


class GetAnnotationsByJobUseCase:
    """Use case: Get all annotations for a job."""
    
    def __init__(self, annotation_repo: SectionAnnotationRepository):
        self.annotation_repo = annotation_repo
    
    async def execute(self, job_id: str) -> List[SectionAnnotation]:
        """Get all annotations for a specific job posting."""
        return await self.annotation_repo.get_annotations_for_job(job_id)


class ListAnnotationsUseCase:
    """Use case: List all annotations with pagination."""
    
    def __init__(self, annotation_repo: SectionAnnotationRepository):
        self.annotation_repo = annotation_repo
    
    async def execute(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """List annotations with pagination."""
        annotations = await self.annotation_repo.list_annotations(
            limit=limit + 1,
            offset=offset
        )
        
        has_more = len(annotations) > limit
        if has_more:
            annotations = annotations[:limit]
        
        return {
            'annotations': annotations,
            'total': len(annotations),
            'has_more': has_more
        }


class DeleteAnnotationUseCase:
    """Use case: Delete an annotation."""
    
    def __init__(self, annotation_repo: SectionAnnotationRepository):
        self.annotation_repo = annotation_repo
    
    async def execute(self, annotation_id: str) -> bool:
        """Delete an annotation by ID."""
        return await self.annotation_repo.delete_annotation(annotation_id)


class ExportTrainingDataUseCase:
    """Use case: Export annotations as ML training data."""
    
    def __init__(self, annotation_repo: SectionAnnotationRepository):
        self.annotation_repo = annotation_repo
    
    async def execute(self) -> Dict[str, Any]:
        """
        Export all annotations in ML training format.
        
        Returns:
            {
                'format': 'section_classification_v1',
                'total_annotations': int,
                'annotations': List[dict],
                'label_distribution': Dict[str, int]
            }
        """
        annotations = await self.annotation_repo.export_training_data()
        
        return {
            'format': 'section_classification_v1',
            'total_annotations': len(annotations),
            'annotations': annotations,
            'label_distribution': self._calculate_label_distribution(annotations)
        }
    
    def _calculate_label_distribution(self, annotations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate how many annotations per label."""
        distribution = {}
        for ann in annotations:
            label = ann['label']
            distribution[label] = distribution.get(label, 0) + 1
        return distribution
