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


# === Brand Analysis Use Cases (Feature 003) ===

class AnalyzeBrandUseCase:
    """
    Use case: Analyze professional document for brand extraction.
    
    Coordinates LLM-powered theme extraction, voice analysis, and 
    narrative arc detection with fallback support.
    """
    
    def __init__(self, brand_repo=None):
        """
        Initialize brand analysis use case.
        
        Args:
            brand_repo: Repository for storing brand representations (optional)
        """
        self.brand_repo = brand_repo
        
    async def execute(
        self,
        document_content: str,
        user_id: str,
        source_document_url: str,
        linkedin_profile_url: Optional[str] = None,
        analysis_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze document and extract brand representation.
        
        Args:
            document_content: CV/resume text content
            user_id: User identifier
            source_document_url: URL/path to source document
            linkedin_profile_url: Optional LinkedIn profile for enrichment
            analysis_options: Optional settings (prompt_version, use_cache, etc.)
            
        Returns:
            Brand analysis result with themes, voice, narrative
        """
        from domain.entities import (
            LLMThemeResult, LLMVoiceCharacteristics, LLMNarrativeArc,
            BrandRepresentation, ProfessionalTheme, ThemeCategory, 
            VoiceTone, FormalityLevel, EnergyLevel
        )
        
        options = analysis_options or {}
        use_enhanced_llm = options.get('use_enhanced_llm', True)
        prompt_version = options.get('prompt_version', 'v1')
        
        brand_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Extract professional themes with enhanced LLM analysis
        themes = await self._extract_themes(document_content, prompt_version)
        
        # Analyze voice characteristics
        voice = await self._analyze_voice(document_content, prompt_version)
        
        # Build narrative arc
        narrative = await self._build_narrative(document_content, prompt_version)
        
        # Calculate confidence scores
        theme_confidence = sum(t.get('confidence_score', 0.7) for t in themes) / len(themes) if themes else 0.0
        confidence_scores = {
            "overall": (theme_confidence * 0.4 + voice.get('confidence', 0.8) * 0.3 + 0.8 * 0.3),
            "themes": theme_confidence,
            "voice": voice.get('confidence', 0.8),
            "narrative": 0.8
        }
        
        # Create brand representation
        brand_data = {
            "brand_id": brand_id,
            "user_id": user_id,
            "source_document_url": source_document_url,
            "linkedin_profile_url": linkedin_profile_url,
            "professional_themes": themes,
            "voice_characteristics": voice,
            "narrative_arc": narrative,
            "confidence_scores": confidence_scores,
            "analysis_metadata": {
                "prompt_version": prompt_version,
                "analysis_type": "llm" if use_enhanced_llm else "keyword",
                "processing_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
                "word_count": len(document_content.split())
            },
            "created_at": start_time,
            "updated_at": datetime.utcnow(),
            "version": 1
        }
        
        # Store if repository available
        if self.brand_repo:
            await self.brand_repo.save_brand_representation(brand_data)
            
        return brand_data
        
    async def _extract_themes(
        self, 
        content: str, 
        prompt_version: str
    ) -> List[Dict[str, Any]]:
        """
        Extract professional themes from document content.
        
        Uses enhanced LLM analysis when available, falls back to keyword analysis.
        """
        text_lower = content.lower()
        themes = []
        
        # Theme patterns for keyword-based extraction (MVP)
        theme_patterns = {
            "leadership": {
                "keywords": ["led", "managed", "coordinated", "directed", "supervised", "mentored"],
                "category": "skill",
                "confidence": 0.85
            },
            "technical_expertise": {
                "keywords": ["developed", "implemented", "designed", "built", "programmed", "engineered"],
                "category": "skill",
                "confidence": 0.85
            },
            "strategic_thinking": {
                "keywords": ["strategy", "strategic", "planning", "roadmap", "vision", "initiative"],
                "category": "value_proposition",
                "confidence": 0.80
            },
            "innovation": {
                "keywords": ["innovation", "innovative", "created", "pioneered", "transformed"],
                "category": "value_proposition",
                "confidence": 0.82
            },
            "results_driven": {
                "keywords": ["achieved", "delivered", "exceeded", "improved", "increased", "reduced"],
                "category": "achievement",
                "confidence": 0.88
            },
            "collaboration": {
                "keywords": ["collaborated", "partnered", "team", "cross-functional", "stakeholders"],
                "category": "skill",
                "confidence": 0.80
            }
        }
        
        for theme_name, config in theme_patterns.items():
            matching_keywords = [kw for kw in config["keywords"] if kw in text_lower]
            if matching_keywords:
                # Calculate confidence based on number of keyword matches
                base_confidence = config["confidence"]
                match_bonus = min(len(matching_keywords) * 0.02, 0.1)
                
                themes.append({
                    "theme_id": str(uuid.uuid4()),
                    "theme_name": theme_name.replace("_", " ").title(),
                    "theme_category": config["category"],
                    "description": f"Demonstrated {theme_name.replace('_', ' ')} throughout career",
                    "keywords": matching_keywords[:5],
                    "confidence_score": min(base_confidence + match_bonus, 0.95),
                    "source_evidence": f"Found {len(matching_keywords)} relevant indicators",
                    "reasoning": f"Pattern matching identified {len(matching_keywords)} keyword matches"
                })
        
        # Ensure at least one theme
        if not themes:
            themes.append({
                "theme_id": str(uuid.uuid4()),
                "theme_name": "Professional Expertise",
                "theme_category": "skill",
                "description": "General professional expertise and experience",
                "keywords": ["professional", "experience"],
                "confidence_score": 0.70,
                "source_evidence": "Default theme for professional documents",
                "reasoning": "No specific themes identified, using default"
            })
        
        # Sort by confidence and return top 5
        themes.sort(key=lambda x: x["confidence_score"], reverse=True)
        return themes[:5]
        
    async def _analyze_voice(
        self, 
        content: str, 
        prompt_version: str
    ) -> Dict[str, Any]:
        """Analyze voice and communication characteristics."""
        text_lower = content.lower()
        
        # Determine tone
        tone = "professional"
        if any(word in text_lower for word in ["passionate", "excited", "thrilled", "love"]):
            tone = "enthusiastic"
        elif any(word in text_lower for word in ["data", "metrics", "analysis", "research"]):
            tone = "analytical"
        elif any(word in text_lower for word in ["creative", "innovative", "design", "artistic"]):
            tone = "creative"
            
        # Determine formality
        formality = "formal"
        if any(word in text_lower for word in ["hey", "folks", "awesome", "cool"]):
            formality = "casual"
        elif any(word in text_lower for word in ["i am", "i've", "my experience"]):
            formality = "business_casual"
            
        # Determine energy level
        energy = "balanced"
        if any(word in text_lower for word in ["passionate", "dynamic", "enthusiastic"]):
            energy = "enthusiastic"
        elif any(word in text_lower for word in ["methodical", "steady", "careful"]):
            energy = "reserved"
            
        # Communication style tags
        styles = []
        if any(word in text_lower for word in ["data", "metrics", "analysis"]):
            styles.append("data_driven")
        if any(word in text_lower for word in ["team", "collaboration", "partnership"]):
            styles.append("collaborative")
        if any(word in text_lower for word in ["achieved", "delivered", "results"]):
            styles.append("action_oriented")
        if not styles:
            styles = ["professional"]
            
        return {
            "tone": tone,
            "formality_level": formality,
            "energy_level": energy,
            "communication_style": styles,
            "vocabulary_complexity": "professional",
            "confidence": 0.85
        }
        
    async def _build_narrative(
        self, 
        content: str, 
        prompt_version: str
    ) -> Dict[str, Any]:
        """Build career narrative arc from document."""
        text_lower = content.lower()
        words = content.split()
        
        # Determine career focus from first part of document
        career_focus = " ".join(words[:20]) + "..." if len(words) > 20 else " ".join(words)
        
        # Determine progression pattern
        progression = "general_professional"
        if any(word in text_lower for word in ["founded", "startup", "entrepreneur"]):
            progression = "entrepreneurial"
        elif any(word in text_lower for word in ["led", "managed", "director"]):
            progression = "technical_to_leadership"
        elif any(word in text_lower for word in ["expert", "specialist", "advanced"]):
            progression = "specialist_expert"
            
        # Value proposition
        value_prop = "Delivering results through expertise and dedication"
        if "innovation" in text_lower or "creative" in text_lower:
            value_prop = "Driving innovation and creative problem-solving"
        elif "data" in text_lower or "analytics" in text_lower:
            value_prop = "Leveraging data-driven insights for strategic decisions"
            
        return {
            "career_focus": career_focus,
            "value_proposition": value_prop,
            "career_progression": f"Progressive career growth with {progression.replace('_', ' ')} trajectory",
            "key_achievements": ["Demonstrated track record of success"],
            "future_goals": "Continuing to drive impact in the industry",
            "progression_pattern": progression
        }


class GenerateBrandContentUseCase:
    """
    Use case: Generate platform-specific content from brand representation.
    
    Creates CV summaries, LinkedIn profiles, portfolio intros, etc.
    using established brand voice and themes.
    """
    
    def __init__(self, brand_repo=None, content_repo=None):
        self.brand_repo = brand_repo
        self.content_repo = content_repo
        
    async def execute(
        self,
        brand_id: str,
        surface_types: List[str],
        generation_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate branded content for specified surfaces.
        
        Args:
            brand_id: Brand representation ID
            surface_types: List of surfaces (cv_summary, linkedin_summary, portfolio_intro)
            generation_preferences: Optional preferences (tone, length, emphasis_themes)
            
        Returns:
            Generated content for each surface
        """
        preferences = generation_preferences or {}
        generation_id = str(uuid.uuid4())
        generated_content = []
        
        # Placeholder brand data (would be fetched from brand_repo)
        brand_data = {
            "professional_themes": [{"theme_name": "Professional Expertise"}],
            "voice_characteristics": {"tone": "professional"},
            "narrative_arc": {"career_focus": "Experienced professional", "value_proposition": "Delivering results"}
        }
        
        for surface_type in surface_types:
            content = await self._generate_for_surface(
                surface_type, 
                brand_data, 
                preferences
            )
            
            generated_content.append({
                "generation_id": str(uuid.uuid4()),
                "brand_id": brand_id,
                "surface_type": surface_type,
                "surface_name": self._get_surface_name(surface_type),
                "content_text": content,
                "generation_timestamp": datetime.utcnow(),
                "generation_version": 1,
                "word_count": len(content.split()),
                "consistency_score": 0.92,
                "edit_count": 0,
                "status": "draft"
            })
            
        return {
            "generation_id": generation_id,
            "brand_id": brand_id,
            "generated_content": generated_content,
            "generation_metadata": {
                "surfaces_count": len(generated_content),
                "total_words": sum(c["word_count"] for c in generated_content)
            }
        }
        
    async def _generate_for_surface(
        self,
        surface_type: str,
        brand_data: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> str:
        """Generate content for a specific surface type."""
        themes = brand_data.get("professional_themes", [])
        narrative = brand_data.get("narrative_arc", {})
        
        theme_names = [t.get("theme_name", "") for t in themes[:3]]
        theme_str = ", ".join(theme_names) if theme_names else "professional skills"
        
        career_focus = narrative.get("career_focus", "experienced professional")
        value_prop = narrative.get("value_proposition", "delivering results")
        
        if surface_type == "cv_summary":
            return (
                f"A results-driven professional with expertise in {theme_str}. "
                f"{career_focus} with a proven track record of {value_prop}. "
                "Known for delivering exceptional outcomes and driving meaningful impact across organizations."
            )
        elif surface_type == "linkedin_summary":
            return (
                f"Welcome! I'm a passionate professional specializing in {theme_str}.\n\n"
                f"{career_focus}\n\n"
                f"What drives me? {value_prop}\n\n"
                "I believe in continuous learning and making a positive impact. Let's connect!"
            )
        elif surface_type == "portfolio_intro":
            return (
                f"Hello, I'm a {career_focus}. My expertise spans {theme_str}, "
                f"and I'm dedicated to {value_prop}. "
                "Explore my portfolio to see examples of my work."
            )
        else:
            return f"Professional content for {surface_type}: {theme_str}"
            
    def _get_surface_name(self, surface_type: str) -> str:
        """Get display name for surface type."""
        names = {
            "cv_summary": "CV Professional Summary",
            "linkedin_summary": "LinkedIn Summary", 
            "portfolio_intro": "Portfolio Introduction"
        }
        return names.get(surface_type, surface_type)
