"""
Analysis Orchestrator for Brand Analysis

Coordinates LLM-powered analysis with fallback strategies and error handling.
Implements the main business logic for brand analysis processing.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..adapters.vertex_ai_adapter import VertexAIAnalysisAdapter
from ..utils.llm_cache import LLMCache
from ...domain.entities import LLMAnalysisResult, LLMThemeResult, LLMVoiceCharacteristics, LLMNarrativeArc
from google.cloud import bigquery


class BrandAnalysisOrchestrator:
    """
    Orchestrates brand analysis using LLM with fallback capabilities.
    
    Implements the main analysis workflow:
    1. Check cache for existing results
    2. Attempt LLM analysis via Vertex AI
    3. Fall back to keyword analysis if LLM fails
    4. Cache successful results
    """
    
    def __init__(self, bigquery_client: bigquery.Client):
        self.vertex_adapter = VertexAIAnalysisAdapter()
        self.cache = LLMCache(bigquery_client)
        self.logger = logging.getLogger(__name__)
        
    async def analyze_document(
        self,
        document_content: str,
        job_posting_id: str,
        analysis_version: str = "v1.0"
    ) -> LLMAnalysisResult:
        """
        Complete document analysis using LLM with fallback.
        
        Args:
            document_content: CV/resume text content
            job_posting_id: Unique identifier for tracking
            analysis_version: Version for model iteration tracking
            
        Returns:
            Complete analysis result with themes, voice, and narrative
        """
        start_time = datetime.now()
        model_version = "gemini-flash"  # From environment
        fallback_used = False
        fallback_reason = None
        
        try:
            # Attempt LLM analysis with parallel processing
            self.logger.info(f"Starting LLM analysis for job {job_posting_id}")
            
            # Run all analysis types concurrently for efficiency
            themes_task = self._analyze_themes_with_cache(document_content, model_version)
            voice_task = self._analyze_voice_with_cache(document_content, model_version)  
            narrative_task = self._analyze_narrative_with_cache(document_content, model_version)
            
            themes, voice_characteristics, narrative_arc = await asyncio.gather(
                themes_task, voice_task, narrative_task
            )
            
            # Calculate overall confidence as weighted average
            theme_conf = sum(t.confidence for t in themes) / len(themes) if themes else 0.0
            overall_confidence = (
                theme_conf * 0.4 + 
                voice_characteristics.confidence_score * 0.3 + 
                narrative_arc.confidence_score * 0.3
            )
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result = LLMAnalysisResult(
                themes=themes,
                voice_characteristics=voice_characteristics,
                narrative_arc=narrative_arc,
                overall_confidence=overall_confidence,
                model_version=model_version,
                tokens_used=self._estimate_tokens_used(themes, voice_characteristics, narrative_arc),
                processing_time_ms=processing_time,
                analysis_timestamp=datetime.now(),
                fallback_used=fallback_used,
                fallback_reason=fallback_reason
            )
            
            self.logger.info(f"LLM analysis completed for job {job_posting_id} - confidence: {overall_confidence:.2f}")
            return result
            
        except Exception as e:
            self.logger.warning(f"LLM analysis failed for job {job_posting_id}: {e}")
            
            # Fall back to keyword-based analysis
            fallback_used = True
            fallback_reason = f"LLM failure: {str(e)[:100]}"
            
            try:
                fallback_result = await self._fallback_analysis(document_content)
                processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                result = LLMAnalysisResult(
                    themes=fallback_result["themes"],
                    voice_characteristics=fallback_result["voice_characteristics"],
                    narrative_arc=fallback_result["narrative_arc"],
                    overall_confidence=0.6,  # Lower confidence for keyword analysis
                    model_version="keyword-fallback",
                    tokens_used=0,
                    processing_time_ms=processing_time,
                    analysis_timestamp=datetime.now(),
                    fallback_used=fallback_used,
                    fallback_reason=fallback_reason
                )
                
                self.logger.info(f"Fallback analysis completed for job {job_posting_id}")
                return result
                
            except Exception as fallback_error:
                self.logger.error(f"Fallback analysis also failed for job {job_posting_id}: {fallback_error}")
                raise Exception(f"Both LLM and fallback analysis failed: {e}, {fallback_error}")
                
    async def _analyze_themes_with_cache(
        self, 
        content: str, 
        model_version: str
    ) -> List[LLMThemeResult]:
        """Analyze themes with cache check."""
        # Check cache first
        cached_result = await self.cache.get(
            content=content,
            prompt_template_version="theme_extraction_v1",
            model_version=model_version,
            analysis_type="theme_extraction"
        )
        
        if cached_result:
            # Convert cached result back to entities
            themes = []
            for theme_data in cached_result["result"]:
                theme = LLMThemeResult(
                    theme_name=theme_data["theme_name"],
                    confidence=theme_data["confidence"],
                    evidence=theme_data["evidence"],
                    context=theme_data["context"],
                    reasoning=theme_data["reasoning"]
                )
                themes.append(theme)
            return themes
            
        # Run LLM analysis
        themes = await self.vertex_adapter.extract_themes(content, "theme_extraction_v1")
        
        # Cache the result
        cache_data = []
        for theme in themes:
            cache_data.append({
                "theme_name": theme.theme_name,
                "confidence": theme.confidence,
                "evidence": theme.evidence,
                "context": theme.context,
                "reasoning": theme.reasoning
            })
            
        await self.cache.set(
            content=content,
            prompt_template_version="theme_extraction_v1",
            model_version=model_version,
            analysis_type="theme_extraction",
            llm_response="",  # Would store raw response in production
            parsed_result=cache_data,
            confidence_score=sum(t.confidence for t in themes) / len(themes) if themes else 0.0,
            tokens_used=len(content.split()) + 200,  # Estimate
            response_time_ms=1000  # Estimate
        )
        
        return themes
        
    async def _analyze_voice_with_cache(
        self, 
        content: str, 
        model_version: str
    ) -> LLMVoiceCharacteristics:
        """Analyze voice with cache check."""
        cached_result = await self.cache.get(
            content=content,
            prompt_template_version="voice_analysis_v1",
            model_version=model_version,
            analysis_type="voice_analysis"
        )
        
        if cached_result:
            data = cached_result["result"]
            return LLMVoiceCharacteristics(
                tone=data["tone"],
                formality=data["formality"],
                energy=data["energy"],
                communication_style=data["communication_style"],
                vocabulary_complexity=data["vocabulary_complexity"],
                evidence_quotes=data["evidence_quotes"],
                confidence_score=data["confidence_score"]
            )
            
        # Run LLM analysis
        voice_characteristics = await self.vertex_adapter.analyze_voice_characteristics(content, "voice_analysis_v1")
        
        # Cache the result
        cache_data = {
            "tone": voice_characteristics.tone,
            "formality": voice_characteristics.formality,
            "energy": voice_characteristics.energy,
            "communication_style": voice_characteristics.communication_style,
            "vocabulary_complexity": voice_characteristics.vocabulary_complexity,
            "evidence_quotes": voice_characteristics.evidence_quotes,
            "confidence_score": voice_characteristics.confidence_score
        }
        
        await self.cache.set(
            content=content,
            prompt_template_version="voice_analysis_v1",
            model_version=model_version,
            analysis_type="voice_analysis",
            llm_response="",
            parsed_result=cache_data,
            confidence_score=voice_characteristics.confidence_score,
            tokens_used=len(content.split()) + 150,
            response_time_ms=800
        )
        
        return voice_characteristics
        
    async def _analyze_narrative_with_cache(
        self, 
        content: str, 
        model_version: str
    ) -> LLMNarrativeArc:
        """Analyze narrative arc with cache check."""
        cached_result = await self.cache.get(
            content=content,
            prompt_template_version="narrative_analysis_v1",
            model_version=model_version,
            analysis_type="narrative_analysis"
        )
        
        if cached_result:
            data = cached_result["result"]
            return LLMNarrativeArc(
                progression_pattern=data["progression_pattern"],
                value_proposition=data["value_proposition"],
                future_positioning=data["future_positioning"],
                timeline_evidence=data["timeline_evidence"],
                confidence_score=data["confidence_score"],
                supporting_narrative=data["supporting_narrative"]
            )
            
        # Run LLM analysis
        narrative_arc = await self.vertex_adapter.analyze_narrative_arc(content, "narrative_analysis_v1")
        
        # Cache the result
        cache_data = {
            "progression_pattern": narrative_arc.progression_pattern,
            "value_proposition": narrative_arc.value_proposition,
            "future_positioning": narrative_arc.future_positioning,
            "timeline_evidence": narrative_arc.timeline_evidence,
            "confidence_score": narrative_arc.confidence_score,
            "supporting_narrative": narrative_arc.supporting_narrative
        }
        
        await self.cache.set(
            content=content,
            prompt_template_version="narrative_analysis_v1",
            model_version=model_version,
            analysis_type="narrative_analysis",
            llm_response="",
            parsed_result=cache_data,
            confidence_score=narrative_arc.confidence_score,
            tokens_used=len(content.split()) + 180,
            response_time_ms=900
        )
        
        return narrative_arc
        
    async def _fallback_analysis(self, content: str) -> Dict[str, Any]:
        """
        Keyword-based fallback analysis when LLM is unavailable.
        
        Uses simple pattern matching and heuristics for basic analysis.
        """
        self.logger.info("Using keyword-based fallback analysis")
        
        # Simple keyword-based theme extraction
        themes = []
        leadership_keywords = ["led", "managed", "coordinated", "directed", "supervised"]
        technical_keywords = ["developed", "implemented", "designed", "built", "programmed"]
        
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in leadership_keywords):
            themes.append(LLMThemeResult(
                theme_name="leadership",
                confidence=0.7,
                evidence=["Contains leadership keywords"],
                context="keyword_analysis",
                reasoning="Pattern matching for leadership terms"
            ))
            
        if any(keyword in content_lower for keyword in technical_keywords):
            themes.append(LLMThemeResult(
                theme_name="technical_expertise",
                confidence=0.7,
                evidence=["Contains technical keywords"],
                context="keyword_analysis",
                reasoning="Pattern matching for technical terms"
            ))
            
        # Basic voice analysis
        voice_characteristics = LLMVoiceCharacteristics(
            tone="professional",
            formality=0.8,
            energy=0.6,
            communication_style=["results-oriented"],
            vocabulary_complexity="professional",
            evidence_quotes=["Keyword-based analysis"],
            confidence_score=0.6
        )
        
        # Basic narrative analysis
        narrative_arc = LLMNarrativeArc(
            progression_pattern="general_professional",
            value_proposition="experienced_professional",
            future_positioning="continued_growth",
            timeline_evidence=[],
            confidence_score=0.5,
            supporting_narrative="Basic keyword-based career analysis"
        )
        
        return {
            "themes": themes,
            "voice_characteristics": voice_characteristics,
            "narrative_arc": narrative_arc
        }
        
    def _estimate_tokens_used(
        self, 
        themes: List[LLMThemeResult], 
        voice: LLMVoiceCharacteristics, 
        narrative: LLMNarrativeArc
    ) -> int:
        """Estimate total tokens used across all analysis calls."""
        # Rough estimation based on response complexity
        theme_tokens = len(themes) * 50
        voice_tokens = 100
        narrative_tokens = len(narrative.timeline_evidence) * 30 + 150
        
        return theme_tokens + voice_tokens + narrative_tokens