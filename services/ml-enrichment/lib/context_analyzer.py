"""
Surface Context Analyzer for AI Brand Roadmap

This module provides context analysis capabilities for different professional surfaces,
enabling adaptive content generation based on surface-specific requirements,
audience expectations, and contextual nuances.

Key capabilities:
- Surface-specific context analysis and requirements extraction
- Cross-surface context divergence detection and resolution
- Contextual adaptation recommendations for content optimization
- Context-aware consistency validation across surfaces
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from domain.entities import BrandRepresentation, ContentGeneration, ProfessionalSurface


@dataclass
class ContextRequirements:
    """Surface-specific context requirements and constraints."""
    
    surface_type: str
    audience_profile: str
    communication_style: str
    content_priorities: List[str]
    tone_requirements: Dict[str, Any]
    length_constraints: Dict[str, int]
    formatting_rules: List[str]
    industry_considerations: List[str]
    platform_constraints: Dict[str, Any]


@dataclass
class ContextAnalysis:
    """Analysis results for surface context adaptation."""
    
    surface_type: str
    context_score: float
    adaptation_recommendations: List[str]
    divergence_points: List[str]
    consistency_risks: List[str]
    optimization_opportunities: List[str]
    confidence_level: float
    analysis_metadata: Dict[str, Any]


@dataclass
class CrossSurfaceContextMap:
    """Context mapping across multiple surfaces for consistency analysis."""
    
    surface_contexts: Dict[str, ContextAnalysis]
    shared_themes: List[str]
    divergent_aspects: List[Dict[str, Any]]
    consistency_score: float
    adaptation_strategy: Dict[str, Any]
    resolution_recommendations: List[str]


class SurfaceContextAnalyzer:
    """
    Analyzes and adapts content context for different professional surfaces.
    
    Provides sophisticated context analysis to ensure content is optimally
    adapted for each surface while maintaining brand consistency across all platforms.
    """
    
    def __init__(self):
        """Initialize context analyzer with surface-specific configurations."""
        self.logger = logging.getLogger(__name__)
        self.context_requirements = self._initialize_context_requirements()
        self.adaptation_strategies = self._initialize_adaptation_strategies()
        
    def _initialize_context_requirements(self) -> Dict[str, ContextRequirements]:
        """Initialize context requirements for each professional surface."""
        
        return {
            'cv_summary': ContextRequirements(
                surface_type='cv_summary',
                audience_profile='hiring_managers_recruiters',
                communication_style='professional_concise',
                content_priorities=[
                    'quantifiable_achievements',
                    'relevant_skills',
                    'career_progression',
                    'value_proposition',
                    'industry_expertise'
                ],
                tone_requirements={
                    'formality': 'formal',
                    'confidence': 'assertive',
                    'energy': 'professional',
                    'perspective': 'third_person_implied'
                },
                length_constraints={
                    'min_words': 80,
                    'max_words': 150,
                    'optimal_words': 120
                },
                formatting_rules=[
                    'bullet_points_preferred',
                    'action_verbs_start',
                    'quantified_results',
                    'no_personal_pronouns',
                    'industry_keywords_integrated'
                ],
                industry_considerations=[
                    'technical_depth_appropriate',
                    'industry_terminology',
                    'regulatory_awareness',
                    'market_trends_relevance'
                ],
                platform_constraints={
                    'character_limit': None,
                    'keyword_optimization': True,
                    'ats_compatibility': True,
                    'visual_hierarchy': 'text_only'
                }
            ),
            
            'linkedin_summary': ContextRequirements(
                surface_type='linkedin_summary',
                audience_profile='professional_network_peers',
                communication_style='conversational_professional',
                content_priorities=[
                    'personal_brand_narrative',
                    'professional_passion',
                    'network_value',
                    'career_vision',
                    'thought_leadership'
                ],
                tone_requirements={
                    'formality': 'business_casual',
                    'confidence': 'authentic',
                    'energy': 'engaging',
                    'perspective': 'first_person'
                },
                length_constraints={
                    'min_words': 150,
                    'max_words': 300,
                    'optimal_words': 220
                },
                formatting_rules=[
                    'story_narrative_flow',
                    'personal_pronouns_welcome',
                    'call_to_action_ending',
                    'paragraph_breaks',
                    'emoji_selective_use'
                ],
                industry_considerations=[
                    'networking_opportunities',
                    'thought_leadership_potential',
                    'industry_discussions',
                    'professional_community_engagement'
                ],
                platform_constraints={
                    'character_limit': 2000,
                    'keyword_optimization': True,
                    'hashtag_integration': True,
                    'visual_hierarchy': 'paragraph_based'
                }
            ),
            
            'portfolio_intro': ContextRequirements(
                surface_type='portfolio_intro',
                audience_profile='potential_clients_collaborators',
                communication_style='creative_professional',
                content_priorities=[
                    'creative_vision',
                    'unique_approach',
                    'portfolio_preview',
                    'collaboration_value',
                    'expertise_demonstration'
                ],
                tone_requirements={
                    'formality': 'creative_professional',
                    'confidence': 'compelling',
                    'energy': 'inspiring',
                    'perspective': 'first_person_narrative'
                },
                length_constraints={
                    'min_words': 100,
                    'max_words': 200,
                    'optimal_words': 150
                },
                formatting_rules=[
                    'engaging_opening',
                    'visual_storytelling',
                    'portfolio_integration_hints',
                    'personal_voice_strong',
                    'call_to_exploration'
                ],
                industry_considerations=[
                    'creative_differentiation',
                    'aesthetic_alignment',
                    'portfolio_coherence',
                    'client_value_focus'
                ],
                platform_constraints={
                    'character_limit': None,
                    'keyword_optimization': False,
                    'visual_integration': True,
                    'visual_hierarchy': 'design_focused'
                }
            )
        }
    
    def _initialize_adaptation_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize adaptation strategies for different context scenarios."""
        
        return {
            'technical_role': {
                'cv_summary': ['emphasize_technical_skills', 'quantify_system_impact', 'highlight_certifications'],
                'linkedin_summary': ['share_technical_passion', 'mention_continuous_learning', 'engage_tech_community'],
                'portfolio_intro': ['showcase_technical_creativity', 'demonstrate_problem_solving', 'highlight_innovation']
            },
            'creative_role': {
                'cv_summary': ['quantify_creative_impact', 'highlight_awards_recognition', 'showcase_brand_results'],
                'linkedin_summary': ['tell_creative_journey', 'share_inspiration_sources', 'build_creative_network'],
                'portfolio_intro': ['express_creative_vision', 'preview_signature_work', 'invite_collaboration']
            },
            'leadership_role': {
                'cv_summary': ['emphasize_team_growth', 'quantify_business_impact', 'highlight_strategic_wins'],
                'linkedin_summary': ['share_leadership_philosophy', 'discuss_team_development', 'engage_leadership_topics'],
                'portfolio_intro': ['demonstrate_leadership_results', 'showcase_transformation_stories', 'invite_strategic_discussions']
            },
            'consultant_role': {
                'cv_summary': ['highlight_client_results', 'showcase_methodology', 'emphasize_industry_expertise'],
                'linkedin_summary': ['share_consulting_insights', 'build_thought_leadership', 'engage_industry_discussions'],
                'portfolio_intro': ['preview_case_studies', 'demonstrate_value_delivery', 'invite_consultation']
            }
        }
    
    async def analyze_surface_context(
        self,
        surface: ProfessionalSurface,
        brand: BrandRepresentation,
        existing_content: Optional[ContentGeneration] = None
    ) -> ContextAnalysis:
        """
        Analyze context requirements and optimization opportunities for a specific surface.
        
        Args:
            surface: Target professional surface
            brand: Brand representation for context alignment
            existing_content: Optional existing content for comparison
            
        Returns:
            Detailed context analysis with adaptation recommendations
        """
        self.logger.info(f"Analyzing context for surface {surface.surface_type}")
        
        try:
            # Get surface context requirements
            requirements = self.context_requirements.get(surface.surface_type)
            if not requirements:
                raise ValueError(f"No context requirements defined for surface {surface.surface_type}")
            
            # Analyze brand alignment with surface context
            brand_alignment = await self._analyze_brand_surface_alignment(brand, requirements)
            
            # Generate adaptation recommendations
            adaptations = await self._generate_adaptation_recommendations(
                brand, requirements, brand_alignment
            )
            
            # Identify potential consistency risks
            consistency_risks = await self._identify_consistency_risks(
                brand, requirements, existing_content
            )
            
            # Find optimization opportunities
            optimizations = await self._find_optimization_opportunities(
                brand, requirements, surface
            )
            
            # Calculate context score
            context_score = self._calculate_context_score(
                brand_alignment, adaptations, consistency_risks
            )
            
            analysis = ContextAnalysis(
                surface_type=surface.surface_type,
                context_score=context_score,
                adaptation_recommendations=adaptations,
                divergence_points=brand_alignment.get('divergence_points', []),
                consistency_risks=consistency_risks,
                optimization_opportunities=optimizations,
                confidence_level=brand_alignment.get('confidence_level', 0.8),
                analysis_metadata={
                    'analysis_timestamp': datetime.utcnow().isoformat(),
                    'brand_themes_count': len(brand.professional_themes),
                    'surface_requirements_matched': len([req for req in requirements.content_priorities if self._brand_supports_requirement(brand, req)]),
                    'adaptation_complexity': self._assess_adaptation_complexity(adaptations),
                    'context_requirements_version': '1.0'
                }
            )
            
            self.logger.info(f"Context analysis complete for {surface.surface_type} with score {context_score:.3f}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Context analysis failed for {surface.surface_type}: {str(e)}")
            raise
    
    async def analyze_cross_surface_context(
        self,
        surfaces: List[ProfessionalSurface],
        brand: BrandRepresentation,
        existing_content: List[ContentGeneration] = None
    ) -> CrossSurfaceContextMap:
        """
        Analyze context consistency and adaptation strategy across multiple surfaces.
        
        Args:
            surfaces: List of professional surfaces to analyze
            brand: Brand representation for consistency analysis
            existing_content: Optional existing content for cross-surface comparison
            
        Returns:
            Cross-surface context mapping with consistency analysis
        """
        self.logger.info(f"Analyzing cross-surface context for {len(surfaces)} surfaces")
        
        try:
            # Analyze context for each surface
            surface_analyses = {}
            for surface in surfaces:
                existing_for_surface = None
                if existing_content:
                    existing_for_surface = next(
                        (content for content in existing_content if content.surface_id == surface.surface_id),
                        None
                    )
                
                analysis = await self.analyze_surface_context(surface, brand, existing_for_surface)
                surface_analyses[surface.surface_type] = analysis
            
            # Identify shared themes across surfaces
            shared_themes = self._identify_shared_themes(surface_analyses, brand)
            
            # Detect divergent aspects
            divergent_aspects = await self._detect_divergent_aspects(surface_analyses, brand)
            
            # Calculate cross-surface consistency score
            consistency_score = self._calculate_cross_surface_consistency_score(
                surface_analyses, shared_themes, divergent_aspects
            )
            
            # Develop adaptation strategy
            adaptation_strategy = await self._develop_adaptation_strategy(
                surface_analyses, shared_themes, divergent_aspects, brand
            )
            
            # Generate resolution recommendations
            resolution_recommendations = await self._generate_resolution_recommendations(
                divergent_aspects, adaptation_strategy
            )
            
            context_map = CrossSurfaceContextMap(
                surface_contexts=surface_analyses,
                shared_themes=shared_themes,
                divergent_aspects=divergent_aspects,
                consistency_score=consistency_score,
                adaptation_strategy=adaptation_strategy,
                resolution_recommendations=resolution_recommendations
            )
            
            self.logger.info(f"Cross-surface context analysis complete with consistency score {consistency_score:.3f}")
            
            return context_map
            
        except Exception as e:
            self.logger.error(f"Cross-surface context analysis failed: {str(e)}")
            raise
    
    async def recommend_context_adaptations(
        self,
        content_generations: List[ContentGeneration],
        brand: BrandRepresentation,
        target_improvements: List[str] = None
    ) -> Dict[str, List[str]]:
        """
        Recommend specific context adaptations for existing content generations.
        
        Args:
            content_generations: Existing content to analyze for adaptations
            brand: Brand representation for alignment analysis
            target_improvements: Optional specific areas to focus improvements on
            
        Returns:
            Surface-specific adaptation recommendations
        """
        self.logger.info(f"Generating context adaptations for {len(content_generations)} content pieces")
        
        try:
            adaptation_recommendations = {}
            
            for generation in content_generations:
                surface_type = generation.generation_metadata.get('surface_type')
                requirements = self.context_requirements.get(surface_type)
                
                if not requirements:
                    continue
                
                # Analyze current content against requirements
                content_analysis = await self._analyze_content_context_alignment(
                    generation.content, requirements, brand
                )
                
                # Generate specific recommendations
                recommendations = await self._generate_specific_adaptations(
                    content_analysis, requirements, brand, target_improvements
                )
                
                adaptation_recommendations[surface_type] = recommendations
            
            self.logger.info(f"Generated adaptations for {len(adaptation_recommendations)} surfaces")
            
            return adaptation_recommendations
            
        except Exception as e:
            self.logger.error(f"Context adaptation recommendation failed: {str(e)}")
            raise
    
    async def _analyze_brand_surface_alignment(
        self,
        brand: BrandRepresentation,
        requirements: ContextRequirements
    ) -> Dict[str, Any]:
        """Analyze how well brand characteristics align with surface requirements."""
        
        # Voice characteristic alignment
        voice_alignment = self._assess_voice_alignment(
            brand.voice_characteristics, requirements.tone_requirements
        )
        
        # Theme priority alignment
        theme_alignment = self._assess_theme_alignment(
            brand.professional_themes, requirements.content_priorities
        )
        
        # Industry consideration alignment
        industry_alignment = self._assess_industry_alignment(
            brand, requirements.industry_considerations
        )
        
        return {
            'voice_alignment_score': voice_alignment,
            'theme_alignment_score': theme_alignment,
            'industry_alignment_score': industry_alignment,
            'overall_alignment': (voice_alignment + theme_alignment + industry_alignment) / 3,
            'confidence_level': min(voice_alignment, theme_alignment, industry_alignment) * 0.8 + 0.2,
            'divergence_points': self._identify_alignment_divergences(
                brand, requirements, voice_alignment, theme_alignment, industry_alignment
            )
        }
    
    async def _generate_adaptation_recommendations(
        self,
        brand: BrandRepresentation,
        requirements: ContextRequirements,
        alignment_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate specific adaptation recommendations for surface optimization."""
        
        recommendations = []
        
        # Voice adaptation recommendations
        if alignment_analysis['voice_alignment_score'] < 0.8:
            recommendations.extend(self._get_voice_adaptations(brand, requirements))
        
        # Content priority adaptations
        if alignment_analysis['theme_alignment_score'] < 0.8:
            recommendations.extend(self._get_theme_adaptations(brand, requirements))
        
        # Industry-specific adaptations
        if alignment_analysis['industry_alignment_score'] < 0.8:
            recommendations.extend(self._get_industry_adaptations(brand, requirements))
        
        # Length and formatting adaptations
        recommendations.extend(self._get_formatting_adaptations(requirements))
        
        return recommendations
    
    async def _identify_consistency_risks(
        self,
        brand: BrandRepresentation,
        requirements: ContextRequirements,
        existing_content: Optional[ContentGeneration]
    ) -> List[str]:
        """Identify potential consistency risks for the surface."""
        
        risks = []
        
        # Brand voice consistency risks
        if self._has_voice_inconsistency_risk(brand.voice_characteristics, requirements):
            risks.append("Voice characteristics may diverge from established brand tone")
        
        # Theme emphasis risks
        if self._has_theme_emphasis_risk(brand.professional_themes, requirements):
            risks.append("Content priorities may overshadow core brand themes")
        
        # Platform constraint risks
        if self._has_platform_constraint_risk(requirements):
            risks.append("Platform constraints may limit brand expression")
        
        # Cross-surface consistency risks
        if existing_content and self._has_cross_surface_risk(existing_content, requirements):
            risks.append("Surface-specific adaptations may create cross-surface inconsistencies")
        
        return risks
    
    async def _find_optimization_opportunities(
        self,
        brand: BrandRepresentation,
        requirements: ContextRequirements,
        surface: ProfessionalSurface
    ) -> List[str]:
        """Find optimization opportunities for surface-specific content."""
        
        opportunities = []
        
        # Leverage unique brand strengths
        strong_themes = [theme for theme in brand.professional_themes if theme.confidence_score > 0.8]
        if strong_themes:
            opportunities.append(f"Leverage strong themes: {', '.join([theme.theme_name for theme in strong_themes[:3]])}")
        
        # Optimize for surface audience
        if requirements.audience_profile in self.adaptation_strategies:
            opportunities.append(f"Optimize for {requirements.audience_profile} expectations")
        
        # Platform-specific optimizations
        if requirements.platform_constraints.get('keyword_optimization'):
            opportunities.append("Integrate industry keywords for discoverability")
        
        if requirements.platform_constraints.get('visual_integration'):
            opportunities.append("Align content with visual portfolio elements")
        
        return opportunities
    
    def _calculate_context_score(
        self,
        alignment_analysis: Dict[str, Any],
        adaptations: List[str],
        risks: List[str]
    ) -> float:
        """Calculate overall context optimization score."""
        
        alignment_score = alignment_analysis['overall_alignment']
        adaptation_penalty = len(adaptations) * 0.05  # More adaptations = more work needed
        risk_penalty = len(risks) * 0.1  # More risks = lower score
        
        return max(0.0, min(1.0, alignment_score - adaptation_penalty - risk_penalty))
    
    def _brand_supports_requirement(self, brand: BrandRepresentation, requirement: str) -> bool:
        """Check if brand characteristics support a specific requirement."""
        
        # Simple heuristic - in production this would be more sophisticated
        theme_keywords = [theme.theme_name.lower() for theme in brand.professional_themes]
        return any(keyword in requirement.lower() for keyword in theme_keywords)
    
    def _assess_adaptation_complexity(self, adaptations: List[str]) -> str:
        """Assess the complexity level of required adaptations."""
        
        if len(adaptations) <= 2:
            return 'low'
        elif len(adaptations) <= 5:
            return 'medium'
        else:
            return 'high'
    
    def _assess_voice_alignment(self, voice_characteristics, tone_requirements: Dict[str, Any]) -> float:
        """Assess alignment between brand voice and surface tone requirements."""
        
        # Simple alignment scoring - in production this would use semantic analysis
        alignment_score = 0.8  # Base score
        
        # Check formality alignment
        brand_formality = voice_characteristics.formality_level
        required_formality = tone_requirements.get('formality', 'professional')
        
        formality_mapping = {
            'casual': 0.2, 'business_casual': 0.4, 'professional': 0.6, 
            'formal': 0.8, 'highly_formal': 1.0
        }
        
        brand_formality_score = formality_mapping.get(brand_formality, 0.6)
        required_formality_score = formality_mapping.get(required_formality, 0.6)
        
        formality_alignment = 1.0 - abs(brand_formality_score - required_formality_score)
        
        return (alignment_score + formality_alignment) / 2
    
    def _assess_theme_alignment(self, themes, content_priorities: List[str]) -> float:
        """Assess alignment between brand themes and content priorities."""
        
        if not themes or not content_priorities:
            return 0.5
        
        # Count theme coverage of priorities
        covered_priorities = 0
        for priority in content_priorities:
            if any(priority.lower() in theme.theme_name.lower() or 
                   priority.lower() in theme.description.lower() if theme.description 
                   else False for theme in themes):
                covered_priorities += 1
        
        return covered_priorities / len(content_priorities)
    
    def _assess_industry_alignment(self, brand: BrandRepresentation, industry_considerations: List[str]) -> float:
        """Assess alignment with industry-specific considerations."""
        
        # Simple heuristic based on theme categories and industry keywords
        industry_themes = [theme for theme in brand.professional_themes 
                         if theme.theme_category in ['industry', 'skill', 'role']]
        
        if not industry_themes:
            return 0.6  # Neutral score when insufficient data
        
        # Higher score for more industry-relevant themes
        return min(1.0, len(industry_themes) / 3)
    
    def _identify_alignment_divergences(
        self, brand, requirements, voice_score: float, theme_score: float, industry_score: float
    ) -> List[str]:
        """Identify specific points where brand and surface requirements diverge."""
        
        divergences = []
        
        if voice_score < 0.7:
            divergences.append(f"Voice formality mismatch: brand {brand.voice_characteristics.formality_level} vs required {requirements.tone_requirements.get('formality')}")
        
        if theme_score < 0.7:
            divergences.append("Limited theme coverage for surface content priorities")
        
        if industry_score < 0.7:
            divergences.append("Insufficient industry-specific theme representation")
        
        return divergences
    
    def _get_voice_adaptations(self, brand, requirements) -> List[str]:
        """Generate voice adaptation recommendations."""
        return [
            f"Adjust tone to {requirements.tone_requirements.get('formality', 'professional')} level",
            f"Adapt energy level to {requirements.tone_requirements.get('energy', 'balanced')}",
            f"Use {requirements.tone_requirements.get('perspective', 'appropriate')} perspective"
        ]
    
    def _get_theme_adaptations(self, brand, requirements) -> List[str]:
        """Generate theme adaptation recommendations."""
        return [
            f"Emphasize {', '.join(requirements.content_priorities[:2])} in content structure",
            "Integrate quantifiable achievements where possible",
            "Balance brand themes with surface-specific priorities"
        ]
    
    def _get_industry_adaptations(self, brand, requirements) -> List[str]:
        """Generate industry-specific adaptation recommendations."""
        return [
            "Incorporate industry-specific terminology",
            "Reference relevant market trends or challenges",
            "Highlight industry-standard qualifications or certifications"
        ]
    
    def _get_formatting_adaptations(self, requirements) -> List[str]:
        """Generate formatting and structure adaptation recommendations."""
        adaptations = []
        
        if 'bullet_points_preferred' in requirements.formatting_rules:
            adaptations.append("Structure content with bullet points for readability")
        
        if 'action_verbs_start' in requirements.formatting_rules:
            adaptations.append("Begin statements with strong action verbs")
        
        if requirements.length_constraints:
            optimal = requirements.length_constraints.get('optimal_words', 150)
            adaptations.append(f"Target approximately {optimal} words for optimal length")
        
        return adaptations
    
    def _has_voice_inconsistency_risk(self, voice_characteristics, requirements) -> bool:
        """Check if there's risk of voice inconsistency."""
        brand_formality = voice_characteristics.formality_level
        required_formality = requirements.tone_requirements.get('formality')
        
        formality_order = ['casual', 'business_casual', 'professional', 'formal', 'highly_formal']
        
        try:
            brand_index = formality_order.index(brand_formality)
            required_index = formality_order.index(required_formality)
            return abs(brand_index - required_index) > 1
        except ValueError:
            return True  # Risk if unknown formality levels
    
    def _has_theme_emphasis_risk(self, themes, requirements) -> bool:
        """Check if there's risk of theme emphasis misalignment."""
        strong_themes = [theme for theme in themes if theme.confidence_score > 0.8]
        return len(strong_themes) < 2  # Risk if few strong themes to work with
    
    def _has_platform_constraint_risk(self, requirements) -> bool:
        """Check if platform constraints pose consistency risks."""
        constraints = requirements.platform_constraints
        return (
            constraints.get('character_limit') and constraints['character_limit'] < 500 or
            constraints.get('ats_compatibility') and constraints['ats_compatibility'] or
            constraints.get('keyword_optimization') and not constraints['keyword_optimization']
        )
    
    def _has_cross_surface_risk(self, existing_content, requirements) -> bool:
        """Check if adapting to requirements risks cross-surface consistency."""
        # Simple heuristic - in production would compare content semantically
        return len(requirements.content_priorities) > 3  # Risk if many specific priorities
    
    def _identify_shared_themes(self, surface_analyses: Dict[str, ContextAnalysis], brand) -> List[str]:
        """Identify themes that should be consistent across all surfaces."""
        
        # Extract core brand themes that are relevant across surfaces
        strong_themes = [theme.theme_name for theme in brand.professional_themes 
                        if theme.confidence_score > 0.7]
        
        # Filter to themes that appear in multiple surface analyses
        shared_themes = []
        for theme in strong_themes:
            appearance_count = sum(
                1 for analysis in surface_analyses.values()
                if any(theme.lower() in rec.lower() for rec in analysis.adaptation_recommendations)
            )
            if appearance_count >= 2:
                shared_themes.append(theme)
        
        return shared_themes
    
    async def _detect_divergent_aspects(
        self, surface_analyses: Dict[str, ContextAnalysis], brand
    ) -> List[Dict[str, Any]]:
        """Detect aspects that diverge significantly between surfaces."""
        
        divergent_aspects = []
        
        # Compare context scores across surfaces
        context_scores = {surface: analysis.context_score 
                         for surface, analysis in surface_analyses.items()}
        
        max_score = max(context_scores.values())
        min_score = min(context_scores.values())
        
        if max_score - min_score > 0.3:  # Significant divergence
            divergent_aspects.append({
                'aspect': 'context_optimization',
                'description': 'Significant variation in context optimization across surfaces',
                'affected_surfaces': [surface for surface, score in context_scores.items() 
                                    if score < max_score - 0.1],
                'severity': 'medium'
            })
        
        # Compare adaptation requirements
        all_adaptations = []
        for analysis in surface_analyses.values():
            all_adaptations.extend(analysis.adaptation_recommendations)
        
        if len(set(all_adaptations)) > len(all_adaptations) * 0.7:  # High uniqueness
            divergent_aspects.append({
                'aspect': 'adaptation_requirements',
                'description': 'Surface-specific adaptations may create inconsistencies',
                'affected_surfaces': list(surface_analyses.keys()),
                'severity': 'low'
            })
        
        return divergent_aspects
    
    def _calculate_cross_surface_consistency_score(
        self, surface_analyses, shared_themes, divergent_aspects
    ) -> float:
        """Calculate overall cross-surface consistency score."""
        
        # Base score from individual surface scores
        individual_scores = [analysis.context_score for analysis in surface_analyses.values()]
        avg_individual_score = sum(individual_scores) / len(individual_scores)
        
        # Bonus for shared themes
        shared_theme_bonus = min(0.2, len(shared_themes) * 0.05)
        
        # Penalty for divergent aspects
        divergence_penalty = sum(
            0.1 if aspect['severity'] == 'low' else 
            0.2 if aspect['severity'] == 'medium' else 0.3
            for aspect in divergent_aspects
        )
        
        return max(0.0, min(1.0, avg_individual_score + shared_theme_bonus - divergence_penalty))
    
    async def _develop_adaptation_strategy(
        self, surface_analyses, shared_themes, divergent_aspects, brand
    ) -> Dict[str, Any]:
        """Develop comprehensive adaptation strategy for cross-surface consistency."""
        
        return {
            'primary_approach': 'theme_consistency_first',
            'shared_theme_emphasis': shared_themes,
            'surface_specific_allowances': [
                aspect for aspect in divergent_aspects 
                if aspect['severity'] == 'low'
            ],
            'consistency_checkpoints': [
                'voice_characteristics_alignment',
                'core_theme_representation',
                'value_proposition_coherence'
            ],
            'adaptation_sequence': list(surface_analyses.keys()),  # Process in order
            'quality_gates': [
                {'metric': 'cross_surface_consistency', 'threshold': 0.8},
                {'metric': 'individual_surface_optimization', 'threshold': 0.7}
            ]
        }
    
    async def _generate_resolution_recommendations(
        self, divergent_aspects, adaptation_strategy
    ) -> List[str]:
        """Generate specific recommendations for resolving divergences."""
        
        recommendations = []
        
        for aspect in divergent_aspects:
            if aspect['aspect'] == 'context_optimization':
                recommendations.append(
                    f"Focus optimization efforts on {', '.join(aspect['affected_surfaces'][:2])}"
                )
            elif aspect['aspect'] == 'adaptation_requirements':
                recommendations.append(
                    "Establish core message framework before surface-specific adaptations"
                )
        
        # General consistency recommendations
        recommendations.extend([
            "Maintain consistent voice characteristics across all surfaces",
            "Ensure core value proposition appears in all content variations",
            "Review cross-surface content flow and narrative coherence"
        ])
        
        return recommendations
    
    async def _analyze_content_context_alignment(
        self, content: str, requirements: ContextRequirements, brand
    ) -> Dict[str, Any]:
        """Analyze how well existing content aligns with context requirements."""
        
        # Simple content analysis - in production would use NLP
        word_count = len(content.split())
        
        # Check length alignment
        length_score = 1.0
        if requirements.length_constraints:
            optimal = requirements.length_constraints.get('optimal_words', 150)
            length_score = max(0.5, 1.0 - abs(word_count - optimal) / optimal)
        
        # Check formatting alignment (simple heuristics)
        formatting_score = 0.8  # Default score
        if 'bullet_points_preferred' in requirements.formatting_rules:
            if '•' in content or '-' in content:
                formatting_score += 0.1
        
        if 'action_verbs_start' in requirements.formatting_rules:
            sentences = content.split('.')
            action_verb_count = sum(1 for sentence in sentences[:3] 
                                  if any(sentence.strip().lower().startswith(verb) 
                                       for verb in ['led', 'managed', 'developed', 'created', 'implemented']))
            formatting_score += action_verb_count * 0.05
        
        return {
            'length_score': length_score,
            'formatting_score': min(1.0, formatting_score),
            'overall_alignment': (length_score + formatting_score) / 2,
            'word_count': word_count,
            'improvement_areas': self._identify_content_improvement_areas(
                content, requirements, length_score, formatting_score
            )
        }
    
    async def _generate_specific_adaptations(
        self, content_analysis, requirements, brand, target_improvements=None
    ) -> List[str]:
        """Generate specific adaptation recommendations for existing content."""
        
        adaptations = []
        
        # Length adaptations
        if content_analysis['length_score'] < 0.8:
            optimal = requirements.length_constraints.get('optimal_words', 150)
            current = content_analysis['word_count']
            if current < optimal:
                adaptations.append(f"Expand content by approximately {optimal - current} words")
            else:
                adaptations.append(f"Condense content by approximately {current - optimal} words")
        
        # Formatting adaptations
        if content_analysis['formatting_score'] < 0.8:
            adaptations.extend(self._get_formatting_adaptations(requirements))
        
        # Target-specific improvements
        if target_improvements:
            for improvement in target_improvements:
                if improvement in content_analysis['improvement_areas']:
                    adaptations.append(f"Focus on improving: {improvement}")
        
        return adaptations
    
    def _identify_content_improvement_areas(
        self, content: str, requirements: ContextRequirements, 
        length_score: float, formatting_score: float
    ) -> List[str]:
        """Identify specific areas where content can be improved."""
        
        areas = []
        
        if length_score < 0.8:
            areas.append('length_optimization')
        
        if formatting_score < 0.8:
            areas.append('formatting_enhancement')
        
        # Check for content priority coverage
        priority_coverage = sum(
            1 for priority in requirements.content_priorities 
            if priority.lower().replace('_', ' ') in content.lower()
        )
        
        if priority_coverage < len(requirements.content_priorities) * 0.6:
            areas.append('content_priority_coverage')
        
        # Check for industry considerations
        industry_coverage = sum(
            1 for consideration in requirements.industry_considerations
            if consideration.lower().replace('_', ' ') in content.lower()
        )
        
        if industry_coverage < len(requirements.industry_considerations) * 0.4:
            areas.append('industry_relevance')
        
        return areas