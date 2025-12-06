"""
Consistency Validator - Cross-Surface Brand Coherence Analysis

Validates that content generated across multiple professional surfaces maintains
consistent brand themes, voice, and messaging while respecting surface-specific
optimization requirements.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Import Vertex AI adapter for analysis
from adapters.vertex_ai_adapter import VertexAIAdapter

# Import domain entities
import sys
sys.path.append('/Users/thomasdoyle/Daintree/frameworks/gcloud/CapacityReset/api/jobs-api')
from domain.entities import ContentGeneration, BrandRepresentation


class ConsistencyAnalyzer:
    """
    Analyzes brand consistency across multiple content surfaces.
    
    Validates:
    - Theme coherence across surfaces
    - Voice and tone consistency
    - Key message alignment
    - Professional identity consistency
    - Value proposition coherence
    """
    
    def __init__(self):
        """Initialize consistency analyzer."""
        self.vertex_ai = VertexAIAdapter()
        self.logger = logging.getLogger(__name__)
        
        # Consistency thresholds
        self.consistency_thresholds = {
            'excellent': 0.9,
            'good': 0.8,
            'acceptable': 0.7,
            'needs_improvement': 0.6
        }
    
    async def validate_cross_surface_consistency(
        self,
        content_generations: List[ContentGeneration],
        brand_representation: BrandRepresentation
    ) -> Dict[str, Any]:
        """
        Comprehensive cross-surface consistency validation.
        
        Args:
            content_generations: List of generated content for different surfaces
            brand_representation: Original brand representation
            
        Returns:
            Detailed consistency analysis with scores and recommendations
        """
        self.logger.info(f"Validating consistency across {len(content_generations)} surfaces")
        
        try:
            # Extract content and surface information
            content_data = self._extract_content_data(content_generations)
            
            if len(content_data) < 2:
                return self._single_surface_result(content_data[0] if content_data else None)
            
            # Perform consistency analysis
            theme_analysis = await self._analyze_theme_consistency(content_data, brand_representation)
            voice_analysis = await self._analyze_voice_consistency(content_data, brand_representation)
            message_analysis = await self._analyze_message_consistency(content_data)
            identity_analysis = await self._analyze_identity_consistency(content_data, brand_representation)
            
            # Calculate overall consistency score
            overall_score = self._calculate_overall_score([
                theme_analysis['score'],
                voice_analysis['score'],
                message_analysis['score'],
                identity_analysis['score']
            ])
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                theme_analysis, voice_analysis, message_analysis, identity_analysis, overall_score
            )
            
            # Compile comprehensive results
            consistency_result = {
                'overall_score': overall_score,
                'consistency_level': self._get_consistency_level(overall_score),
                'analysis': {
                    'theme_consistency': theme_analysis,
                    'voice_consistency': voice_analysis,
                    'message_consistency': message_analysis,
                    'identity_consistency': identity_analysis
                },
                'surface_count': len(content_data),
                'validation_timestamp': datetime.utcnow().isoformat(),
                'recommendations': recommendations,
                'requires_revision': overall_score < self.consistency_thresholds['acceptable']
            }
            
            self.logger.info(f"Consistency validation complete. Overall score: {overall_score:.3f}")
            
            return consistency_result
            
        except Exception as e:
            self.logger.error(f"Consistency validation failed: {str(e)}")
            raise ValueError(f"Consistency validation error: {str(e)}")
    
    async def validate_single_surface_quality(
        self,
        content_generation: ContentGeneration,
        brand_representation: BrandRepresentation
    ) -> Dict[str, Any]:
        """
        Validate single surface content quality against brand representation.
        
        Args:
            content_generation: Single content generation to validate
            brand_representation: Brand representation for comparison
            
        Returns:
            Quality analysis with scores and improvement suggestions
        """
        self.logger.info(f"Validating single surface quality: {content_generation.surface_id}")
        
        try:
            # Brand alignment analysis
            alignment_score = await self._analyze_brand_alignment(content_generation, brand_representation)
            
            # Content quality analysis
            quality_score = await self._analyze_content_quality(content_generation)
            
            # Surface optimization analysis
            optimization_score = await self._analyze_surface_optimization(content_generation)
            
            overall_quality = (alignment_score + quality_score + optimization_score) / 3
            
            # Generate improvement suggestions
            suggestions = self._generate_quality_suggestions(
                alignment_score, quality_score, optimization_score, content_generation
            )
            
            quality_result = {
                'overall_quality': overall_quality,
                'quality_level': self._get_consistency_level(overall_quality),
                'analysis': {
                    'brand_alignment': alignment_score,
                    'content_quality': quality_score,
                    'surface_optimization': optimization_score
                },
                'surface_type': content_generation.generation_metadata.get('surface_type'),
                'validation_timestamp': datetime.utcnow().isoformat(),
                'suggestions': suggestions,
                'needs_improvement': overall_quality < self.consistency_thresholds['acceptable']
            }
            
            self.logger.info(f"Single surface validation complete. Quality score: {overall_quality:.3f}")
            
            return quality_result
            
        except Exception as e:
            self.logger.error(f"Single surface validation failed: {str(e)}")
            raise ValueError(f"Single surface validation error: {str(e)}")
    
    async def compare_content_versions(
        self,
        original_content: ContentGeneration,
        updated_content: ContentGeneration,
        brand_representation: BrandRepresentation
    ) -> Dict[str, Any]:
        """
        Compare two versions of content to assess improvement.
        
        Args:
            original_content: Original content generation
            updated_content: Updated/regenerated content
            brand_representation: Brand representation for context
            
        Returns:
            Comparison analysis with improvement assessment
        """
        self.logger.info("Comparing content versions for improvement assessment")
        
        try:
            # Validate both versions
            original_quality = await self.validate_single_surface_quality(original_content, brand_representation)
            updated_quality = await self.validate_single_surface_quality(updated_content, brand_representation)
            
            # Calculate improvement metrics
            improvement_score = updated_quality['overall_quality'] - original_quality['overall_quality']
            improvement_percentage = (improvement_score / max(original_quality['overall_quality'], 0.1)) * 100
            
            # Analyze specific improvements
            improvements = self._analyze_specific_improvements(original_quality, updated_quality)
            
            comparison_result = {
                'improvement_score': improvement_score,
                'improvement_percentage': improvement_percentage,
                'is_improvement': improvement_score > 0.05,  # Threshold for meaningful improvement
                'original_quality': original_quality['overall_quality'],
                'updated_quality': updated_quality['overall_quality'],
                'improvements': improvements,
                'recommendation': 'use_updated' if improvement_score > 0.05 else 'consider_original',
                'comparison_timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Content comparison complete. Improvement: {improvement_score:.3f}")
            
            return comparison_result
            
        except Exception as e:
            self.logger.error(f"Content version comparison failed: {str(e)}")
            raise ValueError(f"Content comparison error: {str(e)}")
    
    def _extract_content_data(self, content_generations: List[ContentGeneration]) -> List[Dict[str, Any]]:
        """Extract and structure content data for analysis."""
        
        content_data = []
        
        for generation in content_generations:
            surface_type = generation.generation_metadata.get('surface_type', 'unknown')
            
            content_data.append({
                'content': generation.content,
                'surface_type': surface_type,
                'generation_id': generation.generation_id,
                'word_count': len(generation.content.split()),
                'metadata': generation.generation_metadata or {}
            })
        
        return content_data
    
    async def _analyze_theme_consistency(
        self, 
        content_data: List[Dict[str, Any]], 
        brand_representation: BrandRepresentation
    ) -> Dict[str, Any]:
        """Analyze consistency of professional themes across surfaces."""
        
        # Extract expected themes from brand representation
        brand_themes = [
            theme.get('theme_name', str(theme)) 
            for theme in (brand_representation.professional_themes or [])
        ]
        
        if not brand_themes:
            return {'score': 0.8, 'analysis': 'No brand themes available for comparison', 'issues': []}
        
        # Build theme consistency prompt
        content_pieces = []
        for data in content_data:
            content_pieces.append(f"{data['surface_type'].upper()}: {data['content']}")
        
        prompt = f"""
        Analyze theme consistency across these professional content pieces.
        
        Expected Brand Themes: {', '.join(brand_themes)}
        
        Content Pieces:
        {chr(10).join(content_pieces)}
        
        Evaluate:
        1. How well each content piece reflects the expected brand themes
        2. Consistency of theme representation across all pieces
        3. Any missing or conflicting themes
        
        Return JSON:
        {{
            "theme_consistency_score": 0.0,
            "themes_analysis": {{
                "well_represented": ["theme1"],
                "missing_themes": ["theme2"],
                "conflicting_representations": ["theme3"]
            }},
            "surface_scores": {{"cv_summary": 0.0, "linkedin_summary": 0.0}},
            "recommendations": ["suggestion1", "suggestion2"]
        }}
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.1,
                top_p=0.8
            )
            
            analysis = self._parse_json_response(response)
            
            if analysis and 'theme_consistency_score' in analysis:
                return {
                    'score': analysis['theme_consistency_score'],
                    'analysis': analysis,
                    'issues': analysis.get('themes_analysis', {}).get('missing_themes', [])
                }
            else:
                return {'score': 0.7, 'analysis': 'Theme analysis incomplete', 'issues': []}
            
        except Exception as e:
            self.logger.error(f"Theme consistency analysis failed: {str(e)}")
            return {'score': 0.6, 'analysis': f'Analysis error: {str(e)}', 'issues': ['analysis_error']}
    
    async def _analyze_voice_consistency(
        self, 
        content_data: List[Dict[str, Any]], 
        brand_representation: BrandRepresentation
    ) -> Dict[str, Any]:
        """Analyze voice and tone consistency across surfaces."""
        
        # Extract voice characteristics from brand
        voice_characteristics = brand_representation.voice_characteristics or {}
        expected_tone = voice_characteristics.get('tone', 'professional')
        expected_style = voice_characteristics.get('style', 'clear')
        
        # Build voice consistency prompt
        content_pieces = []
        for data in content_data:
            content_pieces.append(f"{data['surface_type'].upper()}: {data['content']}")
        
        prompt = f"""
        Analyze voice and communication style consistency across these content pieces.
        
        Expected Voice Profile:
        - Tone: {expected_tone}
        - Style: {expected_style}
        - Formality: {voice_characteristics.get('formality_level', 'professional')}
        
        Content Pieces:
        {chr(10).join(content_pieces)}
        
        Evaluate:
        1. Consistency of communication tone across all pieces
        2. Alignment with expected voice characteristics
        3. Professional appropriateness for each surface
        
        Return JSON:
        {{
            "voice_consistency_score": 0.0,
            "voice_analysis": {{
                "tone_consistency": 0.0,
                "style_consistency": 0.0,
                "formality_alignment": 0.0
            }},
            "surface_voice_scores": {{"cv_summary": 0.0, "linkedin_summary": 0.0}},
            "voice_recommendations": ["suggestion1"]
        }}
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.1,
                top_p=0.8
            )
            
            analysis = self._parse_json_response(response)
            
            if analysis and 'voice_consistency_score' in analysis:
                return {
                    'score': analysis['voice_consistency_score'],
                    'analysis': analysis,
                    'issues': [issue for issue in analysis.get('voice_recommendations', []) if 'improve' in issue.lower()]
                }
            else:
                return {'score': 0.7, 'analysis': 'Voice analysis incomplete', 'issues': []}
            
        except Exception as e:
            self.logger.error(f"Voice consistency analysis failed: {str(e)}")
            return {'score': 0.6, 'analysis': f'Analysis error: {str(e)}', 'issues': ['analysis_error']}
    
    async def _analyze_message_consistency(self, content_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze key message and value proposition consistency."""
        
        content_pieces = []
        for data in content_data:
            content_pieces.append(f"{data['surface_type'].upper()}: {data['content']}")
        
        prompt = f"""
        Analyze key message and value proposition consistency across these content pieces.
        
        Content Pieces:
        {chr(10).join(content_pieces)}
        
        Evaluate:
        1. Consistency of core value propositions across all pieces
        2. Alignment of key messages and positioning
        3. Professional identity coherence
        
        Return JSON:
        {{
            "message_consistency_score": 0.0,
            "message_analysis": {{
                "value_prop_consistency": 0.0,
                "positioning_alignment": 0.0,
                "key_message_coherence": 0.0
            }},
            "identified_messages": ["message1", "message2"],
            "message_recommendations": ["suggestion1"]
        }}
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.1,
                top_p=0.8
            )
            
            analysis = self._parse_json_response(response)
            
            if analysis and 'message_consistency_score' in analysis:
                return {
                    'score': analysis['message_consistency_score'],
                    'analysis': analysis,
                    'issues': [issue for issue in analysis.get('message_recommendations', []) if 'improve' in issue.lower()]
                }
            else:
                return {'score': 0.7, 'analysis': 'Message analysis incomplete', 'issues': []}
            
        except Exception as e:
            self.logger.error(f"Message consistency analysis failed: {str(e)}")
            return {'score': 0.6, 'analysis': f'Analysis error: {str(e)}', 'issues': ['analysis_error']}
    
    async def _analyze_identity_consistency(
        self, 
        content_data: List[Dict[str, Any]], 
        brand_representation: BrandRepresentation
    ) -> Dict[str, Any]:
        """Analyze professional identity consistency."""
        
        professional_identity = brand_representation.narrative_arc.get('professional_identity', '') if brand_representation.narrative_arc else ''
        
        content_pieces = []
        for data in content_data:
            content_pieces.append(f"{data['surface_type'].upper()}: {data['content']}")
        
        prompt = f"""
        Analyze professional identity consistency across these content pieces.
        
        Expected Professional Identity: {professional_identity}
        
        Content Pieces:
        {chr(10).join(content_pieces)}
        
        Evaluate:
        1. Consistency of professional identity portrayal
        2. Alignment with expected identity characteristics
        3. Coherent professional persona across surfaces
        
        Return JSON:
        {{
            "identity_consistency_score": 0.0,
            "identity_analysis": {{
                "persona_consistency": 0.0,
                "identity_alignment": 0.0,
                "professional_coherence": 0.0
            }},
            "identity_recommendations": ["suggestion1"]
        }}
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.1,
                top_p=0.8
            )
            
            analysis = self._parse_json_response(response)
            
            if analysis and 'identity_consistency_score' in analysis:
                return {
                    'score': analysis['identity_consistency_score'],
                    'analysis': analysis,
                    'issues': [issue for issue in analysis.get('identity_recommendations', []) if 'improve' in issue.lower()]
                }
            else:
                return {'score': 0.7, 'analysis': 'Identity analysis incomplete', 'issues': []}
            
        except Exception as e:
            self.logger.error(f"Identity consistency analysis failed: {str(e)}")
            return {'score': 0.6, 'analysis': f'Analysis error: {str(e)}', 'issues': ['analysis_error']}
    
    async def _analyze_brand_alignment(
        self, 
        content_generation: ContentGeneration, 
        brand_representation: BrandRepresentation
    ) -> float:
        """Analyze how well single surface content aligns with brand."""
        
        themes = [theme.get('theme_name', str(theme)) for theme in (brand_representation.professional_themes or [])]
        voice = brand_representation.voice_characteristics or {}
        
        prompt = f"""
        Analyze how well this content aligns with the expected brand profile.
        
        Content: {content_generation.content}
        
        Expected Brand Profile:
        - Themes: {', '.join(themes)}
        - Tone: {voice.get('tone', 'professional')}
        - Style: {voice.get('style', 'clear')}
        
        Rate alignment from 0.0 to 1.0. Return only the numeric score.
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=50,
                temperature=0.1,
                top_p=0.8
            )
            
            # Extract numeric score
            score_match = re.search(r'(\d+\.?\d*)', response.strip())
            if score_match:
                score = float(score_match.group(1))
                return min(1.0, max(0.0, score))
            
            return 0.7  # Default score if parsing fails
            
        except Exception as e:
            self.logger.error(f"Brand alignment analysis failed: {str(e)}")
            return 0.6
    
    async def _analyze_content_quality(self, content_generation: ContentGeneration) -> float:
        """Analyze general content quality."""
        
        content = content_generation.content
        word_count = len(content.split())
        
        # Basic quality checks
        quality_score = 1.0
        
        # Check for appropriate length
        if word_count < 20:
            quality_score -= 0.3  # Too short
        elif word_count > 300:
            quality_score -= 0.2  # Potentially too long
        
        # Check for basic structure
        sentence_count = len([s for s in content.split('.') if s.strip()])
        if sentence_count < 2:
            quality_score -= 0.2  # Too few sentences
        
        # Check for professional language
        if any(word in content.lower() for word in ['awesome', 'super', 'really cool']):
            quality_score -= 0.1  # Informal language
        
        return max(0.0, quality_score)
    
    async def _analyze_surface_optimization(self, content_generation: ContentGeneration) -> float:
        """Analyze optimization for specific surface type."""
        
        surface_type = content_generation.generation_metadata.get('surface_type', 'unknown')
        content = content_generation.content
        word_count = len(content.split())
        
        # Surface-specific optimization checks
        if surface_type == 'cv_summary':
            # Should be concise and achievement-focused
            if word_count <= 120 and any(word in content.lower() for word in ['achieved', 'led', 'delivered']):
                return 1.0
            return 0.8
            
        elif surface_type == 'linkedin_summary':
            # Should be conversational and engaging
            if word_count <= 250 and ('I' in content or 'my' in content):
                return 1.0
            return 0.8
            
        elif surface_type == 'portfolio_intro':
            # Should be sophisticated and expertise-focused
            if word_count <= 200 and any(word in content.lower() for word in ['expertise', 'experience', 'approach']):
                return 1.0
            return 0.8
        
        return 0.7  # Default for unknown surfaces
    
    def _calculate_overall_score(self, scores: List[float]) -> float:
        """Calculate weighted overall consistency score."""
        if not scores:
            return 0.0
        
        # Equal weighting for all aspects
        return sum(scores) / len(scores)
    
    def _get_consistency_level(self, score: float) -> str:
        """Get consistency level description from score."""
        if score >= self.consistency_thresholds['excellent']:
            return 'excellent'
        elif score >= self.consistency_thresholds['good']:
            return 'good'
        elif score >= self.consistency_thresholds['acceptable']:
            return 'acceptable'
        else:
            return 'needs_improvement'
    
    def _generate_recommendations(
        self, 
        theme_analysis: Dict[str, Any],
        voice_analysis: Dict[str, Any],
        message_analysis: Dict[str, Any],
        identity_analysis: Dict[str, Any],
        overall_score: float
    ) -> List[str]:
        """Generate actionable recommendations for improvement."""
        
        recommendations = []
        
        # Theme-based recommendations
        if theme_analysis['score'] < 0.7:
            recommendations.append("Strengthen theme consistency across all surfaces")
            if theme_analysis.get('issues'):
                recommendations.append(f"Address missing themes: {', '.join(theme_analysis['issues'])}")
        
        # Voice-based recommendations
        if voice_analysis['score'] < 0.7:
            recommendations.append("Improve voice and tone consistency across surfaces")
        
        # Message-based recommendations
        if message_analysis['score'] < 0.7:
            recommendations.append("Align key messages and value propositions more closely")
        
        # Identity-based recommendations
        if identity_analysis['score'] < 0.7:
            recommendations.append("Ensure consistent professional identity portrayal")
        
        # Overall recommendations
        if overall_score < self.consistency_thresholds['acceptable']:
            recommendations.append("Consider regenerating content with stronger brand focus")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _generate_quality_suggestions(
        self, 
        alignment_score: float,
        quality_score: float,
        optimization_score: float,
        content_generation: ContentGeneration
    ) -> List[str]:
        """Generate quality improvement suggestions."""
        
        suggestions = []
        
        if alignment_score < 0.7:
            suggestions.append("Better incorporate brand themes and voice characteristics")
        
        if quality_score < 0.7:
            suggestions.append("Improve overall content quality and structure")
        
        if optimization_score < 0.7:
            surface_type = content_generation.generation_metadata.get('surface_type', 'surface')
            suggestions.append(f"Optimize content specifically for {surface_type} requirements")
        
        return suggestions
    
    def _analyze_specific_improvements(
        self, 
        original_quality: Dict[str, Any], 
        updated_quality: Dict[str, Any]
    ) -> List[str]:
        """Analyze specific areas of improvement between versions."""
        
        improvements = []
        
        # Check each analysis component
        original_analysis = original_quality.get('analysis', {})
        updated_analysis = updated_quality.get('analysis', {})
        
        for aspect in ['brand_alignment', 'content_quality', 'surface_optimization']:
            original_score = original_analysis.get(aspect, 0)
            updated_score = updated_analysis.get(aspect, 0)
            
            if updated_score > original_score + 0.05:  # Meaningful improvement threshold
                improvements.append(f"Improved {aspect.replace('_', ' ')}")
        
        return improvements
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from Vertex AI."""
        try:
            import json
            # Clean response - remove markdown code blocks if present
            cleaned = re.sub(r'```json\s*|\s*```', '', response)
            cleaned = cleaned.strip()
            
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return None
    
    def _single_surface_result(self, content_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Return result for single surface (no cross-surface comparison possible)."""
        return {
            'overall_score': 1.0,  # Single surface is consistent with itself
            'consistency_level': 'excellent',
            'analysis': {
                'note': 'Single surface - no cross-surface comparison available'
            },
            'surface_count': 1 if content_data else 0,
            'validation_timestamp': datetime.utcnow().isoformat(),
            'recommendations': [],
            'requires_revision': False
        }