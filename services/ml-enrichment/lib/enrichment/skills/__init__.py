"""
Skills extraction module with clean architecture.

This module provides skills extraction from job postings using:
- Multiple extraction strategies (lexicon, NER, noun chunks)
- Configurable filtering and scoring
- Pluggable storage backends
- Enhanced ML features (semantic similarity, pattern extraction)
"""

from .config import SkillsConfig
from .extractor import SkillsExtractor

# Enhanced features (import if available)
try:
    from .enhanced_config import EnhancedSkillsConfig
    from .enhanced_extractor import EnhancedSkillsExtractor
    __all__ = ['SkillsConfig', 'SkillsExtractor', 'EnhancedSkillsConfig', 'EnhancedSkillsExtractor']
except ImportError:
    # Enhanced features not available
    __all__ = ['SkillsConfig', 'SkillsExtractor']
