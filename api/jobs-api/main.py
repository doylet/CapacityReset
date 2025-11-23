"""
FastAPI Jobs API - REST Adapter (Hexagon Adapter)

Exposes domain use cases as HTTP endpoints.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

# Domain and Application layers
from domain.entities import Skill, SkillType
from application.use_cases import (
    ListJobsUseCase,
    GetJobDetailUseCase,
    UpdateSkillUseCase,
    AddSkillToJobUseCase,
    GenerateJobsReportUseCase,
    ReinforceLexiconUseCase
)

# Adapters
from adapters.bigquery_repository import (
    BigQueryJobRepository,
    BigQuerySkillRepository,
    BigQueryClusterRepository,
    InMemorySkillLexiconRepository
)


app = FastAPI(title="Jobs API", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to Next.js URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency Injection: Wire up repositories
job_repo = BigQueryJobRepository()
skill_repo = BigQuerySkillRepository()
cluster_repo = BigQueryClusterRepository()
lexicon_repo = InMemorySkillLexiconRepository()

# Instantiate use cases
list_jobs_uc = ListJobsUseCase(job_repo, cluster_repo)
get_job_detail_uc = GetJobDetailUseCase(job_repo, skill_repo, cluster_repo)
update_skill_uc = UpdateSkillUseCase(skill_repo)
add_skill_uc = AddSkillToJobUseCase(skill_repo, lexicon_repo)
generate_report_uc = GenerateJobsReportUseCase(job_repo)
reinforce_lexicon_uc = ReinforceLexiconUseCase(lexicon_repo)


# === Pydantic Models (DTOs) ===

class SkillResponse(BaseModel):
    skill_id: str
    skill_name: str
    skill_category: str
    confidence_score: float
    context_snippet: str
    extraction_method: str
    skill_type: Optional[SkillType] = None


class ClusterResponse(BaseModel):
    cluster_id: int
    cluster_name: str
    cluster_keywords: List[Dict[str, float]]
    cluster_size: int


class JobResponse(BaseModel):
    job_posting_id: str
    job_title: str
    company_name: str
    job_location: str
    job_summary: str
    job_posted_date: date
    skills_count: Optional[int] = None
    cluster: Optional[ClusterResponse] = None


class JobDetailResponse(JobResponse):
    job_description_formatted: str
    skills: List[SkillResponse]


class AddSkillRequest(BaseModel):
    skill_name: str
    skill_category: str
    context_snippet: str
    skill_type: SkillType = SkillType.GENERAL


class UpdateSkillRequest(BaseModel):
    skill_type: SkillType


class GenerateReportRequest(BaseModel):
    job_ids: List[str]


# === Routes ===

@app.get("/")
async def root():
    return {"message": "Jobs API v1.0.0", "status": "healthy"}


@app.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    limit: int = Query(100, le=200),
    offset: int = Query(0, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    location: Optional[str] = None,
    cluster_id: Optional[int] = None,
    skill_name: Optional[str] = None
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
            job_location=job.job_location,
            job_summary=job.job_summary,
            job_posted_date=job.job_posted_date.date() if hasattr(job.job_posted_date, 'date') else job.job_posted_date,
            skills_count=job.skills_count,
            cluster=cluster_resp
        ))
    
    return response


@app.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(job_id: str):
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
            skill_type=s.skill_type
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
        job_location=job.job_location,
        job_summary=job.job_summary,
        job_posted_date=job.job_posted_date.date() if hasattr(job.job_posted_date, 'date') else job.job_posted_date,
        job_description_formatted=job.job_description_formatted,
        skills=skills_resp,
        cluster=cluster_resp
    )


@app.put("/jobs/{job_id}/skills/{skill_id}")
async def update_skill(job_id: str, skill_id: str, request: UpdateSkillRequest):
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


@app.post("/jobs/{job_id}/skills")
async def add_skill_to_job(job_id: str, request: AddSkillRequest):
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


@app.post("/jobs/report")
async def generate_report(request: GenerateReportRequest):
    """Generate ML report for multiple jobs."""
    report = await generate_report_uc.execute(request.job_ids)
    return report


@app.get("/lexicon")
async def get_lexicon():
    """Get skills lexicon."""
    lexicon = await reinforce_lexicon_uc.get_lexicon()
    return {"lexicon": lexicon, "total": len(lexicon)}


@app.post("/lexicon")
async def add_to_lexicon(skill_name: str, skill_category: str, skill_type: SkillType = SkillType.GENERAL):
    """Add skill to lexicon."""
    entry = await reinforce_lexicon_uc.add_skill(skill_name, skill_category, skill_type)
    return {"message": "Skill added to lexicon", "skill": entry.skill_name}


@app.get("/clusters")
async def list_clusters():
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
