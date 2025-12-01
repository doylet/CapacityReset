"""
Skills extraction module with unified architecture.

This module provides skills extraction from job postings using:
- Unified extraction with automatic enhanced/original fallback
- Multiple extraction strategies (lexicon, semantic, patterns, NER, noun chunks)
- Configurable filtering and scoring
- Pluggable storage backends
- Advanced ML features when dependencies are available
"""

# Import unified implementations
from .unified_config import UnifiedSkillsConfig
from .unified_extractor import UnifiedSkillsExtractor

# Backward compatibility aliases
SkillsConfig = UnifiedSkillsConfig  # Original name
SkillsExtractor = UnifiedSkillsExtractor  # Original name
EnhancedSkillsConfig = UnifiedSkillsConfig  # Enhanced name
EnhancedSkillsExtractor = UnifiedSkillsExtractor  # Enhanced name

__all__ = [
    'UnifiedSkillsConfig', 'UnifiedSkillsExtractor',  # New unified names
    'SkillsConfig', 'SkillsExtractor',  # Original compatibility
    'EnhancedSkillsConfig', 'EnhancedSkillsExtractor'  # Enhanced compatibility
]
