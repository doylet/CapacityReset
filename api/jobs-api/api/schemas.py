"""
API Schemas - Pydantic models for request/response validation

Separate DTOs from domain entities for clean API contracts.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
from domain.entities import SkillType


class SkillResponse(BaseModel):
    skill_id: str
    skill_name: str
    skill_category: str
    confidence_score: float
    context_snippet: str
    extraction_method: str
    skill_type: Optional[SkillType] = None
    is_approved: Optional[bool] = None


class ClusterResponse(BaseModel):
    cluster_id: int
    cluster_name: str
    cluster_keywords: List[Dict[str, Any]]  # List of {"score": float, "term": str}
    cluster_size: int


class JobResponse(BaseModel):
    job_posting_id: str
    job_title: str
    company_name: str
    company_url: Optional[str] = None
    company_logo: Optional[str] = None
    job_location: str
    job_summary: str
    job_posted_date: date
    job_url: Optional[str] = None
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
