"""
Brand Analysis Module for LLM-powered professional brand extraction.

This module provides intelligent analysis of professional documents (CVs, resumes)
using Vertex AI Gemini to extract themes, voice characteristics, and narrative arcs.
"""

from .vertex_analyzer import VertexAnalyzer
from .prompt_templates import PromptTemplates
from .fallback_analyzer import FallbackAnalyzer
from .analysis_orchestrator import BrandAnalysisOrchestrator
from .llm_cache_utility import LLMCacheUtility

__version__ = "1.0.0"

__all__ = [
    "VertexAnalyzer",
    "PromptTemplates",
    "FallbackAnalyzer",
    "BrandAnalysisOrchestrator",
    "LLMCacheUtility",
]