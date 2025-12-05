"""
Vertex AI Adapter for LLM Integration

Implements domain interfaces for Vertex AI Gemini integration while maintaining
hexagonal architecture separation.
"""

import os
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, SafetySetting, HarmCategory
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Vertex AI SDK not available - LLM features disabled")

from ..domain.entities import (
    LLMAnalysisResult, LLMThemeResult, LLMVoiceCharacteristics, 
    LLMNarrativeArc, APICall, LLMContentGeneration
)


# Global singleton clients (lazy-loaded per constitution Principle V)
_vertex_client = None
_gemini_model = None


def get_vertex_client() -> Optional[Any]:
    """
    Lazy-load Vertex AI client (Constitution Principle V).
    Returns None if Vertex AI not available.
    """
    global _vertex_client
    
    if not VERTEX_AI_AVAILABLE:
        return None
        
    if _vertex_client is None:
        try:
            project_id = os.getenv("VERTEX_AI_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT"))
            location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
            
            if not project_id:
                logging.error("No VERTEX_AI_PROJECT_ID or GOOGLE_CLOUD_PROJECT configured")
                return None
                
            vertexai.init(project=project_id, location=location)
            _vertex_client = True  # Just a flag that init succeeded
            logging.info(f"Vertex AI initialized for project {project_id} in {location}")
            
        except Exception as e:
            logging.error(f"Failed to initialize Vertex AI: {e}")
            return None
            
    return _vertex_client


def get_gemini_model() -> Optional[GenerativeModel]:
    """
    Lazy-load Gemini model (Constitution Principle V).
    Returns None if model not available.
    """
    global _gemini_model
    
    if not get_vertex_client():
        return None
        
    if _gemini_model is None:
        try:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-flash")
            
            # Safety settings to prevent blocking of professional content
            safety_settings = [
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
            ]
            
            _gemini_model = GenerativeModel(
                model_name=model_name,
                safety_settings=safety_settings
            )
            logging.info(f"Gemini model {model_name} loaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to load Gemini model: {e}")
            return None
            
    return _gemini_model


class VertexAIAnalysisAdapter:
    """
    Vertex AI adapter implementing domain analysis interfaces.
    
    Provides LLM-powered analysis while maintaining fallback capabilities
    and proper error handling according to constitution principles.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        
    async def extract_themes(
        self, 
        document_content: str,
        prompt_version: str = "v1"
    ) -> List[LLMThemeResult]:
        """
        Extract professional themes using LLM analysis.
        
        Args:
            document_content: CV/resume text content
            prompt_version: Version of prompt template to use
            
        Returns:
            List of extracted themes with evidence
        """
        model = get_gemini_model()
        if not model:
            raise RuntimeError("Vertex AI Gemini model not available")
            
        # Theme extraction prompt (constitution-compliant - no HEREDOC)
        prompt = f"""
        Analyze this professional document and extract key themes that represent the person's professional identity.
        
        For each theme, provide:
        1. Theme name (2-3 words)
        2. Confidence score (0.0-1.0)  
        3. Evidence quotes from the text
        4. Brief reasoning for the theme
        
        Document content:
        {document_content}
        
        Return response as JSON:
        {{
            "themes": [
                {{
                    "name": "strategic leadership",
                    "confidence": 0.95,
                    "evidence": ["coordinated cross-functional initiatives", "led team of 15"],
                    "reasoning": "Multiple examples of leading teams and strategic initiatives"
                }}
            ]
        }}
        """
        
        try:
            start_time = datetime.now()
            response = model.generate_content(prompt)
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Parse LLM response
            result_json = json.loads(response.text.strip())
            themes = []
            
            for theme_data in result_json.get("themes", []):
                theme = LLMThemeResult(
                    theme_name=theme_data["name"],
                    confidence=theme_data["confidence"], 
                    evidence=theme_data["evidence"],
                    context="full_document",  # Could be enhanced to track sections
                    reasoning=theme_data["reasoning"]
                )
                themes.append(theme)
                
            # Log API usage
            await self._log_api_call(
                call_type="theme_extraction",
                model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-flash"),
                tokens_used=len(response.text.split()),  # Approximate
                response_time_ms=processing_time,
                success=True
            )
            
            return themes
            
        except Exception as e:
            self.logger.error(f"Theme extraction failed: {e}")
            await self._log_api_call(
                call_type="theme_extraction",
                model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-flash"),
                tokens_used=0,
                response_time_ms=0,
                success=False,
                error_message=str(e)
            )
            raise
            
    async def analyze_voice_characteristics(
        self,
        document_content: str,
        prompt_version: str = "v1"
    ) -> LLMVoiceCharacteristics:
        """
        Analyze voice and communication style using LLM.
        
        Args:
            document_content: CV/resume text content
            prompt_version: Version of prompt template
            
        Returns:
            Voice characteristics with evidence
        """
        model = get_gemini_model()
        if not model:
            raise RuntimeError("Vertex AI Gemini model not available")
            
        prompt = f"""
        Analyze the writing style and voice characteristics of this professional document.
        
        Assess:
        1. Tone (professional, analytical, creative, friendly)
        2. Formality level (0.0=casual, 1.0=formal)
        3. Energy level (0.0=calm, 1.0=dynamic)
        4. Communication style tags
        5. Vocabulary complexity
        
        Provide evidence quotes that support your analysis.
        
        Document content:
        {document_content}
        
        Return as JSON:
        {{
            "tone": "professional",
            "formality": 0.8,
            "energy": 0.6,
            "communication_style": ["data-driven", "results-oriented"],
            "vocabulary_complexity": "technical professional",
            "evidence_quotes": ["achieved 40% improvement in efficiency", "led cross-functional team"],
            "confidence_score": 0.92
        }}
        """
        
        try:
            start_time = datetime.now()
            response = model.generate_content(prompt)
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result_json = json.loads(response.text.strip())
            
            voice_characteristics = LLMVoiceCharacteristics(
                tone=result_json["tone"],
                formality=result_json["formality"],
                energy=result_json["energy"],
                communication_style=result_json["communication_style"],
                vocabulary_complexity=result_json["vocabulary_complexity"],
                evidence_quotes=result_json["evidence_quotes"],
                confidence_score=result_json["confidence_score"]
            )
            
            await self._log_api_call(
                call_type="voice_analysis",
                model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-flash"),
                tokens_used=len(response.text.split()),
                response_time_ms=processing_time,
                success=True
            )
            
            return voice_characteristics
            
        except Exception as e:
            self.logger.error(f"Voice analysis failed: {e}")
            await self._log_api_call(
                call_type="voice_analysis", 
                model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-flash"),
                tokens_used=0,
                response_time_ms=0,
                success=False,
                error_message=str(e)
            )
            raise
            
    async def analyze_narrative_arc(
        self,
        document_content: str,
        prompt_version: str = "v1"
    ) -> LLMNarrativeArc:
        """
        Analyze career narrative arc using LLM.
        
        Args:
            document_content: CV/resume text content
            prompt_version: Version of prompt template
            
        Returns:
            Narrative arc analysis with timeline evidence
        """
        model = get_gemini_model()
        if not model:
            raise RuntimeError("Vertex AI Gemini model not available")
            
        prompt = f"""
        Analyze the career narrative and progression shown in this professional document.
        
        Identify:
        1. Progression pattern (technical_to_leadership, specialist_expert, cross_domain)
        2. Core value proposition (innovation_driver, problem_solver, strategic_thinker) 
        3. Future positioning trajectory
        4. Timeline evidence with role progression
        
        Document content:
        {document_content}
        
        Return as JSON:
        {{
            "progression_pattern": "technical_to_leadership",
            "value_proposition": "innovation_driver", 
            "future_positioning": "senior_technical_lead",
            "timeline_evidence": [
                {{"period": "2020-2023", "role": "Senior Engineer", "growth": "Led team and drove architecture decisions"}}
            ],
            "confidence_score": 0.88,
            "supporting_narrative": "Shows clear progression from individual contributor to technical leadership..."
        }}
        """
        
        try:
            start_time = datetime.now()
            response = model.generate_content(prompt)
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result_json = json.loads(response.text.strip())
            
            narrative_arc = LLMNarrativeArc(
                progression_pattern=result_json["progression_pattern"],
                value_proposition=result_json["value_proposition"],
                future_positioning=result_json["future_positioning"],
                timeline_evidence=result_json["timeline_evidence"],
                confidence_score=result_json["confidence_score"],
                supporting_narrative=result_json["supporting_narrative"]
            )
            
            await self._log_api_call(
                call_type="narrative_analysis",
                model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-flash"),
                tokens_used=len(response.text.split()),
                response_time_ms=processing_time,
                success=True
            )
            
            return narrative_arc
            
        except Exception as e:
            self.logger.error(f"Narrative analysis failed: {e}")
            await self._log_api_call(
                call_type="narrative_analysis",
                model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-flash"), 
                tokens_used=0,
                response_time_ms=0,
                success=False,
                error_message=str(e)
            )
            raise
    
    async def _log_api_call(
        self,
        call_type: str,
        model_name: str, 
        tokens_used: int,
        response_time_ms: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Log API call for monitoring and billing tracking."""
        api_call = APICall(
            call_id=hashlib.md5(f"{datetime.now().isoformat()}{call_type}".encode()).hexdigest()[:8],
            model_name=model_name,
            call_type=call_type,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message
        )
        
        # In production, this would write to BigQuery or monitoring system
        self.logger.info(f"API Call: {api_call.call_type} - {api_call.success} - {api_call.tokens_used} tokens - {api_call.response_time_ms}ms")