"""
Domain Repositories Package

Exports all repository interfaces (ports) for the ML enrichment service.
These interfaces define the contracts for data persistence operations.
"""

from .skill_alias_repository import SkillAliasRepository
from .evaluation_repository import EvaluationResultRepository
from .section_classification_repository import SectionClassificationRepository

__all__ = [
    'SkillAliasRepository',
    'EvaluationResultRepository',
    'SectionClassificationRepository'
]
