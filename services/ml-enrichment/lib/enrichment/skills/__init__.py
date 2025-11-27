"""
Skills extraction module with clean architecture.

This module provides skills extraction from job postings using:
- Multiple extraction strategies (lexicon, NER, noun chunks)
- Configurable filtering and scoring
- Pluggable storage backends
"""

from .config import SkillsConfig
from .extractor import SkillsExtractor

__all__ = ['SkillsConfig', 'SkillsExtractor']
