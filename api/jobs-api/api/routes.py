"""
API Routes - FastAPI route handlers

All HTTP endpoint definitions separated from application setup.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import date

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
    ExportTrainingDataResponse
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
