"""
Brand Analyzer - Professional Brand Theme and Voice Analysis

Extracts professional brand themes and voice characteristics from source documents
using Vertex AI Gemini. Provides detailed analysis of professional identity patterns
for consistent brand representation across surfaces.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Import Vertex AI adapter from Feature 003
from adapters.vertex_ai_adapter import VertexAIAdapter

# Import domain entities
import sys
sys.path.append('/Users/thomasdoyle/Daintree/frameworks/gcloud/CapacityReset/api/jobs-api')
from domain.entities import BrandRepresentation, ProfessionalTheme


class BrandAnalyzer:
    """
    Analyzes professional documents to extract brand themes and voice characteristics.
    
    Uses Vertex AI Gemini to perform deep analysis of professional content,
    identifying recurring themes, voice patterns, and narrative elements
    that define a professional brand identity.
    """
    
    def __init__(self):
        """Initialize BrandAnalyzer with Vertex AI adapter."""
        self.vertex_ai = VertexAIAdapter()
        self.logger = logging.getLogger(__name__)
    
    async def analyze_source_document(self, document_url: str, document_text: str, user_id: str) -> BrandRepresentation:
        """
        Analyze source document to extract complete brand representation.
        
        Args:
            document_url: URL/path to source document
            document_text: Raw text content of the document  
            user_id: ID of the user for brand ownership
            
        Returns:
            BrandRepresentation with extracted themes, voice, and narrative
        """
        self.logger.info(f"Starting brand analysis for user {user_id}, document: {document_url}")
        
        # Extract professional themes
        professional_themes = await self._extract_professional_themes(document_text)
        
        # Analyze voice characteristics
        voice_characteristics = await self._analyze_voice_characteristics(document_text)
        
        # Extract narrative arc
        narrative_arc = await self._extract_narrative_arc(document_text)
        
        # Calculate confidence scores
        confidence_scores = await self._calculate_confidence_scores(
            document_text, professional_themes, voice_characteristics, narrative_arc
        )
        
        # Create brand representation
        brand_representation = BrandRepresentation(
            user_id=user_id,
            source_document_url=document_url,
            professional_themes=professional_themes,
            voice_characteristics=voice_characteristics,
            narrative_arc=narrative_arc,
            confidence_scores=confidence_scores,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1
        )
        
        self.logger.info(f"Brand analysis complete. Extracted {len(professional_themes)} themes with confidence {confidence_scores.get('overall', 0):.2f}")
        
        return brand_representation
    
    async def _extract_professional_themes(self, document_text: str) -> List[Dict[str, Any]]:
        """
        Extract professional themes from document using Vertex AI analysis.
        
        Returns list of professional theme dictionaries with:
        - theme_name: Core theme identifier
        - keywords: Associated keywords and phrases
        - confidence: Confidence score for theme detection
        - evidence: Supporting text snippets
        """
        
        prompt = f"""
        Analyze the following professional document and extract the core professional themes.
        
        For each theme identified, provide:
        1. Theme name (concise, professional label)
        2. Associated keywords and phrases
        3. Confidence score (0.0 to 1.0)
        4. Supporting evidence from the text
        
        Focus on themes that reflect:
        - Industry expertise areas
        - Leadership and management styles
        - Technical capabilities
        - Professional values and approaches
        - Career progression patterns
        - Achievement categories
        
        Document text:
        {document_text}
        
        Return response as valid JSON array with objects containing:
        {{"theme_name": "...", "keywords": ["...", "..."], "confidence": 0.0, "evidence": ["quote1", "quote2"]}}
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=2048,
                temperature=0.1,  # Low temperature for consistent analysis
                top_p=0.8
            )
            
            # Parse JSON response
            themes_data = self._parse_json_response(response)
            
            if isinstance(themes_data, list):
                # Validate and clean theme data
                professional_themes = []
                for theme in themes_data:
                    if self._validate_theme_structure(theme):
                        professional_themes.append(theme)
                
                return professional_themes
            else:
                self.logger.warning("Theme extraction did not return expected list format")
                return []
                
        except Exception as e:
            self.logger.error(f"Error extracting professional themes: {str(e)}")
            return []
    
    async def _analyze_voice_characteristics(self, document_text: str) -> Dict[str, Any]:
        """
        Analyze voice and communication style characteristics.
        
        Returns voice characteristics dictionary with:
        - tone: Overall communication tone
        - style: Writing/communication style
        - personality_traits: Professional personality indicators
        - communication_patterns: Recurring patterns in expression
        - formality_level: Professional formality assessment
        """
        
        prompt = f"""
        Analyze the voice and communication style in this professional document.
        
        Examine and identify:
        1. Overall tone (e.g., confident, collaborative, analytical, innovative)
        2. Communication style (e.g., direct, narrative, technical, consultative)
        3. Professional personality traits evident in the writing
        4. Communication patterns and preferences
        5. Formality level and professional register
        
        Document text:
        {document_text}
        
        Return response as valid JSON object:
        {{
            "tone": "overall tone description",
            "style": "communication style",
            "personality_traits": ["trait1", "trait2"],
            "communication_patterns": ["pattern1", "pattern2"],
            "formality_level": "formal/professional/conversational",
            "confidence": 0.0
        }}
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.1,
                top_p=0.8
            )
            
            voice_data = self._parse_json_response(response)
            
            if isinstance(voice_data, dict):
                return voice_data
            else:
                self.logger.warning("Voice analysis did not return expected dictionary format")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error analyzing voice characteristics: {str(e)}")
            return {}
    
    async def _extract_narrative_arc(self, document_text: str) -> Dict[str, Any]:
        """
        Extract professional narrative structure and career arc.
        
        Returns narrative arc dictionary with:
        - career_progression: Key career development themes
        - achievement_patterns: Types and patterns of achievements
        - growth_narrative: Professional development story
        - future_direction: Implied career trajectory
        """
        
        prompt = f"""
        Analyze the professional narrative and career arc in this document.
        
        Extract:
        1. Career progression themes and patterns
        2. Achievement categories and progression
        3. Professional growth narrative elements
        4. Implied future direction or aspirations
        5. Professional identity evolution
        
        Document text:
        {document_text}
        
        Return response as valid JSON object:
        {{
            "career_progression": ["progression1", "progression2"],
            "achievement_patterns": ["pattern1", "pattern2"],
            "growth_narrative": "narrative description",
            "future_direction": "career trajectory",
            "professional_identity": "identity characterization",
            "confidence": 0.0
        }}
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.2,
                top_p=0.8
            )
            
            narrative_data = self._parse_json_response(response)
            
            if isinstance(narrative_data, dict):
                return narrative_data
            else:
                self.logger.warning("Narrative analysis did not return expected dictionary format")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error extracting narrative arc: {str(e)}")
            return {}
    
    async def _calculate_confidence_scores(
        self, 
        document_text: str, 
        themes: List[Dict[str, Any]], 
        voice: Dict[str, Any], 
        narrative: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate confidence scores for brand analysis components.
        
        Returns confidence scores for:
        - themes: Confidence in theme extraction
        - voice: Confidence in voice analysis
        - narrative: Confidence in narrative extraction
        - overall: Overall analysis confidence
        """
        
        # Base confidence on document length and completeness
        doc_length = len(document_text.split())
        length_confidence = min(1.0, doc_length / 1000)  # Full confidence at 1000+ words
        
        # Theme confidence based on number and quality of themes
        theme_confidence = 0.0
        if themes:
            avg_theme_conf = sum(theme.get('confidence', 0) for theme in themes) / len(themes)
            theme_count_factor = min(1.0, len(themes) / 5)  # Full confidence at 5+ themes
            theme_confidence = avg_theme_conf * theme_count_factor
        
        # Voice confidence based on analysis completeness
        voice_confidence = voice.get('confidence', 0.0)
        if voice.get('tone') and voice.get('style'):
            voice_confidence = max(voice_confidence, 0.7)
        
        # Narrative confidence
        narrative_confidence = narrative.get('confidence', 0.0)
        if narrative.get('career_progression') and narrative.get('growth_narrative'):
            narrative_confidence = max(narrative_confidence, 0.7)
        
        # Overall confidence as weighted average
        overall_confidence = (
            length_confidence * 0.2 +
            theme_confidence * 0.4 +
            voice_confidence * 0.2 +
            narrative_confidence * 0.2
        )
        
        return {
            'themes': theme_confidence,
            'voice': voice_confidence,
            'narrative': narrative_confidence,
            'document_completeness': length_confidence,
            'overall': overall_confidence
        }
    
    def _parse_json_response(self, response: str) -> Any:
        """Parse JSON response from Vertex AI, handling common formatting issues."""
        try:
            # Clean response - remove markdown code blocks if present
            cleaned = re.sub(r'```json\s*|\s*```', '', response)
            cleaned = cleaned.strip()
            
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Raw response: {response}")
            return None
    
    def _validate_theme_structure(self, theme: Dict[str, Any]) -> bool:
        """Validate that theme has required structure."""
        required_fields = ['theme_name', 'keywords', 'confidence']
        return all(field in theme for field in required_fields)
    
    async def update_brand_with_feedback(
        self, 
        brand: BrandRepresentation, 
        feedback_data: Dict[str, Any]
    ) -> BrandRepresentation:
        """
        Update brand representation based on user feedback.
        
        Args:
            brand: Current brand representation
            feedback_data: User feedback about brand accuracy
            
        Returns:
            Updated brand representation
        """
        self.logger.info(f"Updating brand {brand.brand_id} with user feedback")
        
        # Extract feedback insights
        feedback_insights = await self._analyze_feedback_insights(feedback_data)
        
        # Update themes based on feedback
        updated_themes = await self._refine_themes_with_feedback(
            brand.professional_themes, feedback_insights
        )
        
        # Update voice characteristics if feedback provided
        updated_voice = await self._refine_voice_with_feedback(
            brand.voice_characteristics, feedback_insights
        )
        
        # Update confidence scores
        updated_confidence = brand.confidence_scores.copy()
        updated_confidence['user_feedback_integrated'] = True
        updated_confidence['feedback_confidence'] = feedback_insights.get('confidence', 0.8)
        
        # Create updated brand representation
        brand.professional_themes = updated_themes
        brand.voice_characteristics = updated_voice
        brand.confidence_scores = updated_confidence
        brand.updated_at = datetime.utcnow()
        brand.version = (brand.version or 1) + 1
        
        self.logger.info(f"Brand update complete. New version: {brand.version}")
        
        return brand
    
    async def _analyze_feedback_insights(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user feedback to extract actionable insights."""
        
        prompt = f"""
        Analyze this user feedback about professional brand representation accuracy.
        
        Extract insights about:
        1. Which themes are accurate vs inaccurate
        2. Voice/tone adjustments needed
        3. Missing professional elements
        4. Over-emphasized aspects
        
        Feedback data:
        {json.dumps(feedback_data, indent=2)}
        
        Return as JSON:
        {{
            "theme_adjustments": {{"add": ["theme"], "remove": ["theme"], "emphasize": ["theme"]}},
            "voice_adjustments": {{"tone": "adjustment", "style": "adjustment"}},
            "confidence": 0.0
        }}
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.1,
                top_p=0.8
            )
            
            return self._parse_json_response(response) or {}
        except Exception as e:
            self.logger.error(f"Error analyzing feedback insights: {str(e)}")
            return {}
    
    async def _refine_themes_with_feedback(
        self, 
        current_themes: List[Dict[str, Any]], 
        feedback_insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Refine professional themes based on feedback insights."""
        
        if not feedback_insights:
            return current_themes
        
        theme_adjustments = feedback_insights.get('theme_adjustments', {})
        
        # Start with current themes
        refined_themes = current_themes.copy()
        
        # Remove themes marked for removal
        themes_to_remove = theme_adjustments.get('remove', [])
        refined_themes = [
            theme for theme in refined_themes 
            if theme.get('theme_name') not in themes_to_remove
        ]
        
        # Add new themes
        themes_to_add = theme_adjustments.get('add', [])
        for theme_name in themes_to_add:
            refined_themes.append({
                'theme_name': theme_name,
                'keywords': [],
                'confidence': 0.8,  # High confidence for user-specified themes
                'evidence': ['User feedback']
            })
        
        # Emphasize themes
        themes_to_emphasize = theme_adjustments.get('emphasize', [])
        for theme in refined_themes:
            if theme.get('theme_name') in themes_to_emphasize:
                theme['confidence'] = min(1.0, theme.get('confidence', 0.0) + 0.2)
        
        return refined_themes
    
    async def _refine_voice_with_feedback(
        self, 
        current_voice: Dict[str, Any], 
        feedback_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refine voice characteristics based on feedback insights."""
        
        if not feedback_insights:
            return current_voice
        
        voice_adjustments = feedback_insights.get('voice_adjustments', {})
        
        # Update voice with adjustments
        refined_voice = current_voice.copy()
        refined_voice.update(voice_adjustments)
        
        # Increase confidence for adjusted elements
        refined_voice['confidence'] = 0.9
        refined_voice['user_refined'] = True
        
        return refined_voice