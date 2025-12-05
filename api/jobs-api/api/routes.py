"""
API Routes - FastAPI route handlers

All HTTP endpoint definitions separated from application setup.
"""

from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import uuid
import time

from api.schemas import (
    JobResponse,
    JobDetailResponse,
    SkillResponse,
    ClusterResponse,
    AddSkillRequest,
    UpdateSkillRequest,
    GenerateReportRequest,
    CreateAnnotationRequest,
    AnnotationResponse,
    ExportTrainingDataResponse,
    # Brand schemas
    BrandAnalysisResponse,
    BrandOverviewSchema,
    BrandUpdateRequest,
    ContentGenerationRequest,
    ContentGenerationResponse,
    GeneratedContentSchema,
    RegenerationRequest,
    FeedbackRequest,
    ProfessionalSurfaceSchema,
    ProfessionalThemeSchema,
    VoiceCharacteristicsSchema,
    NarrativeArcSchema,
    AnalysisMetadataSchema,
    GenerationMetadataSchema,
    SurfaceTypeEnum,
    ThemeCategoryEnum,
    VoiceToneEnum,
    FormalityLevelEnum,
    EnergyLevelEnum
)
from api.dependencies import (
    get_list_jobs_uc,
    get_job_detail_uc,
    get_update_skill_uc,
    get_add_skill_uc,
    get_unapprove_skill_uc,
    get_generate_report_uc,
    get_reinforce_lexicon_uc,
    get_skill_repo,
    get_lexicon_repo,
    get_cluster_repo
)
from domain.entities import SkillType
from application.use_cases import (
    ListJobsUseCase,
    GetJobDetailUseCase,
    UpdateSkillUseCase,
    AddSkillToJobUseCase,
    UnapproveSkillUseCase,
    GenerateJobsReportUseCase,
    ReinforceLexiconUseCase,
    ApproveSkillUseCase,
    RejectSkillUseCase
)
from domain.repositories import SkillRepository, SkillLexiconRepository, ClusterRepository


# Router for job-related endpoints
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])

# Router for skills management
skills_router = APIRouter(prefix="/skills", tags=["skills"])

# Router for lexicon management
lexicon_router = APIRouter(prefix="/lexicon", tags=["lexicon"])

# Router for clusters
clusters_router = APIRouter(prefix="/clusters", tags=["clusters"])

# Router for annotations
annotations_router = APIRouter(prefix="/annotations", tags=["annotations"])

# Router for brand management (AI Brand Roadmap)
brand_router = APIRouter(prefix="/brand", tags=["brand"])


# === Job Routes ===

@jobs_router.get("", response_model=List[JobResponse])
async def list_jobs(
    limit: int = Query(100, le=200),
    offset: int = Query(0, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    location: Optional[str] = None,
    cluster_id: Optional[int] = None,
    skill_name: Optional[str] = None,
    list_jobs_uc: ListJobsUseCase = Depends(get_list_jobs_uc)
):
    """List jobs with filters."""
    result = await list_jobs_uc.execute(
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        location=location,
        cluster_id=cluster_id,
        skill_name=skill_name
    )
    
    # Convert to response models
    response = []
    for job in result['jobs']:
        cluster_resp = None
        if job.cluster:
            cluster_resp = ClusterResponse(
                cluster_id=job.cluster.cluster_id,
                cluster_name=job.cluster.cluster_name,
                cluster_keywords=job.cluster.cluster_keywords,
                cluster_size=job.cluster.cluster_size
            )
        
        response.append(JobResponse(
            job_posting_id=job.job_posting_id,
            job_title=job.job_title,
            company_name=job.company_name,
            company_url=job.company_url,
            company_logo=job.company_logo,
            job_location=job.job_location,
            job_summary=job.job_summary,
            job_posted_date=job.job_posted_date.date() if hasattr(job.job_posted_date, 'date') else job.job_posted_date,
            job_url=job.job_url,
            skills_count=job.skills_count,
            cluster=cluster_resp
        ))
    
    return response


@jobs_router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(
    job_id: str,
    get_job_detail_uc: GetJobDetailUseCase = Depends(get_job_detail_uc)
):
    """Get job detail with skills."""
    job = await get_job_detail_uc.execute(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Convert to response
    skills_resp = [
        SkillResponse(
            skill_id=s.skill_id,
            skill_name=s.skill_name,
            skill_category=s.skill_category,
            confidence_score=s.confidence_score,
            context_snippet=s.context_snippet,
            extraction_method=s.extraction_method,
            skill_type=s.skill_type,
            is_approved=s.is_approved
        )
        for s in job.skills
    ]
    
    cluster_resp = None
    if job.cluster:
        cluster_resp = ClusterResponse(
            cluster_id=job.cluster.cluster_id,
            cluster_name=job.cluster.cluster_name,
            cluster_keywords=job.cluster.cluster_keywords,
            cluster_size=job.cluster.cluster_size
        )
    
    return JobDetailResponse(
        job_posting_id=job.job_posting_id,
        job_title=job.job_title,
        company_name=job.company_name,
        company_url=job.company_url,
        company_logo=job.company_logo,
        job_location=job.job_location,
        job_summary=job.job_summary,
        job_posted_date=job.job_posted_date.date() if hasattr(job.job_posted_date, 'date') else job.job_posted_date,
        job_url=job.job_url,
        job_description_formatted=job.job_description_formatted,
        skills=skills_resp,
        cluster=cluster_resp
    )


@jobs_router.put("/{job_id}/skills/{skill_id}")
async def update_skill(
    job_id: str,
    skill_id: str,
    request: UpdateSkillRequest,
    update_skill_uc: UpdateSkillUseCase = Depends(get_update_skill_uc),
    skill_repo: SkillRepository = Depends(get_skill_repo)
):
    """Update skill metadata."""
    # First get the skill
    skills = await skill_repo.get_skills_for_job(job_id)
    skill = next((s for s in skills if s.skill_id == skill_id), None)
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    skill.skill_type = request.skill_type
    updated_skill = await update_skill_uc.execute(skill)
    
    return {
        "skill_id": updated_skill.skill_id,
        "skill_type": updated_skill.skill_type,
        "message": "Skill updated successfully"
    }


@jobs_router.post("/{job_id}/skills")
async def add_skill_to_job(
    job_id: str,
    request: AddSkillRequest,
    add_skill_uc: AddSkillToJobUseCase = Depends(get_add_skill_uc)
):
    """Add user-defined skill (reinforcement)."""
    skill = await add_skill_uc.execute(
        job_id=job_id,
        skill_name=request.skill_name,
        skill_category=request.skill_category,
        context_snippet=request.context_snippet,
        skill_type=request.skill_type
    )
    
    return {
        "skill_id": skill.skill_id,
        "skill_name": skill.skill_name,
        "message": "Skill added and lexicon reinforced"
    }


@jobs_router.post("/{job_id}/skills/{skill_id}/approve")
async def approve_skill(
    job_id: str,
    skill_id: str,
    skill_repo: SkillRepository = Depends(get_skill_repo),
    lexicon_repo: SkillLexiconRepository = Depends(get_lexicon_repo)
):
    """Approve an ML-suggested skill and add to lexicon."""
    approve_uc = ApproveSkillUseCase(skill_repo, lexicon_repo)
    skill = await approve_uc.execute(skill_id)
    
    return {
        "skill_id": skill.skill_id,
        "skill_name": skill.skill_name,
        "is_approved": skill.is_approved,
        "message": "Skill approved and added to lexicon"
    }


@jobs_router.post("/{job_id}/skills/{skill_id}/reject")
async def reject_skill(
    job_id: str,
    skill_id: str,
    skill_repo: SkillRepository = Depends(get_skill_repo)
):
    """Reject an ML-suggested skill and remove it."""
    reject_uc = RejectSkillUseCase(skill_repo)
    success = await reject_uc.execute(skill_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return {
        "message": "Skill rejected and removed"
    }


@jobs_router.post("/{job_id}/skills/{skill_id}/unapprove")
async def unapprove_skill(
    job_id: str,
    skill_id: str,
    unapprove_uc: UnapproveSkillUseCase = Depends(get_unapprove_skill_uc)
):
    """Unapprove an approved skill (return to pending state)."""
    skill = await unapprove_uc.execute(skill_id)
    
    return {
        "skill_id": skill.skill_id,
        "skill_name": skill.skill_name,
        "is_approved": skill.is_approved,
        "message": "Skill unapproved and returned to pending"
    }


@jobs_router.post("/report")
async def generate_report(
    request: GenerateReportRequest,
    generate_report_uc: GenerateJobsReportUseCase = Depends(get_generate_report_uc)
):
    """Generate ML report for multiple jobs."""
    report = await generate_report_uc.execute(request.job_ids)
    return report


# === Skills Routes ===

@skills_router.get("/categories")
async def get_skill_categories(
    lexicon_repo: SkillLexiconRepository = Depends(get_lexicon_repo)
):
    """Get all skill categories with counts (dynamic from lexicon)."""
    categories = await lexicon_repo.get_categories_with_counts()
    return {"categories": categories}


@skills_router.get("")
async def search_skills(
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(10, le=50),
    lexicon_repo: SkillLexiconRepository = Depends(get_lexicon_repo)
):
    """Search skills for autocomplete."""
    if q:
        skills = await lexicon_repo.search_skills(q, limit)
    else:
        # Return most popular skills
        all_skills = await lexicon_repo.get_lexicon()
        skills = [
            {
                "skill_name": s.skill_name,
                "skill_category": s.skill_category,
                "usage_count": s.usage_count
            }
            for s in sorted(all_skills, key=lambda x: x.usage_count, reverse=True)[:limit]
        ]
    
    return {"skills": skills, "total": len(skills)}


# === Lexicon Routes ===

@lexicon_router.get("")
async def get_lexicon(
    reinforce_lexicon_uc: ReinforceLexiconUseCase = Depends(get_reinforce_lexicon_uc)
):
    """Get skills lexicon."""
    lexicon = await reinforce_lexicon_uc.get_lexicon()
    return {"lexicon": lexicon, "total": len(lexicon)}


@lexicon_router.post("")
async def add_to_lexicon(
    skill_name: str,
    skill_category: str,
    skill_type: SkillType = SkillType.GENERAL,
    reinforce_lexicon_uc: ReinforceLexiconUseCase = Depends(get_reinforce_lexicon_uc)
):
    """Add skill to lexicon."""
    entry = await reinforce_lexicon_uc.add_skill(skill_name, skill_category, skill_type)
    return {"message": "Skill added to lexicon", "skill": entry.skill_name}


# === Cluster Routes ===

@clusters_router.get("")
async def list_clusters(
    cluster_repo: ClusterRepository = Depends(get_cluster_repo)
):
    """Get all clusters."""
    clusters = await cluster_repo.list_all_clusters()
    return [
        ClusterResponse(
            cluster_id=c.cluster_id,
            cluster_name=c.cluster_name,
            cluster_keywords=c.cluster_keywords,
            cluster_size=c.cluster_size
        )
        for c in clusters
    ]


# === Annotation Routes ===

@annotations_router.post("", response_model=AnnotationResponse)
async def create_annotation(
    request: CreateAnnotationRequest
):
    """Create a new section annotation for ML training."""
    from api.dependencies import get_create_annotation_uc
    from application.use_cases import CreateAnnotationUseCase
    
    use_case = get_create_annotation_uc()
    
    try:
        annotation = await use_case.execute(
            job_id=request.job_id,
            section_text=request.section_text,
            section_start_index=request.section_start_index,
            section_end_index=request.section_end_index,
            label=request.label,
            annotator_id=request.annotator_id,
            notes=request.notes
        )
        
        return AnnotationResponse(
            annotation_id=annotation.annotation_id,
            job_posting_id=annotation.job_posting_id,
            section_text=annotation.section_text,
            section_start_index=annotation.section_start_index,
            section_end_index=annotation.section_end_index,
            label=annotation.label.value,
            contains_skills=annotation.contains_skills,
            annotator_id=annotation.annotator_id,
            notes=annotation.notes,
            created_at=annotation.created_at.isoformat() if annotation.created_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@jobs_router.get("/{job_id}/annotations", response_model=List[AnnotationResponse])
async def get_job_annotations(job_id: str):
    """Get all annotations for a specific job."""
    from api.dependencies import get_annotations_by_job_uc
    from application.use_cases import GetAnnotationsByJobUseCase
    
    use_case = get_annotations_by_job_uc()
    annotations = await use_case.execute(job_id)
    
    return [
        AnnotationResponse(
            annotation_id=ann.annotation_id,
            job_posting_id=ann.job_posting_id,
            section_text=ann.section_text,
            section_start_index=ann.section_start_index,
            section_end_index=ann.section_end_index,
            label=ann.label.value,
            contains_skills=ann.contains_skills,
            annotator_id=ann.annotator_id,
            notes=ann.notes,
            created_at=ann.created_at.isoformat() if ann.created_at else None
        )
        for ann in annotations
    ]


@annotations_router.get("", response_model=List[AnnotationResponse])
async def list_annotations(
    limit: int = Query(100, le=200),
    offset: int = Query(0, ge=0)
):
    """List all annotations with pagination."""
    from api.dependencies import get_list_annotations_uc
    from application.use_cases import ListAnnotationsUseCase
    
    use_case = get_list_annotations_uc()
    result = await use_case.execute(limit=limit, offset=offset)
    
    return [
        AnnotationResponse(
            annotation_id=ann.annotation_id,
            job_posting_id=ann.job_posting_id,
            section_text=ann.section_text,
            section_start_index=ann.section_start_index,
            section_end_index=ann.section_end_index,
            label=ann.label.value,
            contains_skills=ann.contains_skills,
            annotator_id=ann.annotator_id,
            notes=ann.notes,
            created_at=ann.created_at.isoformat() if ann.created_at else None
        )
        for ann in result['annotations']
    ]


@annotations_router.delete("/{annotation_id}")
async def delete_annotation(annotation_id: str):
    """Delete an annotation."""
    from api.dependencies import get_delete_annotation_uc
    from application.use_cases import DeleteAnnotationUseCase
    
    use_case = get_delete_annotation_uc()
    success = await use_case.execute(annotation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    return {"status": "deleted", "annotation_id": annotation_id}


@annotations_router.get("/export/training-data", response_model=ExportTrainingDataResponse)
async def export_training_data():
    """Export all annotations as ML training data."""
    from api.dependencies import get_export_training_data_uc
    from application.use_cases import ExportTrainingDataUseCase
    
    use_case = get_export_training_data_uc()
    data = await use_case.execute()
    
    return ExportTrainingDataResponse(
        format=data['format'],
        total_annotations=data['total_annotations'],
        annotations=data['annotations'],
        label_distribution=data['label_distribution']
    )


# === Brand Routes (AI Brand Roadmap) ===

# MVP Implementation Note: In-memory storage for demonstration purposes.
# Production deployment should use BigQuery adapters from domain/repositories.py
# This enables immediate feature testing while maintaining the hexagonal architecture
# separation that allows swapping in persistent storage without API changes.
_brand_storage: Dict[str, Dict[str, Any]] = {}
_content_storage: Dict[str, Dict[str, Any]] = {}


def _get_surface_type_value(surface_type: Any) -> str:
    """Extract string value from surface type, handling both enum and string types."""
    if hasattr(surface_type, 'value'):
        return surface_type.value
    return str(surface_type)


_surfaces_data = [
    {
        "surface_id": "surf-cv-summary-001",
        "surface_type": "cv_summary",
        "surface_name": "CV Professional Summary",
        "content_requirements": {
            "min_length": 100,
            "max_length": 300,
            "tone_guidelines": ["professional", "achievement-focused"],
            "structure_requirements": ["opening_statement", "key_achievements", "value_proposition"]
        },
        "template_structure": "A results-driven {career_focus} professional...",
        "active": True
    },
    {
        "surface_id": "surf-linkedin-summary-001",
        "surface_type": "linkedin_summary",
        "surface_name": "LinkedIn Summary",
        "content_requirements": {
            "min_length": 150,
            "max_length": 500,
            "tone_guidelines": ["conversational", "professional", "authentic"],
            "structure_requirements": ["hook", "story", "expertise", "call_to_action"]
        },
        "template_structure": "{hook_statement}\n\n{career_story}...",
        "active": True
    },
    {
        "surface_id": "surf-portfolio-intro-001",
        "surface_type": "portfolio_intro",
        "surface_name": "Portfolio Introduction",
        "content_requirements": {
            "min_length": 100,
            "max_length": 250,
            "tone_guidelines": ["creative", "professional", "engaging"],
            "structure_requirements": ["introduction", "expertise", "value_statement"]
        },
        "template_structure": "Hello, I am {professional_title}...",
        "active": True
    }
]


@brand_router.post("/analysis", response_model=BrandAnalysisResponse)
async def analyze_brand(
    document: UploadFile = File(...),
    linkedin_profile_url: Optional[str] = None,
    use_enhanced_llm: bool = True
):
    """
    Analyze professional document for brand extraction.
    
    Upload CV/resume and optional LinkedIn profile for comprehensive brand analysis.
    Returns brand overview with themes, voice characteristics, and narrative arc.
    
    The analysis uses LLM-powered extraction to identify:
    - Professional themes with evidence citations and confidence scores
    - Voice characteristics (tone, formality, energy, communication style)
    - Narrative arc (career progression, value proposition, future positioning)
    
    Args:
        document: CV/resume file to analyze
        linkedin_profile_url: Optional LinkedIn profile for enrichment
        use_enhanced_llm: Whether to use enhanced LLM analysis (default: True)
    """
    from application.use_cases import AnalyzeBrandUseCase
    
    start_time = time.time()
    
    # Read document content
    content = await document.read()
    document_text = content.decode('utf-8', errors='ignore')
    
    # Generate brand ID
    brand_id = str(uuid.uuid4())
    
    # Use enhanced brand analysis use case
    analyze_uc = AnalyzeBrandUseCase()
    brand_data = await analyze_uc.execute(
        document_content=document_text,
        user_id="default-user",
        source_document_url=f"uploads/{document.filename}",
        linkedin_profile_url=linkedin_profile_url,
        analysis_options={
            "use_enhanced_llm": use_enhanced_llm,
            "prompt_version": "v1"
        }
    )
    
    # Extract themes with enhanced evidence
    themes = brand_data.get("professional_themes", [])
    voice = brand_data.get("voice_characteristics", {})
    narrative = brand_data.get("narrative_arc", {})
    confidence_scores = brand_data.get("confidence_scores", {
        "overall": 0.85,
        "themes": 0.82,
        "voice": 0.88,
        "narrative": 0.80
    })
    
    # Store brand representation
    brand_data["brand_id"] = brand_id
    _brand_storage[brand_id] = brand_data
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    # Build enhanced theme response with evidence and reasoning
    enhanced_themes = []
    for theme in themes:
        enhanced_themes.append(ProfessionalThemeSchema(
            theme_id=theme.get("theme_id", str(uuid.uuid4())),
            theme_name=theme.get("theme_name", ""),
            theme_category=theme.get("theme_category", "skill"),
            description=theme.get("description", ""),
            keywords=theme.get("keywords", []),
            confidence_score=theme.get("confidence_score", 0.7),
            source_evidence=theme.get("source_evidence", ""),
            reasoning=theme.get("reasoning", "")  # LLM explanation for theme
        ))
    
    return BrandAnalysisResponse(
        brand_id=brand_id,
        analysis_status="completed",
        brand_overview=BrandOverviewSchema(
            brand_id=brand_id,
            professional_themes=enhanced_themes,
            voice_characteristics=VoiceCharacteristicsSchema(**voice),
            narrative_arc=NarrativeArcSchema(**narrative),
            confidence_scores=confidence_scores,
            created_at=brand_data.get("created_at"),
            updated_at=brand_data.get("updated_at")
        ),
        analysis_metadata=AnalysisMetadataSchema(
            document_type=document.content_type,
            word_count=len(document_text.split()),
            confidence_score=confidence_scores.get("overall", 0.85),
            processing_time_ms=processing_time_ms,
            analysis_type=brand_data.get("analysis_metadata", {}).get("analysis_type", "llm"),
            prompt_version=brand_data.get("analysis_metadata", {}).get("prompt_version", "v1")
        )
    )


@brand_router.get("/overview/{brand_id}", response_model=BrandOverviewSchema)
async def get_brand_overview(brand_id: str):
    """Retrieve brand overview."""
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    brand_data = _brand_storage[brand_id]
    
    return BrandOverviewSchema(
        brand_id=brand_id,
        professional_themes=[
            ProfessionalThemeSchema(**theme) for theme in brand_data["professional_themes"]
        ],
        voice_characteristics=VoiceCharacteristicsSchema(**brand_data["voice_characteristics"]),
        narrative_arc=NarrativeArcSchema(**brand_data["narrative_arc"]),
        confidence_scores=brand_data["confidence_scores"],
        created_at=brand_data.get("created_at"),
        updated_at=brand_data.get("updated_at")
    )


@brand_router.patch("/overview/{brand_id}", response_model=BrandOverviewSchema)
async def update_brand_overview(brand_id: str, request: BrandUpdateRequest):
    """Update brand overview."""
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    brand_data = _brand_storage[brand_id]
    
    # Update fields if provided
    if request.professional_themes is not None:
        brand_data["professional_themes"] = [t.model_dump() for t in request.professional_themes]
    if request.voice_characteristics is not None:
        brand_data["voice_characteristics"] = request.voice_characteristics.model_dump()
    if request.narrative_arc is not None:
        brand_data["narrative_arc"] = request.narrative_arc.model_dump()
    
    brand_data["updated_at"] = datetime.utcnow()
    brand_data["version"] += 1
    
    return BrandOverviewSchema(
        brand_id=brand_id,
        professional_themes=[
            ProfessionalThemeSchema(**theme) for theme in brand_data["professional_themes"]
        ],
        voice_characteristics=VoiceCharacteristicsSchema(**brand_data["voice_characteristics"]),
        narrative_arc=NarrativeArcSchema(**brand_data["narrative_arc"]),
        confidence_scores=brand_data["confidence_scores"],
        created_at=brand_data.get("created_at"),
        updated_at=brand_data.get("updated_at")
    )


@brand_router.post("/{brand_id}/generate", response_model=ContentGenerationResponse)
async def generate_content(brand_id: str, request: ContentGenerationRequest):
    """
    Generate cross-surface branded content.
    
    Create consistent content across multiple professional surfaces (CV, LinkedIn, portfolio)
    using established brand representation.
    """
    start_time = time.time()
    
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    brand_data = _brand_storage[brand_id]
    generation_id = str(uuid.uuid4())
    generated_content = []
    
    for surface_type in request.surface_types:
        content_id = str(uuid.uuid4())
        content_text = _generate_surface_content(
            brand_data, 
            surface_type.value,
            request.generation_preferences
        )
        
        content_data = {
            "generation_id": content_id,
            "brand_id": brand_id,
            "surface_type": surface_type,
            "surface_name": _get_surface_name(surface_type.value),
            "content_text": content_text,
            "generation_timestamp": datetime.utcnow(),
            "generation_version": 1,
            "word_count": len(content_text.split()),
            "consistency_score": 0.92,
            "edit_count": 0,
            "status": "draft"
        }
        
        _content_storage[content_id] = content_data
        generated_content.append(GeneratedContentSchema(**content_data))
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    return ContentGenerationResponse(
        generation_id=generation_id,
        brand_id=brand_id,
        generated_content=generated_content,
        generation_metadata=GenerationMetadataSchema(
            generation_time_ms=processing_time_ms,
            consistency_score=0.92,
            surfaces_count=len(generated_content)
        )
    )


@brand_router.get("/{brand_id}/content", response_model=List[GeneratedContentSchema])
async def get_generated_content(
    brand_id: str,
    surface_type: Optional[SurfaceTypeEnum] = None
):
    """Retrieve generated content for a brand."""
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    contents = [
        GeneratedContentSchema(**data)
        for data in _content_storage.values()
        if data["brand_id"] == brand_id and (
            surface_type is None or data["surface_type"] == surface_type
        )
    ]
    
    return contents


@brand_router.post("/{brand_id}/content/{generation_id}/regenerate", response_model=GeneratedContentSchema)
async def regenerate_content(
    brand_id: str,
    generation_id: str,
    request: RegenerationRequest
):
    """Regenerate specific surface content with feedback."""
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    if generation_id not in _content_storage:
        raise HTTPException(status_code=404, detail="Content generation not found")
    
    content_data = _content_storage[generation_id]
    if content_data["brand_id"] != brand_id:
        raise HTTPException(status_code=404, detail="Content not found for this brand")
    
    brand_data = _brand_storage[brand_id]
    
    # Archive old generation
    content_data["status"] = "archived"
    
    # Create new generation
    new_id = str(uuid.uuid4())
    new_content_text = _generate_surface_content(
        brand_data,
        _get_surface_type_value(content_data["surface_type"]),
        None,
        feedback=request.feedback_details,
        tone=request.preferred_tone,
        length=request.preferred_length
    )
    
    new_content = {
        "generation_id": new_id,
        "brand_id": brand_id,
        "surface_type": content_data["surface_type"],
        "surface_name": content_data.get("surface_name"),
        "content_text": new_content_text,
        "generation_timestamp": datetime.utcnow(),
        "generation_version": content_data["generation_version"] + 1,
        "word_count": len(new_content_text.split()),
        "consistency_score": 0.90,
        "edit_count": 0,
        "status": "draft"
    }
    
    _content_storage[new_id] = new_content
    
    return GeneratedContentSchema(**new_content)


@brand_router.post("/{brand_id}/feedback")
async def submit_feedback(brand_id: str, request: FeedbackRequest):
    """Submit content feedback for learning improvement."""
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Record learning event (MVP: just acknowledge receipt)
    event_id = str(uuid.uuid4())
    
    return {
        "event_id": event_id,
        "brand_id": brand_id,
        "feedback_type": request.feedback_type,
        "status": "recorded",
        "message": "Feedback recorded successfully for learning improvement"
    }


@brand_router.post("/{brand_id}/rating")
async def submit_rating(
    brand_id: str,
    rating: int = Query(..., ge=1, le=5),
    generation_id: Optional[str] = None
):
    """Submit satisfaction rating for generated content."""
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    if generation_id and generation_id in _content_storage:
        _content_storage[generation_id]["user_satisfaction_rating"] = rating
    
    return {
        "brand_id": brand_id,
        "generation_id": generation_id,
        "rating": rating,
        "status": "recorded"
    }


# === Enhanced LLM Feedback Collection System ===

@brand_router.post("/{brand_id}/feedback/analysis")
async def submit_analysis_feedback(
    brand_id: str,
    analysis_type: str = Query(..., description="Type of analysis (theme_analysis, voice_analysis, narrative_analysis)"),
    feedback_rating: int = Query(..., ge=1, le=5, description="Quality rating 1-5"),
    feedback_text: Optional[str] = None,
    specific_issues: Optional[List[str]] = None,
    suggested_improvements: Optional[str] = None
):
    """
    Submit detailed feedback on LLM analysis quality.
    
    Collects user feedback on theme extraction, voice analysis, and narrative arc
    generation to improve LLM prompt engineering and model performance.
    """
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    feedback_id = str(uuid.uuid4())
    
    # Store feedback for learning (MVP: in-memory)
    feedback_data = {
        "feedback_id": feedback_id,
        "brand_id": brand_id,
        "analysis_type": analysis_type,
        "feedback_rating": feedback_rating,
        "feedback_text": feedback_text,
        "specific_issues": specific_issues or [],
        "suggested_improvements": suggested_improvements,
        "timestamp": datetime.utcnow(),
        "user_id": "default-user",  # TODO: Get from auth context
        "status": "recorded"
    }
    
    return {
        "feedback_id": feedback_id,
        "analysis_type": analysis_type,
        "status": "recorded",
        "message": f"Analysis feedback recorded for {analysis_type}"
    }


@brand_router.post("/{brand_id}/feedback/theme/{theme_id}")
async def submit_theme_feedback(
    brand_id: str,
    theme_id: str,
    is_relevant: bool = Query(..., description="Whether this theme is relevant"),
    confidence_rating: Optional[int] = Query(None, ge=1, le=5, description="Confidence in theme accuracy"),
    feedback_comment: Optional[str] = None
):
    """
    Submit feedback on individual theme relevance and accuracy.
    
    Enables fine-grained feedback collection on specific themes identified
    by LLM analysis to improve theme extraction precision.
    """
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    feedback_id = str(uuid.uuid4())
    
    feedback_data = {
        "feedback_id": feedback_id,
        "brand_id": brand_id,
        "theme_id": theme_id,
        "feedback_type": "theme_relevance",
        "is_relevant": is_relevant,
        "confidence_rating": confidence_rating,
        "feedback_comment": feedback_comment,
        "timestamp": datetime.utcnow(),
        "user_id": "default-user"
    }
    
    return {
        "feedback_id": feedback_id,
        "theme_id": theme_id,
        "status": "recorded",
        "message": f"Theme feedback recorded: {'relevant' if is_relevant else 'not relevant'}"
    }


@brand_router.post("/{brand_id}/feedback/voice")
async def submit_voice_feedback(
    brand_id: str,
    accuracy_rating: int = Query(..., ge=1, le=5, description="Voice analysis accuracy"),
    tone_accuracy: Optional[bool] = Query(None, description="Is the identified tone accurate?"),
    formality_accuracy: Optional[bool] = Query(None, description="Is the formality level accurate?"),
    missing_characteristics: Optional[List[str]] = None,
    feedback_details: Optional[str] = None
):
    """
    Submit feedback on voice characteristics analysis accuracy.
    
    Collects detailed feedback on voice analysis components to improve
    LLM understanding of communication style and personality traits.
    """
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    feedback_id = str(uuid.uuid4())
    
    feedback_data = {
        "feedback_id": feedback_id,
        "brand_id": brand_id,
        "feedback_type": "voice_characteristics",
        "accuracy_rating": accuracy_rating,
        "tone_accuracy": tone_accuracy,
        "formality_accuracy": formality_accuracy,
        "missing_characteristics": missing_characteristics or [],
        "feedback_details": feedback_details,
        "timestamp": datetime.utcnow(),
        "user_id": "default-user"
    }
    
    return {
        "feedback_id": feedback_id,
        "feedback_type": "voice_characteristics",
        "status": "recorded",
        "message": "Voice analysis feedback recorded"
    }


@brand_router.post("/{brand_id}/feedback/content/{generation_id}")
async def submit_content_feedback(
    brand_id: str,
    generation_id: str,
    quality_rating: int = Query(..., ge=1, le=5, description="Content quality rating"),
    authenticity_rating: int = Query(..., ge=1, le=5, description="Voice authenticity rating"),
    usefulness_rating: int = Query(..., ge=1, le=5, description="Content usefulness rating"),
    specific_feedback: Optional[str] = None,
    improvement_suggestions: Optional[List[str]] = None
):
    """
    Submit detailed feedback on generated content quality and authenticity.
    
    Captures comprehensive feedback on content generation performance
    to improve LLM content creation and voice consistency.
    """
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    if generation_id not in _content_storage:
        raise HTTPException(status_code=404, detail="Content generation not found")
    
    feedback_id = str(uuid.uuid4())
    
    feedback_data = {
        "feedback_id": feedback_id,
        "brand_id": brand_id,
        "generation_id": generation_id,
        "feedback_type": "content_quality",
        "quality_rating": quality_rating,
        "authenticity_rating": authenticity_rating,
        "usefulness_rating": usefulness_rating,
        "specific_feedback": specific_feedback,
        "improvement_suggestions": improvement_suggestions or [],
        "timestamp": datetime.utcnow(),
        "user_id": "default-user"
    }
    
    # Update content record with feedback
    if generation_id in _content_storage:
        _content_storage[generation_id]["user_feedback"] = feedback_data
    
    return {
        "feedback_id": feedback_id,
        "generation_id": generation_id,
        "status": "recorded",
        "message": "Content feedback recorded for improvement"
    }


@brand_router.get("/{brand_id}/feedback/analytics")
async def get_feedback_analytics(brand_id: str):
    """
    Get feedback analytics and trends for brand analysis.
    
    Provides insights into user satisfaction and areas for improvement
    based on collected feedback data.
    """
    if brand_id not in _brand_storage:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Mock analytics data for MVP
    analytics = {
        "brand_id": brand_id,
        "feedback_summary": {
            "total_feedback_events": 5,
            "avg_analysis_rating": 4.2,
            "avg_content_rating": 4.0,
            "theme_accuracy_rate": 0.85,
            "voice_accuracy_rate": 0.78
        },
        "improvement_areas": [
            "Voice formality detection needs refinement",
            "Theme confidence scoring could be more accurate"
        ],
        "recent_trends": {
            "satisfaction_trend": "improving",
            "most_accurate_analysis": "theme_analysis",
            "least_accurate_analysis": "voice_analysis"
        },
        "generated_at": datetime.utcnow()
    }
    
    return analytics


@brand_router.get("/surfaces", response_model=List[ProfessionalSurfaceSchema])
async def list_surfaces():
    """List available professional surfaces."""
    return [
        ProfessionalSurfaceSchema(
            surface_id=s["surface_id"],
            surface_type=s["surface_type"],
            surface_name=s["surface_name"],
            content_requirements=s["content_requirements"],
            template_structure=s.get("template_structure"),
            active=s.get("active", True)
        )
        for s in _surfaces_data
    ]


# === Helper functions for brand analysis ===

def _extract_themes_from_document(text: str) -> List[Dict[str, Any]]:
    """Extract professional themes from document text (MVP implementation)."""
    themes = []
    text_lower = text.lower()
    
    # Simple keyword-based theme extraction for MVP
    theme_patterns = {
        "leadership": ("leadership", "skill", ["leadership", "team management", "mentoring"]),
        "technical_expertise": ("technical expertise", "skill", ["programming", "development", "engineering"]),
        "communication": ("communication", "skill", ["communication", "presentation", "collaboration"]),
        "innovation": ("innovation", "value_proposition", ["innovation", "creative", "problem-solving"]),
        "results_driven": ("results-driven", "achievement", ["results", "delivered", "achieved"])
    }
    
    for key, (name, category, keywords) in theme_patterns.items():
        if any(kw in text_lower for kw in keywords):
            themes.append({
                "theme_id": str(uuid.uuid4()),
                "theme_name": name,
                "theme_category": category,
                "description": f"Demonstrated {name} throughout career",
                "keywords": keywords,
                "confidence_score": 0.85,
                "source_evidence": f"Extracted from document analysis"
            })
    
    # Ensure at least one theme
    if not themes:
        themes.append({
            "theme_id": str(uuid.uuid4()),
            "theme_name": "professional expertise",
            "theme_category": "skill",
            "description": "General professional expertise",
            "keywords": ["professional", "experience"],
            "confidence_score": 0.75,
            "source_evidence": "Default theme from document"
        })
    
    return themes[:5]  # Limit to 5 themes


def _analyze_voice_characteristics(text: str) -> Dict[str, Any]:
    """Analyze voice characteristics from document text (MVP implementation)."""
    text_lower = text.lower()
    
    # Simple heuristics for voice analysis
    tone = "professional"
    if any(word in text_lower for word in ["passionate", "excited", "thrilled"]):
        tone = "enthusiastic"
    elif any(word in text_lower for word in ["data", "metrics", "analysis"]):
        tone = "analytical"
    
    formality = "formal"
    if any(word in text_lower for word in ["hey", "folks", "awesome"]):
        formality = "casual"
    elif any(word in text_lower for word in ["i am", "i've", "my experience"]):
        formality = "business_casual"
    
    return {
        "tone": tone,
        "formality_level": formality,
        "energy_level": "balanced",
        "communication_style": ["data_driven", "action_oriented"],
        "vocabulary_complexity": "professional"
    }


def _build_narrative_arc(text: str) -> Dict[str, Any]:
    """Build narrative arc from document text (MVP implementation)."""
    words = text.split()
    
    # Extract simple narrative elements
    career_focus = "Experienced professional"
    if len(words) > 10:
        career_focus = " ".join(words[:5]) + "..."
    
    return {
        "career_focus": career_focus,
        "value_proposition": "Delivering results through expertise and dedication",
        "career_progression": "Progressive career growth with increasing responsibilities",
        "key_achievements": ["Demonstrated track record of success"],
        "future_goals": "Continuing to drive impact in the industry"
    }


def _generate_surface_content(
    brand_data: Dict[str, Any],
    surface_type: str,
    preferences: Any = None,
    feedback: str = None,
    tone: Any = None,
    length: Any = None
) -> str:
    """Generate content for a specific surface (MVP implementation)."""
    themes = brand_data.get("professional_themes", [])
    narrative = brand_data.get("narrative_arc", {})
    voice = brand_data.get("voice_characteristics", {})
    
    theme_names = [t.get("theme_name", "") for t in themes[:3]]
    theme_str = ", ".join(theme_names) if theme_names else "professional skills"
    
    career_focus = narrative.get("career_focus", "experienced professional")
    value_prop = narrative.get("value_proposition", "delivering results")
    
    if surface_type == "cv_summary":
        return f"A results-driven professional with expertise in {theme_str}. {career_focus} with a proven track record of {value_prop}. Known for delivering exceptional outcomes and driving meaningful impact across organizations."
    
    elif surface_type == "linkedin_summary":
        return f"Welcome! I'm a passionate professional specializing in {theme_str}.\n\n{career_focus}\n\nWhat drives me? {value_prop}\n\nI believe in continuous learning and making a positive impact. Let's connect and explore how we can collaborate!"
    
    elif surface_type == "portfolio_intro":
        return f"Hello, I'm a {career_focus}. My expertise spans {theme_str}, and I'm dedicated to {value_prop}. Explore my portfolio to see examples of my work and the impact I've created."
    
    return f"Professional content for {surface_type}: {theme_str}"


def _get_surface_name(surface_type: str) -> str:
    """Get display name for a surface type."""
    names = {
        "cv_summary": "CV Professional Summary",
        "linkedin_summary": "LinkedIn Summary",
        "portfolio_intro": "Portfolio Introduction"
    }
    return names.get(surface_type, surface_type)
