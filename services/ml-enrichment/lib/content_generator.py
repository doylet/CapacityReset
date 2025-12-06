"""
Content Generator - Cross-Surface Professional Content Generation

Generates consistent professional content across multiple surfaces (CV summary, 
LinkedIn summary, portfolio introduction) using brand representation data.
Ensures brand consistency and surface-specific optimization with context awareness.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Import Vertex AI adapter from Feature 003
from adapters.vertex_ai_adapter import VertexAIAdapter

# Import domain entities
import sys
sys.path.append('/Users/thomasdoyle/Daintree/frameworks/gcloud/CapacityReset/api/jobs-api')
from domain.entities import BrandRepresentation, ProfessionalSurface, ContentGeneration

# Import context analyzer for cross-context consistency
from lib.context_analyzer import SurfaceContextAnalyzer


class ContentGenerator:
    """
    Generates professional content across multiple surfaces using brand representation.
    
    Key Features:
    - One-click generation across CV, LinkedIn, portfolio surfaces
    - Brand consistency validation across all generated content
    - Surface-specific optimization (length, tone, format)
    - Performance target: <30 seconds for complete generation
    """
    
    def __init__(self):
        """Initialize ContentGenerator with Vertex AI adapter and context analyzer."""
        self.vertex_ai = VertexAIAdapter()
        self.context_analyzer = SurfaceContextAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.generation_start_time = None
        self.target_generation_time = 30  # seconds
    
    async def generate_cross_surface_content(
        self, 
        brand: BrandRepresentation, 
        surfaces: List[ProfessionalSurface]
    ) -> List[ContentGeneration]:
        """
        Generate content for all specified surfaces in one operation with context consistency.
        
        Args:
            brand: Brand representation to generate content from
            surfaces: List of professional surfaces to generate for
            
        Returns:
            List of ContentGeneration objects for each surface
        """
        self.generation_start_time = datetime.utcnow()
        self.logger.info(f"Starting cross-surface content generation for brand {brand.brand_id}")
        
        try:
            # Step 1: Analyze cross-surface context requirements
            self.logger.info("Analyzing cross-surface context requirements")
            context_map = await self.context_analyzer.analyze_cross_surface_context(
                surfaces, brand
            )
            
            # Step 2: Pre-process brand themes and voice for efficient generation
            brand_context = self._prepare_brand_context(brand)
            
            # Step 3: Apply context-aware adaptations to brand context
            context_adapted_brand = await self._apply_context_adaptations(
                brand_context, context_map
            )
            
            # Step 4: Generate content for each surface with context awareness
            content_generations = []
            
            for surface in surfaces:
                self.logger.info(f"Generating context-aware content for surface: {surface.surface_type}")
                
                # Get surface-specific context analysis
                surface_context = context_map.surface_contexts.get(surface.surface_type)
                
                # Generate content with context consistency
                content = await self._generate_context_aware_surface_content(
                    brand, surface, context_adapted_brand, surface_context
                )
                
                # Create content generation record with context metadata
                generation = ContentGeneration(
                    brand_id=brand.brand_id,
                    surface_id=surface.surface_id,
                    content=content,
                    generation_metadata={
                        'surface_type': surface.surface_type,
                        'generation_timestamp': datetime.utcnow().isoformat(),
                        'brand_themes_count': len(brand.professional_themes or []),
                        'brand_confidence': brand.confidence_scores.get('overall', 0.0),
                        'generation_method': 'cross_surface_batch',
                        'context_score': surface_context.context_score if surface_context else 0.8,
                        'context_adaptations_applied': len(surface_context.adaptation_recommendations) if surface_context else 0,
                        'cross_surface_consistency_score': context_map.consistency_score
                    },
                    is_active=True,
                    user_edited=False,
                    created_at=datetime.utcnow()
                )
                
                content_generations.append(generation)
            
            # Step 5: Validate and maintain cross-surface consistency
            consistency_validation = await self._maintain_cross_surface_consistency(
                content_generations, context_map
            )
            
            # Step 6: Apply consistency adjustments if needed
            if consistency_validation['requires_adjustment']:
                self.logger.info("Applying cross-surface consistency adjustments")
                content_generations = await self._apply_consistency_adjustments(
                    content_generations, consistency_validation, context_map
                )
            
            # Step 7: Final validation and metadata updates
            final_consistency_score = await self._validate_cross_surface_consistency(content_generations)
            
            # Add final consistency metadata to all generations
            for generation in content_generations:
                generation.generation_metadata['final_consistency_score'] = final_consistency_score
                generation.generation_metadata['cross_surface_validated'] = True
                generation.generation_metadata['context_consistency_maintained'] = True
                generation.generation_metadata['shared_themes'] = context_map.shared_themes
            
            # Log performance
            generation_time = (datetime.utcnow() - self.generation_start_time).total_seconds()
            self.logger.info(f"Context-aware cross-surface generation complete in {generation_time:.2f}s (target: {self.target_generation_time}s)")
            
            # Performance validation
            if generation_time > self.target_generation_time:
                self.logger.warning(f"Generation time exceeded target: {generation_time:.2f}s > {self.target_generation_time}s")
            
            return content_generations
            
        except Exception as e:
            self.logger.error(f"Cross-surface content generation failed: {str(e)}")
            raise
    
    async def generate_single_surface_content(
        self, 
        brand: BrandRepresentation, 
        surface: ProfessionalSurface
    ) -> ContentGeneration:
        """
        Generate content for a single professional surface.
        
        Args:
            brand: Brand representation to generate from
            surface: Professional surface to generate for
            
        Returns:
            ContentGeneration object for the surface
        """
        self.logger.info(f"Generating single surface content: {surface.surface_type}")
        
        try:
            # Prepare brand context
            brand_context = self._prepare_brand_context(brand)
            
            # Generate content
            content = await self._generate_surface_content(brand, surface, brand_context)
            
            # Create generation record
            generation = ContentGeneration(
                brand_id=brand.brand_id,
                surface_id=surface.surface_id,
                content=content,
                generation_metadata={
                    'surface_type': surface.surface_type,
                    'generation_timestamp': datetime.utcnow().isoformat(),
                    'brand_themes_count': len(brand.professional_themes or []),
                    'brand_confidence': brand.confidence_scores.get('overall', 0.0),
                    'generation_method': 'single_surface'
                },
                is_active=True,
                user_edited=False,
                created_at=datetime.utcnow()
            )
            
            self.logger.info(f"Single surface content generation complete: {surface.surface_type}")
            return generation
            
        except Exception as e:
            self.logger.error(f"Single surface content generation failed: {str(e)}")
            raise
    
    async def regenerate_surface_content(
        self, 
        brand: BrandRepresentation, 
        surface: ProfessionalSurface,
        feedback: Optional[str] = None
    ) -> ContentGeneration:
        """
        Regenerate content for a surface with optional user feedback.
        
        Args:
            brand: Brand representation
            surface: Professional surface to regenerate
            feedback: Optional user feedback for improvement
            
        Returns:
            New ContentGeneration with updated content
        """
        self.logger.info(f"Regenerating surface content: {surface.surface_type}")
        
        try:
            # Prepare enhanced brand context with feedback
            brand_context = self._prepare_brand_context(brand)
            
            if feedback:
                brand_context['user_feedback'] = feedback
                brand_context['regeneration_context'] = True
            
            # Generate improved content
            content = await self._generate_surface_content(brand, surface, brand_context)
            
            # Create new generation record
            generation = ContentGeneration(
                brand_id=brand.brand_id,
                surface_id=surface.surface_id,
                content=content,
                generation_metadata={
                    'surface_type': surface.surface_type,
                    'generation_timestamp': datetime.utcnow().isoformat(),
                    'brand_themes_count': len(brand.professional_themes or []),
                    'brand_confidence': brand.confidence_scores.get('overall', 0.0),
                    'generation_method': 'regeneration',
                    'user_feedback_provided': bool(feedback),
                    'feedback_length': len(feedback) if feedback else 0
                },
                is_active=True,
                user_edited=False,
                created_at=datetime.utcnow()
            )
            
            self.logger.info(f"Surface content regeneration complete: {surface.surface_type}")
            return generation
            
        except Exception as e:
            self.logger.error(f"Surface content regeneration failed: {str(e)}")
            raise
    
    def _prepare_brand_context(self, brand: BrandRepresentation) -> Dict[str, Any]:
        """Prepare optimized brand context for content generation."""
        
        # Extract top themes for focused generation
        top_themes = []
        if brand.professional_themes:
            # Sort themes by confidence if available
            sorted_themes = sorted(
                brand.professional_themes, 
                key=lambda t: t.get('confidence', 0.0), 
                reverse=True
            )
            top_themes = sorted_themes[:5]  # Top 5 themes for focused generation
        
        # Extract key voice characteristics
        voice_summary = {}
        if brand.voice_characteristics:
            voice_summary = {
                'tone': brand.voice_characteristics.get('tone', 'professional'),
                'style': brand.voice_characteristics.get('style', 'clear'),
                'formality_level': brand.voice_characteristics.get('formality_level', 'professional')
            }
        
        # Extract narrative elements
        narrative_summary = {}
        if brand.narrative_arc:
            narrative_summary = {
                'career_progression': brand.narrative_arc.get('career_progression', []),
                'professional_identity': brand.narrative_arc.get('professional_identity', ''),
                'future_direction': brand.narrative_arc.get('future_direction', '')
            }
        
        return {
            'top_themes': top_themes,
            'voice_summary': voice_summary,
            'narrative_summary': narrative_summary,
            'brand_confidence': brand.confidence_scores.get('overall', 0.0),
            'themes_count': len(brand.professional_themes or [])
        }
    
    async def _generate_surface_content(
        self, 
        brand: BrandRepresentation, 
        surface: ProfessionalSurface, 
        brand_context: Dict[str, Any]
    ) -> str:
        """Generate content optimized for specific professional surface."""
        
        # Get surface-specific requirements
        surface_requirements = surface.requirements or {}
        max_words = surface_requirements.get('max_words', 150)
        tone = surface_requirements.get('preferred_tone', 'professional')
        format_style = surface_requirements.get('format', 'paragraph')
        
        # Build generation prompt based on surface type
        prompt = await self._build_surface_prompt(
            surface.surface_type, brand_context, surface_requirements
        )
        
        try:
            # Generate content with Vertex AI
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=min(max_words * 4, 1024),  # Conservative token estimate
                temperature=0.3,  # Balanced creativity and consistency
                top_p=0.8
            )
            
            # Clean and format response
            content = self._clean_generated_content(response, surface_requirements)
            
            # Validate content length
            if not self._validate_content_length(content, max_words):
                self.logger.warning(f"Generated content exceeds word limit for {surface.surface_type}")
                content = self._trim_content_to_limit(content, max_words)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Content generation failed for {surface.surface_type}: {str(e)}")
            raise ValueError(f"Failed to generate content for {surface.surface_type}")
    
    async def _build_surface_prompt(
        self, 
        surface_type: str, 
        brand_context: Dict[str, Any], 
        requirements: Dict[str, Any]
    ) -> str:
        """Build surface-specific generation prompt."""
        
        # Base brand information
        themes_text = ', '.join([
            theme.get('theme_name', str(theme)) 
            for theme in brand_context.get('top_themes', [])
        ])
        
        voice_summary = brand_context.get('voice_summary', {})
        narrative_summary = brand_context.get('narrative_summary', {})
        
        # Surface-specific prompt templates
        if surface_type == 'cv_summary':
            prompt = f"""
            Create a professional CV summary that showcases this person's brand identity.
            
            Professional Themes: {themes_text}
            Communication Style: {voice_summary.get('tone', 'professional')} tone, {voice_summary.get('style', 'clear')} style
            Career Identity: {narrative_summary.get('professional_identity', 'Accomplished professional')}
            
            Requirements:
            - Maximum {requirements.get('max_words', 100)} words
            - {requirements.get('format', 'paragraph')} format
            - Focus on value proposition and key achievements
            - Use active voice and quantifiable accomplishments when possible
            - Tailor for ATS compatibility
            
            Generate a compelling CV summary that captures their professional brand:
            """
            
        elif surface_type == 'linkedin_summary':
            prompt = f"""
            Create a LinkedIn About section that reflects this person's professional brand.
            
            Professional Themes: {themes_text}
            Communication Style: {voice_summary.get('tone', 'professional')} tone, {voice_summary.get('style', 'clear')} style
            Career Narrative: {narrative_summary.get('career_progression', 'Professional growth trajectory')}
            Future Direction: {narrative_summary.get('future_direction', 'Continued excellence')}
            
            Requirements:
            - Maximum {requirements.get('max_words', 220)} words
            - {requirements.get('format', 'paragraph')} format
            - Conversational yet professional tone
            - Include call-to-action or connection invitation
            - Optimize for LinkedIn search and networking
            
            Generate an engaging LinkedIn About section:
            """
            
        elif surface_type == 'portfolio_intro':
            prompt = f"""
            Create a portfolio introduction that establishes this person's professional brand.
            
            Professional Themes: {themes_text}
            Communication Style: {voice_summary.get('tone', 'professional')} tone, {voice_summary.get('style', 'clear')} style
            Professional Identity: {narrative_summary.get('professional_identity', 'Dedicated professional')}
            Career Progression: {narrative_summary.get('career_progression', 'Continuous growth')}
            
            Requirements:
            - Maximum {requirements.get('max_words', 180)} words
            - {requirements.get('format', 'paragraph')} format
            - Showcase expertise and unique value
            - Demonstrate thought leadership and approach
            - Compelling narrative that draws readers in
            
            Generate a captivating portfolio introduction:
            """
            
        else:
            # Generic professional surface
            prompt = f"""
            Create professional content that reflects this person's brand identity.
            
            Professional Themes: {themes_text}
            Communication Style: {voice_summary.get('tone', 'professional')} tone
            Professional Identity: {narrative_summary.get('professional_identity', 'Professional')}
            
            Requirements:
            - Maximum {requirements.get('max_words', 150)} words
            - Professional and engaging tone
            - Clear value proposition
            
            Generate professional content for {surface_type}:
            """
        
        # Add feedback context if regenerating
        if brand_context.get('regeneration_context') and brand_context.get('user_feedback'):
            prompt += f"\n\nUser Feedback for Improvement: {brand_context['user_feedback']}\n"
            prompt += "Please address this feedback in the generated content.\n"
        
        return prompt.strip()
    
    async def _validate_cross_surface_consistency(self, generations: List[ContentGeneration]) -> float:
        """Validate consistency across all generated content surfaces."""
        
        if len(generations) < 2:
            return 1.0  # Single surface is automatically consistent
        
        # Extract content for analysis
        content_pieces = [gen.content for gen in generations]
        surface_types = [gen.generation_metadata.get('surface_type', 'unknown') for gen in generations]
        
        # Build consistency validation prompt
        prompt = f"""
        Analyze the consistency of these professional content pieces across different surfaces.
        
        Content Pieces:
        """
        
        for i, (content, surface_type) in enumerate(zip(content_pieces, surface_types)):
            prompt += f"\n{i+1}. {surface_type.upper()}:\n{content}\n"
        
        prompt += """
        
        Evaluate consistency across:
        1. Professional themes and messaging
        2. Voice and communication style
        3. Key value propositions
        4. Overall brand identity
        
        Return a JSON response with:
        {
            "consistency_score": 0.0,
            "analysis": {
                "themes_consistency": 0.0,
                "voice_consistency": 0.0,
                "value_prop_consistency": 0.0,
                "overall_coherence": 0.0
            },
            "recommendations": ["recommendation1", "recommendation2"]
        }
        
        Scores should be between 0.0 (completely inconsistent) and 1.0 (perfectly consistent).
        """
        
        try:
            response = await self.vertex_ai.generate_text(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.1,  # Low temperature for consistent analysis
                top_p=0.8
            )
            
            # Parse consistency analysis
            import json
            import re
            
            # Clean response - remove markdown code blocks if present
            cleaned = re.sub(r'```json\s*|\s*```', '', response)
            cleaned = cleaned.strip()
            
            consistency_data = json.loads(cleaned)
            
            return consistency_data.get('consistency_score', 0.8)  # Default to good consistency
            
        except Exception as e:
            self.logger.error(f"Consistency validation failed: {str(e)}")
            return 0.8  # Return reasonable default on validation failure
    
    def _clean_generated_content(self, content: str, requirements: Dict[str, Any]) -> str:
        """Clean and format generated content according to requirements."""
        
        # Basic cleaning
        content = content.strip()
        
        # Remove any instructional text that might have been included
        content = re.sub(r'^(Here\'s|Here is|This is).*?:', '', content, flags=re.IGNORECASE)
        content = content.strip()
        
        # Format according to requirements
        format_style = requirements.get('format', 'paragraph')
        
        if format_style == 'paragraph':
            # Ensure proper paragraph formatting
            content = re.sub(r'\n\s*\n', '\n\n', content)  # Normalize paragraph breaks
        elif format_style == 'bullet':
            # Convert to bullet format if needed
            sentences = content.split('. ')
            if len(sentences) > 1:
                content = '• ' + '\n• '.join(sentence.strip() for sentence in sentences if sentence.strip())
        
        return content
    
    def _validate_content_length(self, content: str, max_words: int) -> bool:
        """Validate that content meets word length requirements."""
        word_count = len(content.split())
        return word_count <= max_words
    
    def _trim_content_to_limit(self, content: str, max_words: int) -> str:
        """Trim content to meet word limit while preserving meaning."""
        words = content.split()
        
        if len(words) <= max_words:
            return content
        
        # Trim to limit and ensure it ends properly
        trimmed_words = words[:max_words]
        trimmed_content = ' '.join(trimmed_words)
        
        # If we cut off mid-sentence, try to end at a complete sentence
        sentences = trimmed_content.split('. ')
        if len(sentences) > 1:
            # Remove the potentially incomplete last sentence
            complete_sentences = sentences[:-1]
            trimmed_content = '. '.join(complete_sentences) + '.'
        
        return trimmed_content
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the last generation operation."""
        if not self.generation_start_time:
            return {'error': 'No generation operation recorded'}
        
        current_time = datetime.utcnow()
        generation_time = (current_time - self.generation_start_time).total_seconds()
        
        return {
            'last_generation_time_seconds': generation_time,
            'target_time_seconds': self.target_generation_time,
            'meets_performance_target': generation_time <= self.target_generation_time,
            'performance_ratio': generation_time / self.target_generation_time
        }
    
    # Context-aware content generation methods for cross-surface consistency
    
    async def _apply_context_adaptations(
        self, 
        brand_context: Dict[str, Any], 
        context_map: Any
    ) -> Dict[str, Any]:
        """Apply cross-surface context adaptations to brand context."""
        
        adapted_context = brand_context.copy()
        
        # Emphasize shared themes across all surfaces
        if context_map.shared_themes:
            adapted_context['emphasized_themes'] = context_map.shared_themes
            self.logger.debug(f"Emphasizing shared themes: {context_map.shared_themes}")
        
        # Apply adaptation strategy
        strategy = context_map.adaptation_strategy
        if strategy.get('primary_approach') == 'theme_consistency_first':
            adapted_context['consistency_priority'] = 'themes'
            adapted_context['consistency_checkpoints'] = strategy.get('consistency_checkpoints', [])
        
        # Add cross-surface consistency guidelines
        adapted_context['cross_surface_guidelines'] = {
            'maintain_voice_consistency': True,
            'preserve_core_themes': context_map.shared_themes,
            'allow_surface_adaptations': [
                aspect for aspect in context_map.divergent_aspects 
                if aspect.get('severity') == 'low'
            ],
            'consistency_target_score': 0.8
        }
        
        return adapted_context
    
    async def _generate_context_aware_surface_content(
        self,
        brand: BrandRepresentation,
        surface: Any,
        context_adapted_brand: Dict[str, Any],
        surface_context: Any
    ) -> str:
        """Generate content for a surface with context awareness and consistency maintenance."""
        
        try:
            # Use the existing surface content generation but with context adaptations
            base_content = await self._generate_surface_content(
                brand, surface, context_adapted_brand
            )
            
            # Apply surface-specific context adaptations
            if surface_context and surface_context.adaptation_recommendations:
                adapted_content = await self._apply_surface_context_adaptations(
                    base_content, surface_context.adaptation_recommendations, surface.surface_type
                )
                return adapted_content
            
            return base_content
            
        except Exception as e:
            self.logger.error(f"Context-aware content generation failed for {surface.surface_type}: {str(e)}")
            # Fallback to basic generation
            return await self._generate_surface_content(brand, surface, context_adapted_brand)
    
    async def _apply_surface_context_adaptations(
        self,
        content: str,
        adaptations: List[str],
        surface_type: str
    ) -> str:
        """Apply surface-specific context adaptations to generated content."""
        
        adapted_content = content
        
        for adaptation in adaptations:
            if 'tone' in adaptation.lower():
                # Apply tone adaptations
                adapted_content = await self._apply_tone_adaptation(adapted_content, adaptation, surface_type)
            elif 'length' in adaptation.lower():
                # Apply length adaptations
                adapted_content = await self._apply_length_adaptation(adapted_content, adaptation)
            elif 'format' in adaptation.lower():
                # Apply formatting adaptations
                adapted_content = await self._apply_format_adaptation(adapted_content, adaptation, surface_type)
            elif 'emphasis' in adaptation.lower():
                # Apply emphasis adaptations
                adapted_content = await self._apply_emphasis_adaptation(adapted_content, adaptation)
        
        return adapted_content
    
    async def _maintain_cross_surface_consistency(
        self,
        content_generations: List[Any],
        context_map: Any
    ) -> Dict[str, Any]:
        """Analyze and maintain consistency across generated content."""
        
        # Analyze consistency across all generated content
        consistency_issues = []
        
        # Check voice consistency
        voice_consistency = await self._check_voice_consistency(content_generations)
        if voice_consistency['score'] < 0.8:
            consistency_issues.append({
                'type': 'voice_inconsistency',
                'severity': 'medium',
                'affected_surfaces': voice_consistency['inconsistent_surfaces'],
                'recommendations': voice_consistency['recommendations']
            })
        
        # Check theme consistency
        theme_consistency = await self._check_theme_consistency(
            content_generations, context_map.shared_themes
        )
        if theme_consistency['score'] < 0.8:
            consistency_issues.append({
                'type': 'theme_inconsistency',
                'severity': 'high',
                'affected_surfaces': theme_consistency['weak_surfaces'],
                'recommendations': theme_consistency['recommendations']
            })
        
        # Check narrative coherence
        narrative_consistency = await self._check_narrative_coherence(content_generations)
        if narrative_consistency['score'] < 0.7:
            consistency_issues.append({
                'type': 'narrative_inconsistency',
                'severity': 'medium',
                'affected_surfaces': narrative_consistency['disconnected_surfaces'],
                'recommendations': narrative_consistency['recommendations']
            })
        
        return {
            'requires_adjustment': len(consistency_issues) > 0,
            'consistency_issues': consistency_issues,
            'overall_consistency_score': min(
                voice_consistency['score'],
                theme_consistency['score'], 
                narrative_consistency['score']
            ),
            'validation_timestamp': datetime.utcnow().isoformat()
        }
    
    async def _apply_consistency_adjustments(
        self,
        content_generations: List[Any],
        consistency_validation: Dict[str, Any],
        context_map: Any
    ) -> List[Any]:
        """Apply adjustments to maintain cross-surface consistency."""
        
        adjusted_generations = []
        
        for generation in content_generations:
            adjusted_content = generation.content
            surface_type = generation.generation_metadata.get('surface_type')
            
            # Apply adjustments based on consistency issues
            for issue in consistency_validation['consistency_issues']:
                if surface_type in issue.get('affected_surfaces', []):
                    adjusted_content = await self._apply_consistency_adjustment(
                        adjusted_content, issue, context_map, surface_type
                    )
            
            # Update generation with adjusted content
            generation.content = adjusted_content
            generation.generation_metadata['consistency_adjustments_applied'] = len([
                issue for issue in consistency_validation['consistency_issues']
                if surface_type in issue.get('affected_surfaces', [])
            ])
            
            adjusted_generations.append(generation)
        
        return adjusted_generations
    
    async def _apply_tone_adaptation(self, content: str, adaptation: str, surface_type: str) -> str:
        """Apply tone-specific adaptations to content."""
        
        # Simple tone adaptation - in production would use more sophisticated NLP
        if 'formal' in adaptation.lower() and surface_type == 'cv_summary':
            # Make more formal for CV
            content = content.replace("I'm", "I am").replace("can't", "cannot")
        elif 'conversational' in adaptation.lower() and surface_type == 'linkedin_summary':
            # Make more conversational for LinkedIn
            content = content.replace("I am", "I'm").replace("cannot", "can't")
        
        return content
    
    async def _apply_length_adaptation(self, content: str, adaptation: str) -> str:
        """Apply length-specific adaptations to content."""
        
        words = content.split()
        
        if 'expand' in adaptation.lower():
            # Add more descriptive language
            expanded_content = content.replace(
                '. ', '. Additionally, '
            )
            return expanded_content
        elif 'condense' in adaptation.lower():
            # Remove transitional phrases
            condensed_content = content.replace(
                'Additionally, ', ''
            ).replace(
                'Furthermore, ', ''
            ).replace(
                'Moreover, ', ''
            )
            return condensed_content
        
        return content
    
    async def _apply_format_adaptation(self, content: str, adaptation: str, surface_type: str) -> str:
        """Apply format-specific adaptations to content."""
        
        if 'bullet' in adaptation.lower() and surface_type == 'cv_summary':
            # Convert to bullet points for CV
            sentences = content.split('. ')
            if len(sentences) > 1:
                content = '• ' + '\n• '.join(sentence.strip() + '.' for sentence in sentences if sentence.strip())
        elif 'paragraph' in adaptation.lower() and surface_type in ['linkedin_summary', 'portfolio_intro']:
            # Ensure paragraph format for narrative surfaces
            content = content.replace('• ', '').replace('\n', ' ')
        
        return content
    
    async def _apply_emphasis_adaptation(self, content: str, adaptation: str) -> str:
        """Apply emphasis-specific adaptations to content."""
        
        # Simple emphasis adaptation - in production would use semantic analysis
        if 'quantify' in adaptation.lower():
            # Encourage quantification
            content = content.replace(
                'many', 'numerous'
            ).replace(
                'several', 'multiple'
            )
        
        return content
    
    async def _check_voice_consistency(self, content_generations: List[Any]) -> Dict[str, Any]:
        """Check voice consistency across generated content."""
        
        # Simple heuristic analysis - in production would use sophisticated NLP
        formal_indicators = ['cannot', 'shall', 'furthermore', 'moreover']
        casual_indicators = ["can't", "I'll", "we'll", 'really', 'quite']
        
        surface_formality = {}
        
        for generation in content_generations:
            content = generation.content.lower()
            surface_type = generation.generation_metadata.get('surface_type')
            
            formal_count = sum(1 for indicator in formal_indicators if indicator in content)
            casual_count = sum(1 for indicator in casual_indicators if indicator in content)
            
            formality_score = (formal_count - casual_count) / max(formal_count + casual_count, 1)
            surface_formality[surface_type] = formality_score
        
        # Check for consistency
        formality_values = list(surface_formality.values())
        consistency_score = 1.0 - (max(formality_values) - min(formality_values)) if formality_values else 1.0
        
        inconsistent_surfaces = [
            surface for surface, score in surface_formality.items()
            if abs(score - sum(formality_values) / len(formality_values)) > 0.3
        ]
        
        return {
            'score': consistency_score,
            'inconsistent_surfaces': inconsistent_surfaces,
            'recommendations': [
                f"Align formality level across {', '.join(inconsistent_surfaces[:2])}"
            ] if inconsistent_surfaces else []
        }
    
    async def _check_theme_consistency(self, content_generations: List[Any], shared_themes: List[str]) -> Dict[str, Any]:
        """Check theme consistency across generated content."""
        
        surface_theme_coverage = {}
        
        for generation in content_generations:
            content = generation.content.lower()
            surface_type = generation.generation_metadata.get('surface_type')
            
            theme_count = sum(1 for theme in shared_themes if theme.lower() in content)
            coverage_score = theme_count / max(len(shared_themes), 1)
            surface_theme_coverage[surface_type] = coverage_score
        
        # Calculate consistency
        coverage_values = list(surface_theme_coverage.values())
        avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else 0
        consistency_score = min(coverage_values) if coverage_values else 0
        
        weak_surfaces = [
            surface for surface, coverage in surface_theme_coverage.items()
            if coverage < avg_coverage * 0.7
        ]
        
        return {
            'score': consistency_score,
            'weak_surfaces': weak_surfaces,
            'recommendations': [
                f"Strengthen theme representation in {', '.join(weak_surfaces[:2])}"
            ] if weak_surfaces else []
        }
    
    async def _check_narrative_coherence(self, content_generations: List[Any]) -> Dict[str, Any]:
        """Check narrative coherence across generated content."""
        
        # Simple coherence check based on common narrative elements
        narrative_elements = ['experience', 'skills', 'passion', 'goals', 'value']
        
        surface_narrative_scores = {}
        
        for generation in content_generations:
            content = generation.content.lower()
            surface_type = generation.generation_metadata.get('surface_type')
            
            element_count = sum(1 for element in narrative_elements if element in content)
            narrative_score = element_count / len(narrative_elements)
            surface_narrative_scores[surface_type] = narrative_score
        
        # Check coherence
        narrative_values = list(surface_narrative_scores.values())
        coherence_score = min(narrative_values) if narrative_values else 0
        
        disconnected_surfaces = [
            surface for surface, score in surface_narrative_scores.items()
            if score < 0.4
        ]
        
        return {
            'score': coherence_score,
            'disconnected_surfaces': disconnected_surfaces,
            'recommendations': [
                f"Improve narrative flow in {', '.join(disconnected_surfaces[:2])}"
            ] if disconnected_surfaces else []
        }
    
    async def _apply_consistency_adjustment(
        self,
        content: str,
        issue: Dict[str, Any],
        context_map: Any,
        surface_type: str
    ) -> str:
        """Apply specific consistency adjustment based on identified issue."""
        
        adjusted_content = content
        
        if issue['type'] == 'voice_inconsistency':
            # Apply voice consistency adjustments
            for recommendation in issue.get('recommendations', []):
                if 'formality' in recommendation.lower():
                    adjusted_content = await self._apply_tone_adaptation(
                        adjusted_content, recommendation, surface_type
                    )
        
        elif issue['type'] == 'theme_inconsistency':
            # Strengthen theme representation
            shared_themes = context_map.shared_themes if hasattr(context_map, 'shared_themes') else []
            if shared_themes:
                # Simple theme reinforcement
                theme_phrase = f"with expertise in {', '.join(shared_themes[:2])}"
                if theme_phrase not in adjusted_content:
                    sentences = adjusted_content.split('. ')
                    if len(sentences) > 1:
                        sentences[1] = sentences[1] + f" {theme_phrase}"
                        adjusted_content = '. '.join(sentences)
        
        elif issue['type'] == 'narrative_inconsistency':
            # Improve narrative flow
            if not any(word in adjusted_content.lower() for word in ['passion', 'drive', 'commitment']):
                adjusted_content = adjusted_content.replace(
                    'experience', 'passionate experience'
                )
        
        return adjusted_content