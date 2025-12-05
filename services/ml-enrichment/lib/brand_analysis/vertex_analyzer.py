"""
Vertex AI Analyzer for LLM-Powered Brand Analysis

Implements theme extraction, voice analysis, and narrative arc analysis
using Vertex AI Gemini models with fallback and caching support.
"""

import os
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from ..adapters.vertex_ai_adapter import VertexAIAnalysisAdapter, get_gemini_model
from .prompt_templates import PromptTemplates
from .fallback_analyzer import FallbackAnalyzer
from ..domain.entities import LLMThemeResult, LLMVoiceCharacteristics, LLMNarrativeArc


class VertexAnalyzer:
    """
    LLM-powered brand analysis using Vertex AI Gemini.
    
    Provides enhanced theme extraction, voice analysis, and narrative arc
    detection with fallback to keyword-based analysis when LLM unavailable.
    """
    
    def __init__(self):
        self.adapter = VertexAIAnalysisAdapter()
        self.fallback = FallbackAnalyzer()
        self.logger = logging.getLogger(__name__)
        self.model_version = os.getenv("GEMINI_MODEL_NAME", "gemini-flash")
        
    async def extract_themes(
        self,
        document_content: str,
        prompt_version: str = "v1",
        use_fallback_on_error: bool = True
    ) -> Tuple[List[LLMThemeResult], Dict[str, Any]]:
        """
        Extract professional themes from document using LLM analysis.
        
        Args:
            document_content: CV/resume text content
            prompt_version: Version of prompt template to use
            use_fallback_on_error: Whether to use fallback on LLM failure
            
        Returns:
            Tuple of (themes list, metadata dict)
        """
        metadata = {
            "analysis_type": "theme_extraction",
            "prompt_version": prompt_version,
            "model_version": self.model_version,
            "fallback_used": False,
            "start_time": datetime.now()
        }
        
        try:
            # Get prompt template
            prompt_template = PromptTemplates.get_theme_extraction_prompt(prompt_version)
            formatted_prompt = PromptTemplates.format_prompt(
                prompt_template,
                document_content=self._prepare_document(document_content)
            )
            
            # Get Gemini model
            model = get_gemini_model()
            if not model:
                raise RuntimeError("Gemini model not available")
            
            self.logger.info(f"Extracting themes with {self.model_version}, prompt {prompt_version}")
            
            # Generate LLM response
            start_time = datetime.now()
            response = model.generate_content(formatted_prompt)
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Parse response
            themes = self._parse_theme_response(response.text)
            
            # Update metadata
            metadata.update({
                "processing_time_ms": processing_time_ms,
                "tokens_used": self._estimate_tokens(document_content, response.text),
                "themes_extracted": len(themes),
                "success": True
            })
            
            self.logger.info(f"Extracted {len(themes)} themes in {processing_time_ms}ms")
            return themes, metadata
            
        except Exception as e:
            self.logger.error(f"Theme extraction failed: {e}")
            
            if use_fallback_on_error:
                self.logger.info("Using fallback analyzer for theme extraction")
                themes = self.fallback.analyze_themes(document_content)
                
                metadata.update({
                    "fallback_used": True,
                    "fallback_reason": str(e),
                    "themes_extracted": len(themes),
                    "success": True
                })
                
                return themes, metadata
            else:
                metadata["success"] = False
                metadata["error"] = str(e)
                raise
                
    async def analyze_voice(
        self,
        document_content: str,
        prompt_version: str = "v1",
        use_fallback_on_error: bool = True
    ) -> Tuple[LLMVoiceCharacteristics, Dict[str, Any]]:
        """
        Analyze voice and communication characteristics using LLM.
        
        Args:
            document_content: CV/resume text content
            prompt_version: Version of prompt template
            use_fallback_on_error: Whether to use fallback on LLM failure
            
        Returns:
            Tuple of (voice characteristics, metadata dict)
        """
        metadata = {
            "analysis_type": "voice_analysis",
            "prompt_version": prompt_version,
            "model_version": self.model_version,
            "fallback_used": False,
            "start_time": datetime.now()
        }
        
        try:
            # Get prompt template
            prompt_template = PromptTemplates.get_voice_analysis_prompt(prompt_version)
            formatted_prompt = PromptTemplates.format_prompt(
                prompt_template,
                document_content=self._prepare_document(document_content)
            )
            
            # Get Gemini model
            model = get_gemini_model()
            if not model:
                raise RuntimeError("Gemini model not available")
            
            self.logger.info(f"Analyzing voice with {self.model_version}, prompt {prompt_version}")
            
            # Generate LLM response
            start_time = datetime.now()
            response = model.generate_content(formatted_prompt)
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Parse response
            voice_characteristics = self._parse_voice_response(response.text)
            
            # Update metadata
            metadata.update({
                "processing_time_ms": processing_time_ms,
                "tokens_used": self._estimate_tokens(document_content, response.text),
                "confidence": voice_characteristics.confidence_score,
                "success": True
            })
            
            self.logger.info(f"Voice analysis completed in {processing_time_ms}ms, confidence: {voice_characteristics.confidence_score}")
            return voice_characteristics, metadata
            
        except Exception as e:
            self.logger.error(f"Voice analysis failed: {e}")
            
            if use_fallback_on_error:
                self.logger.info("Using fallback analyzer for voice analysis")
                voice_characteristics = self.fallback.analyze_voice_characteristics(document_content)
                
                metadata.update({
                    "fallback_used": True,
                    "fallback_reason": str(e),
                    "confidence": voice_characteristics.confidence_score,
                    "success": True
                })
                
                return voice_characteristics, metadata
            else:
                metadata["success"] = False
                metadata["error"] = str(e)
                raise
                
    async def analyze_narrative_arc(
        self,
        document_content: str,
        prompt_version: str = "v1",
        use_fallback_on_error: bool = True
    ) -> Tuple[LLMNarrativeArc, Dict[str, Any]]:
        """
        Analyze career narrative arc using LLM.
        
        Args:
            document_content: CV/resume text content
            prompt_version: Version of prompt template
            use_fallback_on_error: Whether to use fallback on LLM failure
            
        Returns:
            Tuple of (narrative arc, metadata dict)
        """
        metadata = {
            "analysis_type": "narrative_analysis",
            "prompt_version": prompt_version,
            "model_version": self.model_version,
            "fallback_used": False,
            "start_time": datetime.now()
        }
        
        try:
            # Get prompt template
            prompt_template = PromptTemplates.get_narrative_analysis_prompt(prompt_version)
            formatted_prompt = PromptTemplates.format_prompt(
                prompt_template,
                document_content=self._prepare_document(document_content)
            )
            
            # Get Gemini model
            model = get_gemini_model()
            if not model:
                raise RuntimeError("Gemini model not available")
            
            self.logger.info(f"Analyzing narrative arc with {self.model_version}, prompt {prompt_version}")
            
            # Generate LLM response
            start_time = datetime.now()
            response = model.generate_content(formatted_prompt)
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Parse response
            narrative_arc = self._parse_narrative_response(response.text)
            
            # Update metadata
            metadata.update({
                "processing_time_ms": processing_time_ms,
                "tokens_used": self._estimate_tokens(document_content, response.text),
                "confidence": narrative_arc.confidence_score,
                "timeline_evidence_count": len(narrative_arc.timeline_evidence),
                "success": True
            })
            
            self.logger.info(f"Narrative analysis completed in {processing_time_ms}ms, confidence: {narrative_arc.confidence_score}")
            return narrative_arc, metadata
            
        except Exception as e:
            self.logger.error(f"Narrative analysis failed: {e}")
            
            if use_fallback_on_error:
                self.logger.info("Using fallback analyzer for narrative analysis")
                narrative_arc = self.fallback.analyze_narrative_arc(document_content)
                
                metadata.update({
                    "fallback_used": True,
                    "fallback_reason": str(e),
                    "confidence": narrative_arc.confidence_score,
                    "timeline_evidence_count": len(narrative_arc.timeline_evidence),
                    "success": True
                })
                
                return narrative_arc, metadata
            else:
                metadata["success"] = False
                metadata["error"] = str(e)
                raise
    
    def _prepare_document(self, content: str, max_length: int = 10000) -> str:
        """
        Prepare document content for LLM analysis.
        
        Cleans text and limits to max token length.
        """
        # Clean whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Truncate if too long
        if len(content) > max_length:
            content = content[:max_length] + "... [truncated]"
            self.logger.warning(f"Document truncated to {max_length} characters")
        
        return content
        
    def _parse_theme_response(self, response_text: str) -> List[LLMThemeResult]:
        """
        Parse LLM response to extract themes.
        
        Handles JSON parsing with error recovery.
        """
        try:
            # Try to extract JSON from response
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            
            themes = []
            for theme_data in result.get("themes", []):
                theme = LLMThemeResult(
                    theme_name=theme_data.get("name", "").strip(),
                    confidence=float(theme_data.get("confidence", 0.5)),
                    evidence=theme_data.get("evidence", []),
                    context="llm_analysis",
                    reasoning=theme_data.get("reasoning", ""),
                    source="llm"
                )
                themes.append(theme)
                
            return themes
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse theme response: {e}")
            # Return empty list if parsing fails
            return []
            
    def _parse_voice_response(self, response_text: str) -> LLMVoiceCharacteristics:
        """
        Parse LLM response to extract voice characteristics.
        """
        try:
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            
            return LLMVoiceCharacteristics(
                tone=result.get("tone", "professional"),
                formality=float(result.get("formality", 0.5)),
                energy=float(result.get("energy", 0.5)),
                communication_style=result.get("communication_style", []),
                vocabulary_complexity=result.get("vocabulary_complexity", "professional"),
                evidence_quotes=result.get("evidence_quotes", []),
                confidence_score=float(result.get("confidence_score", 0.5))
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse voice response: {e}")
            # Return default voice characteristics
            return LLMVoiceCharacteristics(
                tone="professional",
                formality=0.5,
                energy=0.5,
                communication_style=["professional"],
                vocabulary_complexity="professional",
                evidence_quotes=[],
                confidence_score=0.3  # Low confidence due to parsing failure
            )
            
    def _parse_narrative_response(self, response_text: str) -> LLMNarrativeArc:
        """
        Parse LLM response to extract narrative arc.
        """
        try:
            json_str = self._extract_json(response_text)
            result = json.loads(json_str)
            
            return LLMNarrativeArc(
                progression_pattern=result.get("progression_pattern", "general_professional"),
                value_proposition=result.get("value_proposition", "experienced_professional"),
                future_positioning=result.get("future_positioning", "continued_growth"),
                timeline_evidence=result.get("timeline_evidence", []),
                confidence_score=float(result.get("confidence_score", 0.5)),
                supporting_narrative=result.get("supporting_narrative", "")
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse narrative response: {e}")
            # Return default narrative arc
            return LLMNarrativeArc(
                progression_pattern="general_professional",
                value_proposition="experienced_professional",
                future_positioning="continued_growth",
                timeline_evidence=[],
                confidence_score=0.3,  # Low confidence due to parsing failure
                supporting_narrative="Unable to fully analyze narrative arc"
            )
            
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from LLM response text.
        
        Handles cases where JSON is wrapped in markdown code blocks.
        """
        # Try to find JSON in code block
        code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # Try to find raw JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # Return original text if no pattern found
        return text
        
    def _estimate_tokens(self, input_text: str, output_text: str) -> int:
        """
        Estimate token usage for input and output.
        
        Rough approximation: ~4 characters per token.
        """
        input_tokens = len(input_text) // 4
        output_tokens = len(output_text) // 4
        return input_tokens + output_tokens
