"""
Analysis Orchestrator for Brand Analysis

Coordinates LLM-powered analysis with fallback strategies and error handling.
Implements the main business logic for brand analysis processing.
"""

import logging
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from .vertex_analyzer import VertexAnalyzer
from .fallback_analyzer import FallbackAnalyzer
from ..adapters.vertex_ai_adapter import VertexAIAnalysisAdapter
from ..utils.llm_cache import LLMCache
from ..domain.entities import LLMAnalysisResult, LLMThemeResult, LLMVoiceCharacteristics, LLMNarrativeArc
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
    
    # Confidence thresholds for analysis quality
    MIN_THEME_CONFIDENCE = 0.3
    MIN_VOICE_CONFIDENCE = 0.4
    MIN_NARRATIVE_CONFIDENCE = 0.4
    
    # Analysis timeout in seconds
    ANALYSIS_TIMEOUT = 30
    
    def __init__(self, bigquery_client: bigquery.Client):
        self.vertex_adapter = VertexAIAnalysisAdapter()
        self.vertex_analyzer = VertexAnalyzer()
        self.fallback = FallbackAnalyzer()
        self.cache = LLMCache(bigquery_client)
        self.logger = logging.getLogger(__name__)
        self.model_version = os.getenv("GEMINI_MODEL_NAME", "gemini-flash")
        
    async def analyze_document(
        self,
        document_content: str,
        job_posting_id: str,
        analysis_version: str = "v1.0",
        use_enhanced_analyzer: bool = True
    ) -> LLMAnalysisResult:
        """
        Complete document analysis using LLM with fallback.
        
        Args:
            document_content: CV/resume text content
            job_posting_id: Unique identifier for tracking
            analysis_version: Version for model iteration tracking
            use_enhanced_analyzer: Whether to use the enhanced VertexAnalyzer
            
        Returns:
            Complete analysis result with themes, voice, and narrative
        """
        start_time = datetime.now()
        model_version = self.model_version
        fallback_used = False
        fallback_reason = None
        analysis_metadata = {
            "job_posting_id": job_posting_id,
            "analysis_version": analysis_version,
            "document_length": len(document_content),
            "word_count": len(document_content.split())
        }
        
        try:
            # Attempt LLM analysis with parallel processing and timeout
            self.logger.info(f"Starting LLM analysis for job {job_posting_id}")
            
            if use_enhanced_analyzer:
                # Use enhanced VertexAnalyzer with better error handling
                themes_task = self._analyze_themes_enhanced(document_content)
                voice_task = self._analyze_voice_enhanced(document_content)  
                narrative_task = self._analyze_narrative_enhanced(document_content)
            else:
                # Use original analysis with cache
                themes_task = self._analyze_themes_with_cache(document_content, model_version)
                voice_task = self._analyze_voice_with_cache(document_content, model_version)  
                narrative_task = self._analyze_narrative_with_cache(document_content, model_version)
            
            # Run with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(themes_task, voice_task, narrative_task, return_exceptions=True),
                    timeout=self.ANALYSIS_TIMEOUT
                )
                
                # Handle individual task failures
                themes, voice_characteristics, narrative_arc = self._handle_partial_failures(
                    results, document_content
                )
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Analysis timeout for job {job_posting_id}")
                fallback_used = True
                fallback_reason = "Analysis timeout exceeded"
                fallback_result = await self._fallback_analysis(document_content)
                themes = fallback_result["themes"]
                voice_characteristics = fallback_result["voice_characteristics"]
                narrative_arc = fallback_result["narrative_arc"]
            
            # Validate and filter low-confidence themes
            themes = self._filter_low_confidence_themes(themes)
            
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
        
    async def _analyze_themes_enhanced(self, content: str) -> List[LLMThemeResult]:
        """Analyze themes using enhanced VertexAnalyzer."""
        themes, metadata = await self.vertex_analyzer.extract_themes(
            document_content=content,
            prompt_version="v1",
            use_fallback_on_error=True
        )
        self.logger.debug(f"Theme extraction metadata: {metadata}")
        return themes
        
    async def _analyze_voice_enhanced(self, content: str) -> LLMVoiceCharacteristics:
        """Analyze voice using enhanced VertexAnalyzer."""
        voice, metadata = await self.vertex_analyzer.analyze_voice(
            document_content=content,
            prompt_version="v1",
            use_fallback_on_error=True
        )
        self.logger.debug(f"Voice analysis metadata: {metadata}")
        return voice
        
    async def _analyze_narrative_enhanced(self, content: str) -> LLMNarrativeArc:
        """Analyze narrative arc using enhanced VertexAnalyzer."""
        narrative, metadata = await self.vertex_analyzer.analyze_narrative_arc(
            document_content=content,
            prompt_version="v1",
            use_fallback_on_error=True
        )
        self.logger.debug(f"Narrative analysis metadata: {metadata}")
        return narrative
        
    def _handle_partial_failures(
        self,
        results: List[Any],
        document_content: str
    ) -> tuple:
        """
        Handle partial failures in parallel analysis.
        
        If any individual analysis fails, use fallback for that component
        while keeping successful results.
        """
        themes = results[0]
        voice = results[1]
        narrative = results[2]
        
        # Handle theme extraction failure
        if isinstance(themes, Exception):
            self.logger.warning(f"Theme extraction failed: {themes}")
            themes = self.fallback.analyze_themes(document_content)
            
        # Handle voice analysis failure  
        if isinstance(voice, Exception):
            self.logger.warning(f"Voice analysis failed: {voice}")
            voice = self.fallback.analyze_voice_characteristics(document_content)
            
        # Handle narrative analysis failure
        if isinstance(narrative, Exception):
            self.logger.warning(f"Narrative analysis failed: {narrative}")
            narrative = self.fallback.analyze_narrative_arc(document_content)
            
        return themes, voice, narrative
        
    def _filter_low_confidence_themes(
        self,
        themes: List[LLMThemeResult]
    ) -> List[LLMThemeResult]:
        """
        Filter out themes below the confidence threshold.
        
        Ensures only quality themes are returned to users.
        """
        filtered = [t for t in themes if t.confidence >= self.MIN_THEME_CONFIDENCE]
        
        if len(filtered) < len(themes):
            self.logger.info(
                f"Filtered {len(themes) - len(filtered)} low-confidence themes"
            )
            
        # Ensure at least one theme is returned
        if not filtered and themes:
            # Return the highest confidence theme
            filtered = [max(themes, key=lambda t: t.confidence)]
            
        return filtered
        
    async def analyze_themes_only(
        self,
        document_content: str,
        prompt_version: str = "v1"
    ) -> List[LLMThemeResult]:
        """
        Perform only theme extraction for focused analysis.
        
        Useful when only theme data is needed without full brand analysis.
        """
        try:
            themes, metadata = await self.vertex_analyzer.extract_themes(
                document_content=document_content,
                prompt_version=prompt_version,
                use_fallback_on_error=True
            )
            return self._filter_low_confidence_themes(themes)
        except Exception as e:
            self.logger.error(f"Theme-only analysis failed: {e}")
            return self.fallback.analyze_themes(document_content)
            
    async def analyze_voice_only(
        self,
        document_content: str,
        prompt_version: str = "v1"
    ) -> LLMVoiceCharacteristics:
        """
        Perform only voice analysis for focused analysis.
        """
        try:
            voice, metadata = await self.vertex_analyzer.analyze_voice(
                document_content=document_content,
                prompt_version=prompt_version,
                use_fallback_on_error=True
            )
            return voice
        except Exception as e:
            self.logger.error(f"Voice-only analysis failed: {e}")
            return self.fallback.analyze_voice_characteristics(document_content)