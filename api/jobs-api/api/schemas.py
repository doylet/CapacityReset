"""
API Schemas - Pydantic models for request/response validation

Separate DTOs from domain entities for clean API contracts.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
from domain.entities import SkillType, AnnotationLabel


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


# === Section Annotation Schemas ===

class CreateAnnotationRequest(BaseModel):
    job_id: str
    section_text: str
    section_start_index: int
    section_end_index: int
    label: AnnotationLabel
    annotator_id: str
    notes: Optional[str] = None


class AnnotationResponse(BaseModel):
    annotation_id: str
    job_posting_id: str
    section_text: str
    section_start_index: int
    section_end_index: int
    label: str
    contains_skills: bool
    annotator_id: str
    notes: Optional[str]
    created_at: Optional[str]


class ExportTrainingDataResponse(BaseModel):
    format: str
    total_annotations: int
    annotations: List[Dict[str, Any]]
    label_distribution: Dict[str, int]


# === AI Brand Roadmap Schemas ===

class ThemeCategoryEnum(str, Enum):
    """Categories for professional themes."""
    SKILL = "skill"
    INDUSTRY = "industry"
    ROLE = "role"
    VALUE_PROPOSITION = "value_proposition"
    ACHIEVEMENT = "achievement"


class VoiceToneEnum(str, Enum):
    """Tone options for voice characteristics."""
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    AUTHORITATIVE = "authoritative"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"


class FormalityLevelEnum(str, Enum):
    """Formality level options."""
    CASUAL = "casual"
    BUSINESS_CASUAL = "business_casual"
    FORMAL = "formal"
    HIGHLY_FORMAL = "highly_formal"


class EnergyLevelEnum(str, Enum):
    """Energy level options."""
    RESERVED = "reserved"
    BALANCED = "balanced"
    ENTHUSIASTIC = "enthusiastic"
    DYNAMIC = "dynamic"


class CareerLevelEnum(str, Enum):
    """Career level options."""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    EXECUTIVE = "executive"


class SurfaceTypeEnum(str, Enum):
    """Surface type options."""
    CV_SUMMARY = "cv_summary"
    LINKEDIN_SUMMARY = "linkedin_summary"
    PORTFOLIO_INTRO = "portfolio_intro"


class TargetLengthEnum(str, Enum):
    """Target length options."""
    CONCISE = "concise"
    STANDARD = "standard"
    DETAILED = "detailed"


class FeedbackReasonEnum(str, Enum):
    """Feedback reason options."""
    TONE_ADJUSTMENT = "tone_adjustment"
    CONTENT_ACCURACY = "content_accuracy"
    LENGTH_CHANGE = "length_change"
    STYLE_PREFERENCE = "style_preference"


class FeedbackTypeEnum(str, Enum):
    """Feedback type options."""
    CONTENT_EDIT = "content_edit"
    SATISFACTION_RATING = "satisfaction_rating"
    PREFERENCE_CHANGE = "preference_change"
    GENERAL_FEEDBACK = "general_feedback"


class LengthPreferenceEnum(str, Enum):
    """Length preference options."""
    SHORTER = "shorter"
    CURRENT = "current"
    LONGER = "longer"


class AnalysisPreferencesSchema(BaseModel):
    """Preferences for brand analysis."""
    industry_focus: Optional[str] = None
    career_level: Optional[CareerLevelEnum] = None
    tone_preference: Optional[VoiceToneEnum] = None


class ProfessionalThemeSchema(BaseModel):
    """Professional theme response with LLM-enhanced evidence."""
    theme_id: str
    theme_name: str
    theme_category: ThemeCategoryEnum
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    source_evidence: Optional[str] = None
    reasoning: Optional[str] = None  # LLM explanation for theme identification
    evidence_quotes: List[str] = Field(default_factory=list)  # Supporting quotes from document


class VoiceCharacteristicsSchema(BaseModel):
    """Voice characteristics response."""
    tone: VoiceToneEnum
    formality_level: FormalityLevelEnum
    energy_level: EnergyLevelEnum
    communication_style: List[str] = Field(default_factory=list)
    vocabulary_complexity: str = "professional"


class NarrativeArcSchema(BaseModel):
    """Narrative arc response."""
    career_focus: str
    value_proposition: str
    career_progression: Optional[str] = None
    key_achievements: List[str] = Field(default_factory=list)
    future_goals: Optional[str] = None


class BrandOverviewSchema(BaseModel):
    """Brand overview response."""
    brand_id: str
    professional_themes: List[ProfessionalThemeSchema]
    voice_characteristics: VoiceCharacteristicsSchema
    narrative_arc: NarrativeArcSchema
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AnalysisMetadataSchema(BaseModel):
    """Analysis metadata response with LLM tracking."""
    document_type: Optional[str] = None
    word_count: Optional[int] = None
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    processing_time_ms: Optional[int] = None
    analysis_type: Optional[str] = None  # "llm" or "keyword"
    prompt_version: Optional[str] = None  # Prompt template version used
    model_version: Optional[str] = None  # LLM model version
    fallback_used: Optional[bool] = None  # Whether fallback was triggered


class BrandAnalysisResponse(BaseModel):
    """Response for brand analysis."""
    brand_id: str
    analysis_status: str
    brand_overview: BrandOverviewSchema
    analysis_metadata: Optional[AnalysisMetadataSchema] = None


class BrandUpdateRequest(BaseModel):
    """Request for updating brand overview."""
    professional_themes: Optional[List[ProfessionalThemeSchema]] = None
    voice_characteristics: Optional[VoiceCharacteristicsSchema] = None
    narrative_arc: Optional[NarrativeArcSchema] = None


class GenerationPreferencesSchema(BaseModel):
    """Preferences for content generation."""
    emphasis_themes: List[str] = Field(default_factory=list)
    target_length: TargetLengthEnum = TargetLengthEnum.STANDARD
    include_achievements: bool = True


class ContentGenerationRequest(BaseModel):
    """Request for content generation."""
    surface_types: List[SurfaceTypeEnum] = Field(min_length=1, max_length=10)
    generation_preferences: Optional[GenerationPreferencesSchema] = None


class GeneratedContentSchema(BaseModel):
    """Generated content response."""
    generation_id: str
    surface_type: SurfaceTypeEnum
    surface_name: Optional[str] = None
    content_text: str
    generation_timestamp: datetime
    generation_version: int = 1
    word_count: int = 0
    consistency_score: Optional[float] = None
    edit_count: int = 0
    user_satisfaction_rating: Optional[int] = Field(default=None, ge=1, le=5)
    status: str = "draft"


class GenerationMetadataSchema(BaseModel):
    """Generation metadata response."""
    generation_time_ms: Optional[int] = None
    consistency_score: Optional[float] = None
    surfaces_count: int = 0


class ContentGenerationResponse(BaseModel):
    """Response for content generation."""
    generation_id: str
    brand_id: str
    generated_content: List[GeneratedContentSchema]
    generation_metadata: Optional[GenerationMetadataSchema] = None


class RegenerationRequest(BaseModel):
    """Request for regenerating content."""
    feedback_reason: FeedbackReasonEnum
    feedback_details: Optional[str] = Field(default=None, max_length=500)
    preferred_tone: Optional[VoiceToneEnum] = None
    preferred_length: Optional[LengthPreferenceEnum] = None


class ContentEditSchema(BaseModel):
    """Content edit details."""
    original_text: Optional[str] = None
    modified_text: Optional[str] = None
    edit_type: Optional[str] = None


class PreferencesSchema(BaseModel):
    """User preferences."""
    tone_preference: Optional[str] = None
    emphasis_areas: List[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    """Request for submitting feedback."""
    feedback_type: FeedbackTypeEnum
    generation_id: Optional[str] = None
    satisfaction_rating: Optional[int] = Field(default=None, ge=1, le=5)
    content_edits: Optional[ContentEditSchema] = None
    preferences: Optional[PreferencesSchema] = None
    feedback_text: Optional[str] = Field(default=None, max_length=1000)


class ContentRequirementsSchema(BaseModel):
    """Content requirements for a surface."""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    tone_guidelines: List[str] = Field(default_factory=list)
    structure_requirements: List[str] = Field(default_factory=list)


class ProfessionalSurfaceSchema(BaseModel):
    """Professional surface response."""
    surface_id: str
    surface_type: str
    surface_name: str
    content_requirements: ContentRequirementsSchema
    template_structure: Optional[str] = None
    active: bool = True
