"""
Generation Templates - Professional Content Templates and Prompts

Provides standardized templates and prompts for consistent content generation
across different professional surfaces. Supports dynamic customization based
on brand characteristics and surface requirements.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import logging


class SurfaceType(Enum):
    """Enumeration of supported professional surface types."""
    CV_SUMMARY = "cv_summary"
    LINKEDIN_SUMMARY = "linkedin_summary"  
    PORTFOLIO_INTRO = "portfolio_intro"
    COVER_LETTER_INTRO = "cover_letter_intro"
    ELEVATOR_PITCH = "elevator_pitch"


class ToneStyle(Enum):
    """Enumeration of supported communication tones."""
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    CONFIDENT = "confident"
    APPROACHABLE = "approachable"
    ANALYTICAL = "analytical"
    INNOVATIVE = "innovative"


class GenerationTemplates:
    """
    Manages templates and prompts for professional content generation.
    
    Provides:
    - Surface-specific prompt templates
    - Dynamic content structure templates
    - Formatting and style guidelines
    - Consistency validation rules
    """
    
    def __init__(self):
        """Initialize templates with logging."""
        self.logger = logging.getLogger(__name__)
        
        # Core template configurations
        self.surface_configs = self._load_surface_configurations()
        self.prompt_templates = self._load_prompt_templates()
        self.formatting_rules = self._load_formatting_rules()
        self.consistency_rules = self._load_consistency_rules()
    
    def get_surface_prompt(
        self, 
        surface_type: str, 
        brand_context: Dict[str, Any],
        surface_requirements: Dict[str, Any] = None
    ) -> str:
        """
        Get optimized prompt for specific surface type and brand context.
        
        Args:
            surface_type: Type of professional surface
            brand_context: Brand themes, voice, narrative data
            surface_requirements: Surface-specific requirements (word count, format)
            
        Returns:
            Customized generation prompt
        """
        surface_requirements = surface_requirements or {}
        
        # Get base template for surface
        template = self.prompt_templates.get(surface_type)
        if not template:
            raise ValueError(f"No template available for surface type: {surface_type}")
        
        # Extract brand information
        themes = self._format_themes(brand_context.get('top_themes', []))
        voice = brand_context.get('voice_summary', {})
        narrative = brand_context.get('narrative_summary', {})
        
        # Get surface configuration
        config = self.surface_configs.get(surface_type, {})
        default_word_limit = config.get('default_word_limit', 150)
        default_tone = config.get('default_tone', 'professional')
        
        # Build customized prompt
        prompt = template['base_prompt'].format(
            themes=themes,
            tone=voice.get('tone', default_tone),
            style=voice.get('style', 'clear'),
            formality=voice.get('formality_level', 'professional'),
            professional_identity=narrative.get('professional_identity', 'Accomplished professional'),
            career_progression=self._format_career_progression(narrative.get('career_progression', [])),
            future_direction=narrative.get('future_direction', 'Continued excellence'),
            word_limit=surface_requirements.get('max_words', default_word_limit),
            format_style=surface_requirements.get('format', config.get('default_format', 'paragraph'))
        )
        
        # Add surface-specific guidelines
        if template.get('specific_guidelines'):
            prompt += "\n\n" + template['specific_guidelines']
        
        # Add contextual modifiers
        prompt += self._get_contextual_modifiers(surface_type, brand_context, surface_requirements)
        
        return prompt.strip()
    
    def get_formatting_rules(self, surface_type: str) -> Dict[str, Any]:
        """Get formatting rules for specific surface type."""
        return self.formatting_rules.get(surface_type, self.formatting_rules.get('default', {}))
    
    def get_consistency_rules(self) -> Dict[str, Any]:
        """Get cross-surface consistency validation rules."""
        return self.consistency_rules
    
    def get_surface_configuration(self, surface_type: str) -> Dict[str, Any]:
        """Get complete configuration for surface type."""
        return self.surface_configs.get(surface_type, {})
    
    def validate_surface_content(
        self, 
        surface_type: str, 
        content: str, 
        requirements: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate generated content against surface requirements.
        
        Returns validation results with scores and recommendations.
        """
        requirements = requirements or {}
        config = self.surface_configs.get(surface_type, {})
        formatting_rules = self.formatting_rules.get(surface_type, {})
        
        validation_results = {
            'valid': True,
            'issues': [],
            'scores': {},
            'recommendations': []
        }
        
        # Word count validation
        word_count = len(content.split())
        max_words = requirements.get('max_words', config.get('default_word_limit', 150))
        
        if word_count > max_words:
            validation_results['valid'] = False
            validation_results['issues'].append(f"Content exceeds word limit: {word_count} > {max_words}")
            validation_results['recommendations'].append("Trim content to meet word limit")
        
        validation_results['scores']['word_count_compliance'] = min(1.0, max_words / max(word_count, 1))
        
        # Format validation
        expected_format = requirements.get('format', config.get('default_format', 'paragraph'))
        format_score = self._validate_format(content, expected_format, formatting_rules)
        validation_results['scores']['format_compliance'] = format_score
        
        if format_score < 0.8:
            validation_results['issues'].append(f"Content format doesn't match expected: {expected_format}")
            validation_results['recommendations'].append(f"Reformat content to {expected_format} style")
        
        # Tone validation
        tone_requirements = formatting_rules.get('tone_requirements', {})
        tone_score = self._validate_tone(content, tone_requirements)
        validation_results['scores']['tone_compliance'] = tone_score
        
        if tone_score < 0.7:
            validation_results['issues'].append("Content tone doesn't match professional surface requirements")
            validation_results['recommendations'].append("Adjust tone to match professional standards")
        
        # Overall score
        scores = validation_results['scores']
        validation_results['scores']['overall'] = sum(scores.values()) / len(scores)
        
        return validation_results
    
    def _load_surface_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Load surface-specific configurations."""
        return {
            'cv_summary': {
                'default_word_limit': 100,
                'default_format': 'paragraph',
                'default_tone': 'professional',
                'purpose': 'Concise value proposition for CV/resume',
                'key_elements': ['achievements', 'skills', 'value_proposition'],
                'optimization_targets': ['ATS_compatibility', 'recruiter_scanning']
            },
            'linkedin_summary': {
                'default_word_limit': 220,
                'default_format': 'paragraph',
                'default_tone': 'conversational_professional',
                'purpose': 'Networking and personal branding',
                'key_elements': ['story', 'achievements', 'call_to_action'],
                'optimization_targets': ['engagement', 'searchability', 'connection_building']
            },
            'portfolio_intro': {
                'default_word_limit': 180,
                'default_format': 'paragraph',
                'default_tone': 'confident_professional',
                'purpose': 'Showcase expertise and attract opportunities',
                'key_elements': ['expertise', 'unique_approach', 'thought_leadership'],
                'optimization_targets': ['credibility', 'differentiation', 'expertise_demonstration']
            },
            'cover_letter_intro': {
                'default_word_limit': 120,
                'default_format': 'paragraph',
                'default_tone': 'professional',
                'purpose': 'Opening paragraph for job applications',
                'key_elements': ['position_interest', 'value_alignment', 'key_qualifications'],
                'optimization_targets': ['attention_grabbing', 'relevance', 'enthusiasm']
            },
            'elevator_pitch': {
                'default_word_limit': 75,
                'default_format': 'spoken',
                'default_tone': 'confident',
                'purpose': 'Brief verbal introduction for networking',
                'key_elements': ['role', 'value_proposition', 'conversation_starter'],
                'optimization_targets': ['memorability', 'clarity', 'engagement']
            }
        }
    
    def _load_prompt_templates(self) -> Dict[str, Dict[str, str]]:
        """Load prompt templates for each surface type."""
        return {
            'cv_summary': {
                'base_prompt': '''Create a compelling CV summary that captures this professional's brand identity.

Professional Themes: {themes}
Communication Style: {tone} tone, {style} approach, {formality} level
Professional Identity: {professional_identity}

Requirements:
- Maximum {word_limit} words
- {format_style} format
- Focus on quantifiable achievements and value proposition
- Use active voice and strong action verbs
- Optimize for ATS systems and recruiter scanning
- Highlight unique differentiators

Generate a powerful CV summary that immediately communicates their value:''',
                
                'specific_guidelines': '''
Additional Guidelines:
- Start with years of experience if significant (5+ years)
- Include 2-3 core competencies or specializations
- Mention industry or functional area if relevant
- End with a forward-looking statement or value proposition
- Avoid first person pronouns
- Use present tense for current role, past tense for previous'''
            },
            
            'linkedin_summary': {
                'base_prompt': '''Create an engaging LinkedIn About section that reflects this professional's brand.

Professional Themes: {themes}
Communication Style: {tone} tone, {style} approach
Career Progression: {career_progression}
Professional Identity: {professional_identity}
Future Direction: {future_direction}

Requirements:
- Maximum {word_limit} words
- {format_style} format
- Conversational yet professional tone
- Tell a story that connects past, present, and future
- Include a call-to-action for connection or collaboration
- Optimize for LinkedIn search and networking

Generate a compelling LinkedIn About section:''',
                
                'specific_guidelines': '''
Additional Guidelines:
- Use first person voice for authenticity
- Start with a hook or interesting statement
- Include 2-3 short paragraphs maximum
- Mention key industries, skills, or achievements
- End with how others can connect or work with them
- Include relevant keywords for search optimization
- Show personality while maintaining professionalism'''
            },
            
            'portfolio_intro': {
                'base_prompt': '''Create a portfolio introduction that establishes thought leadership and expertise.

Professional Themes: {themes}
Communication Style: {tone} tone, {style} approach
Professional Identity: {professional_identity}
Career Progression: {career_progression}

Requirements:
- Maximum {word_limit} words
- {format_style} format
- Demonstrate deep expertise and unique approach
- Showcase thought leadership and innovation
- Create compelling narrative that draws readers in
- Position for high-value opportunities

Generate a captivating portfolio introduction:''',
                
                'specific_guidelines': '''
Additional Guidelines:
- Lead with expertise and unique value proposition
- Mention signature methodologies or approaches if applicable
- Include notable achievements or recognitions
- Reference types of clients or projects worked with
- Convey passion and commitment to excellence
- End with what readers can expect from the portfolio
- Use confident but not boastful language'''
            },
            
            'cover_letter_intro': {
                'base_prompt': '''Create an opening paragraph for a cover letter that captures attention.

Professional Themes: {themes}
Communication Style: {tone} tone, {style} approach
Professional Identity: {professional_identity}

Requirements:
- Maximum {word_limit} words
- {format_style} format
- Hook the reader's attention immediately
- Express genuine interest in the specific role
- Highlight most relevant qualifications
- Set up the rest of the cover letter

Generate an attention-grabbing cover letter opening:''',
                
                'specific_guidelines': '''
Additional Guidelines:
- Reference specific position and company
- Mention how you learned about the opportunity if relevant
- Lead with your strongest relevant qualification
- Show enthusiasm without being overly eager
- Avoid generic openings like "I am writing to apply"
- Create a bridge to discuss fit in subsequent paragraphs
- Use formal business writing tone'''
            },
            
            'elevator_pitch': {
                'base_prompt': '''Create a brief elevator pitch for networking situations.

Professional Themes: {themes}
Communication Style: {tone} tone, {style} approach
Professional Identity: {professional_identity}

Requirements:
- Maximum {word_limit} words (30-45 seconds spoken)
- {format_style} format optimized for verbal delivery
- Memorable and conversational
- Include a conversation starter or question
- Easy to remember and deliver naturally

Generate a compelling elevator pitch:''',
                
                'specific_guidelines': '''
Additional Guidelines:
- Start with name and current role or expertise area
- Include one key achievement or differentiator
- Mention who you help or what you solve
- End with a question or invitation for discussion
- Use simple, clear language that flows naturally
- Practice-friendly structure for consistent delivery
- Adaptable to different networking contexts'''
            }
        }
    
    def _load_formatting_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load formatting and style rules for each surface."""
        return {
            'cv_summary': {
                'sentence_structure': 'concise',
                'tone_requirements': {
                    'formality': 'high',
                    'confidence': 'high', 
                    'enthusiasm': 'moderate'
                },
                'language_style': 'active_voice',
                'punctuation': 'minimal',
                'paragraph_structure': 'single_block'
            },
            'linkedin_summary': {
                'sentence_structure': 'varied',
                'tone_requirements': {
                    'formality': 'moderate',
                    'confidence': 'high',
                    'enthusiasm': 'high'
                },
                'language_style': 'conversational_professional',
                'punctuation': 'natural',
                'paragraph_structure': 'multiple_short'
            },
            'portfolio_intro': {
                'sentence_structure': 'sophisticated',
                'tone_requirements': {
                    'formality': 'high',
                    'confidence': 'very_high',
                    'enthusiasm': 'moderate'
                },
                'language_style': 'thought_leadership',
                'punctuation': 'professional',
                'paragraph_structure': 'flowing_narrative'
            },
            'default': {
                'sentence_structure': 'clear',
                'tone_requirements': {
                    'formality': 'moderate',
                    'confidence': 'moderate',
                    'enthusiasm': 'moderate'
                },
                'language_style': 'professional',
                'punctuation': 'standard',
                'paragraph_structure': 'logical'
            }
        }
    
    def _load_consistency_rules(self) -> Dict[str, Any]:
        """Load rules for cross-surface consistency validation."""
        return {
            'core_themes': {
                'threshold': 0.8,
                'description': 'Core professional themes should appear consistently'
            },
            'voice_tone': {
                'threshold': 0.7,
                'description': 'Voice and communication style should be recognizable'
            },
            'value_proposition': {
                'threshold': 0.8,
                'description': 'Key value propositions should align across surfaces'
            },
            'professional_identity': {
                'threshold': 0.9,
                'description': 'Professional identity should remain consistent'
            },
            'key_achievements': {
                'threshold': 0.6,
                'description': 'Major achievements should be reflected appropriately'
            }
        }
    
    def _format_themes(self, themes: List[Dict[str, Any]]) -> str:
        """Format themes for prompt insertion."""
        if not themes:
            return "Professional expertise and experience"
        
        theme_names = [
            theme.get('theme_name', str(theme)) 
            for theme in themes[:5]  # Limit to top 5 themes
        ]
        
        return ', '.join(theme_names)
    
    def _format_career_progression(self, progression: List[str]) -> str:
        """Format career progression for prompt insertion."""
        if not progression:
            return "Steady professional growth and development"
        
        return '; '.join(progression[:3])  # Limit to top 3 progression points
    
    def _get_contextual_modifiers(
        self, 
        surface_type: str, 
        brand_context: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> str:
        """Get contextual modifiers based on brand confidence and context."""
        
        modifiers = []
        
        # Brand confidence modifiers
        confidence = brand_context.get('brand_confidence', 0.0)
        if confidence < 0.7:
            modifiers.append("\nNote: Use clear, straightforward language due to moderate brand confidence.")
        elif confidence > 0.9:
            modifiers.append("\nNote: Leverage strong brand confidence for compelling positioning.")
        
        # Theme count modifiers
        themes_count = brand_context.get('themes_count', 0)
        if themes_count < 3:
            modifiers.append("\nFocus on available themes and supplement with general professional strengths.")
        elif themes_count > 7:
            modifiers.append("\nSelect the most relevant themes to avoid overcrowding the content.")
        
        # Regeneration context
        if brand_context.get('regeneration_context'):
            user_feedback = brand_context.get('user_feedback', '')
            if user_feedback:
                modifiers.append(f"\nUser Feedback to Address: {user_feedback}")
                modifiers.append("\nPlease incorporate this feedback while maintaining professional quality.")
        
        return ''.join(modifiers)
    
    def _validate_format(self, content: str, expected_format: str, formatting_rules: Dict[str, Any]) -> float:
        """Validate content format compliance."""
        
        # Basic format validation
        if expected_format == 'paragraph':
            # Should be cohesive paragraph(s)
            paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
            if paragraph_count > 3:
                return 0.6  # Too many paragraphs
            return 1.0
        
        elif expected_format == 'bullet':
            # Should use bullet points or list format
            if '•' in content or content.strip().startswith('-'):
                return 1.0
            return 0.3
        
        elif expected_format == 'spoken':
            # Should be natural for speaking
            sentence_count = len([s for s in content.split('.') if s.strip()])
            avg_sentence_length = len(content.split()) / max(sentence_count, 1)
            if avg_sentence_length <= 15:  # Shorter sentences better for speaking
                return 1.0
            return 0.7
        
        return 0.8  # Default moderate compliance
    
    def _validate_tone(self, content: str, tone_requirements: Dict[str, Any]) -> float:
        """Validate content tone compliance."""
        
        # Basic tone validation (simplified)
        content_lower = content.lower()
        
        # Check for confidence indicators
        confidence_words = ['achieved', 'led', 'delivered', 'created', 'improved', 'successful']
        confidence_score = sum(1 for word in confidence_words if word in content_lower) / max(len(content.split()), 1)
        
        # Check formality
        informal_words = ['awesome', 'super', 'really', 'totally', 'kinda']
        formality_score = 1.0 - (sum(1 for word in informal_words if word in content_lower) * 0.2)
        
        # Average the scores
        tone_score = (confidence_score * 10 + formality_score) / 2
        
        return min(1.0, tone_score)