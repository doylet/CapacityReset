"""
Domain Package

Contains the domain model for the ML enrichment service:
- entities: Core domain entities (SkillAlias, ExtractedSkill, etc.)
- repositories: Port interfaces for data persistence
"""

from .entities import (
    SkillAlias,
    ExtractedSkill,
    SectionClassification,
    ClusterAssignment,
    EvaluationResult,
    JobEnrichment,
    # LLM Analysis entities
    LLMThemeResult,
    LLMVoiceCharacteristics,
    LLMNarrativeArc,
    LLMAnalysisResult,
    ContentGenerationRequest,
    LLMContentGeneration,
    APICall
)

from .repositories import (
    SkillAliasRepository,
    EvaluationResultRepository,
    SectionClassificationRepository
)

__all__ = [
    # Entities
    'SkillAlias',
    'ExtractedSkill',
    'SectionClassification',
    'ClusterAssignment',
    'EvaluationResult',
    'JobEnrichment',
    # LLM Analysis entities
    'LLMThemeResult',
    'LLMVoiceCharacteristics',
    'LLMNarrativeArc',
    'LLMAnalysisResult',
    'ContentGenerationRequest',
    'LLMContentGeneration',
    'APICall',
    
    # Repositories
    'SkillAliasRepository',
    'EvaluationResultRepository',
    'SectionClassificationRepository'
]
