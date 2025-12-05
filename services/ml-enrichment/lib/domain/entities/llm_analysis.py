"""
LLM Analysis Domain Entities

Entities representing LLM analysis results for brand analysis.
These are used by the brand analysis module for theme extraction,
voice analysis, and narrative arc detection.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class LLMThemeResult:
    """Theme extracted using LLM analysis."""
    theme_name: str
    confidence: float
    evidence: List[str]  # Supporting quotes from document
    context: str  # Section where theme was identified
    reasoning: str  # LLM explanation for theme identification
    source: str = "llm"  # Analysis method
    
    def __post_init__(self):
        """Validate theme result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
        if not self.theme_name.strip():
            raise ValueError("Theme name cannot be empty")


@dataclass
class LLMVoiceCharacteristics:
    """Voice characteristics extracted using LLM analysis."""
    tone: str  # professional, friendly, analytical, creative
    formality: float  # 0.0 = casual, 1.0 = formal
    energy: float  # 0.0 = calm, 1.0 = high-energy  
    communication_style: List[str]  # data-driven, storytelling, technical, collaborative
    vocabulary_complexity: str  # technical, business, accessible
    evidence_quotes: List[str]  # Supporting text examples
    confidence_score: float
    
    def __post_init__(self):
        """Validate voice characteristics."""
        if not 0.0 <= self.formality <= 1.0:
            raise ValueError("Formality must be between 0 and 1")
        if not 0.0 <= self.energy <= 1.0:
            raise ValueError("Energy must be between 0 and 1")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0 and 1")


@dataclass
class LLMNarrativeArc:
    """Career narrative arc extracted using LLM analysis."""
    progression_pattern: str  # technical_to_leadership, specialist_expert, cross_domain
    value_proposition: str  # innovation_driver, problem_solver, strategic_thinker
    future_positioning: str  # senior_technical_lead, strategic_advisor, domain_expert
    timeline_evidence: List[Dict[str, Any]]  # [{"period": "2020-2023", "role": "...", "growth": "..."}]
    confidence_score: float
    supporting_narrative: str  # LLM-generated explanation
    
    def __post_init__(self):
        """Validate narrative arc."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0 and 1")
        if not self.progression_pattern.strip():
            raise ValueError("Progression pattern cannot be empty")


@dataclass
class LLMAnalysisResult:
    """Complete LLM analysis result for a document."""
    themes: List[LLMThemeResult]
    voice_characteristics: LLMVoiceCharacteristics
    narrative_arc: LLMNarrativeArc
    overall_confidence: float
    model_version: str  # gemini-flash-1.5, gemini-pro-1.5
    tokens_used: int
    processing_time_ms: int
    analysis_timestamp: datetime
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    
    def __post_init__(self):
        """Validate analysis result."""
        if not 0.0 <= self.overall_confidence <= 1.0:
            raise ValueError("Overall confidence must be between 0 and 1")
        if self.tokens_used < 0:
            raise ValueError("Tokens used cannot be negative")


@dataclass
class ContentGenerationRequest:
    """Request for platform-specific content generation."""
    brand_id: str
    platform: str  # linkedin, cv_summary, portfolio_intro
    content_type: str  # summary, bio, introduction
    target_audience: str  # recruiters, peers, clients
    tone_preference: Optional[str] = None  # override brand voice if specified
    length_constraint: Optional[int] = None  # word count limit
    additional_context: Optional[str] = None  # user-provided context


@dataclass
class LLMContentGeneration:
    """LLM-generated content for specific platform."""
    content: str
    platform: str
    confidence_score: float
    word_count: int
    tone_match_score: float  # How well it matches brand voice (0-1)
    prompt_version: str
    generation_reasoning: str  # LLM explanation of choices made
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate generated content."""
        if not self.content.strip():
            raise ValueError("Content cannot be empty")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0 and 1")
        if not 0.0 <= self.tone_match_score <= 1.0:
            raise ValueError("Tone match score must be between 0 and 1")
        if self.word_count == 0 and self.content:
            self.word_count = len(self.content.split())


@dataclass
class APICall:
    """Record of Vertex AI API interaction for monitoring."""
    call_id: str
    model_name: str  # gemini-flash, gemini-pro
    call_type: str  # theme_extraction, voice_analysis, narrative_analysis, content_generation
    tokens_used: int
    response_time_ms: int
    success: bool
    error_message: Optional[str] = None
    cost_estimate: Optional[float] = None  # USD estimate
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate API call record."""
        if self.tokens_used < 0:
            raise ValueError("Tokens used cannot be negative")
        if self.response_time_ms < 0:
            raise ValueError("Response time cannot be negative")
