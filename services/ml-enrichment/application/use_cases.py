"""
Brand Analysis Use Cases - Application Layer Business Logic

Implements use cases for professional brand discovery, analysis, and management.
Orchestrates brand analysis workflow using domain services and repositories.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import brand analysis components
from lib.brand_analyzer import BrandAnalyzer
from lib.document_parser import DocumentParser

# Import content generation components
from lib.content_generator import ContentGenerator
from lib.consistency_validator import ConsistencyAnalyzer

# Import adapters
from adapters.bigquery_repository import (
    BigQueryBrandRepository, BigQueryContentGenerationRepository,
    BigQueryLearningRepository, BigQueryProfessionalSurfaceRepository
)

# Import domain entities
import sys
sys.path.append('/Users/thomasdoyle/Daintree/frameworks/gcloud/CapacityReset/api/jobs-api')
from domain.entities import (
    BrandRepresentation, ContentGeneration, BrandLearningEvent, ProfessionalSurface
)


class BrandDiscoveryUseCase:
    """
    Use case for discovering professional brand from source documents.
    
    Handles the complete workflow from document parsing to brand representation
    creation and storage.
    """
    
    def __init__(self):
        """Initialize use case with required dependencies."""
        self.document_parser = DocumentParser()
        self.brand_analyzer = BrandAnalyzer()
        self.brand_repository = BigQueryBrandRepository()
        self.logger = logging.getLogger(__name__)
    
    async def analyze_brand_from_document(
        self, 
        user_id: str, 
        document_source: str, 
        source_type: str = 'auto'
    ) -> BrandRepresentation:
        """
        Complete brand discovery workflow from document source.
        
        Args:
            user_id: ID of the user for brand ownership
            document_source: URL, file path, or text content
            source_type: 'url', 'file', 'text', or 'auto' for detection
            
        Returns:
            Created BrandRepresentation with analysis results
        """
        self.logger.info(f"Starting brand discovery for user {user_id}, source type: {source_type}")
        
        try:
            # Step 1: Parse document content
            document_text, parsing_metadata = await self._parse_document_source(
                document_source, source_type
            )
            
            # Step 2: Validate document content
            if not self._validate_document_content(document_text):
                raise ValueError("Document content insufficient for brand analysis")
            
            # Step 3: Analyze brand representation
            brand_representation = await self.brand_analyzer.analyze_source_document(
                document_url=document_source,
                document_text=document_text,
                user_id=user_id
            )
            
            # Step 4: Enhance with parsing metadata
            brand_representation = self._enhance_brand_with_metadata(
                brand_representation, parsing_metadata
            )
            
            # Step 5: Store brand representation
            brand_id = await self.brand_repository.save_brand_representation(brand_representation)
            brand_representation.brand_id = brand_id
            
            self.logger.info(f"Brand discovery complete. Brand ID: {brand_id}")
            return brand_representation
            
        except Exception as e:
            self.logger.error(f"Brand discovery failed: {str(e)}")
            raise
    
    async def refresh_brand_analysis(self, brand_id: str) -> BrandRepresentation:
        """
        Re-analyze existing brand using latest source document.
        
        Args:
            brand_id: ID of existing brand to refresh
            
        Returns:
            Updated BrandRepresentation
        """
        self.logger.info(f"Refreshing brand analysis for brand {brand_id}")
        
        try:
            # Get existing brand
            existing_brand = await self.brand_repository.get_brand_by_id(brand_id)
            if not existing_brand:
                raise ValueError(f"Brand {brand_id} not found")
            
            # Re-parse source document
            document_text, parsing_metadata = await self._parse_document_source(
                existing_brand.source_document_url, 'url'
            )
            
            # Re-analyze with updated document
            refreshed_brand = await self.brand_analyzer.analyze_source_document(
                document_url=existing_brand.source_document_url,
                document_text=document_text,
                user_id=existing_brand.user_id
            )
            
            # Preserve brand ID and increment version
            refreshed_brand.brand_id = brand_id
            refreshed_brand.version = (existing_brand.version or 1) + 1
            
            # Update stored representation
            updated_brand = await self.brand_repository.update_brand(refreshed_brand)
            
            self.logger.info(f"Brand refresh complete. New version: {updated_brand.version}")
            return updated_brand
            
        except Exception as e:
            self.logger.error(f"Brand refresh failed: {str(e)}")
            raise
    
    async def _parse_document_source(self, source: str, source_type: str) -> tuple[str, Dict[str, Any]]:
        """Parse document based on source type."""
        
        if source_type == 'auto':
            source_type = self._detect_source_type(source)
        
        if source_type == 'url':
            return await self.document_parser.parse_document_from_url(source)
        elif source_type == 'file':
            return await self.document_parser.parse_document_from_file(source)
        elif source_type == 'text':
            return await self.document_parser.parse_document_text(source)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    def _detect_source_type(self, source: str) -> str:
        """Auto-detect source type from content."""
        if source.startswith(('http://', 'https://')):
            return 'url'
        elif '\n' in source or len(source) > 500:  # Likely text content
            return 'text'
        else:
            return 'file'  # Assume file path
    
    def _validate_document_content(self, document_text: str) -> bool:
        """Validate that document content is sufficient for analysis."""
        if not document_text or len(document_text.strip()) < 100:
            return False
        
        word_count = len(document_text.split())
        return word_count >= 50  # Minimum words for meaningful analysis
    
    def _enhance_brand_with_metadata(
        self, 
        brand: BrandRepresentation, 
        metadata: Dict[str, Any]
    ) -> BrandRepresentation:
        """Enhance brand representation with parsing metadata."""
        
        # Add metadata to confidence scores
        if not brand.confidence_scores:
            brand.confidence_scores = {}
        
        brand.confidence_scores.update({
            'document_word_count': metadata.get('word_count', 0),
            'document_sections_detected': metadata.get('detected_sections', {}),
            'parsing_method': metadata.get('source_type', 'unknown')
        })
        
        return brand


class BrandRetrievalUseCase:
    """
    Use case for retrieving and managing existing brand representations.
    """
    
    def __init__(self):
        """Initialize use case with repository dependencies."""
        self.brand_repository = BigQueryBrandRepository()
        self.logger = logging.getLogger(__name__)
    
    async def get_user_brand(self, user_id: str) -> Optional[BrandRepresentation]:
        """
        Get current brand representation for user.
        
        Args:
            user_id: ID of user
            
        Returns:
            Current BrandRepresentation or None if not found
        """
        self.logger.info(f"Retrieving brand for user {user_id}")
        
        try:
            brand = await self.brand_repository.get_brand_by_user(user_id)
            
            if brand:
                self.logger.info(f"Found brand {brand.brand_id} for user {user_id}")
            else:
                self.logger.info(f"No brand found for user {user_id}")
            
            return brand
            
        except Exception as e:
            self.logger.error(f"Error retrieving user brand: {str(e)}")
            raise
    
    async def get_brand_details(self, brand_id: str) -> Optional[BrandRepresentation]:
        """
        Get specific brand by ID.
        
        Args:
            brand_id: Brand identifier
            
        Returns:
            BrandRepresentation or None if not found
        """
        self.logger.info(f"Retrieving brand details for {brand_id}")
        
        try:
            brand = await self.brand_repository.get_brand_by_id(brand_id)
            
            if brand:
                self.logger.info(f"Found brand {brand_id}")
            else:
                self.logger.info(f"Brand {brand_id} not found")
            
            return brand
            
        except Exception as e:
            self.logger.error(f"Error retrieving brand details: {str(e)}")
            raise
    
    async def get_brand_evolution(self, brand_id: str) -> List[BrandRepresentation]:
        """
        Get brand version history showing evolution over time.
        
        Args:
            brand_id: Brand identifier
            
        Returns:
            List of BrandRepresentation versions in chronological order
        """
        self.logger.info(f"Retrieving brand evolution for {brand_id}")
        
        try:
            brand_history = await self.brand_repository.get_brand_history(brand_id)
            
            self.logger.info(f"Found {len(brand_history)} versions for brand {brand_id}")
            return brand_history
            
        except Exception as e:
            self.logger.error(f"Error retrieving brand evolution: {str(e)}")
            raise


class BrandLearningUseCase:
    """
    Use case for processing user feedback and learning events to improve brand accuracy.
    """
    
    def __init__(self):
        """Initialize use case with required dependencies."""
        self.brand_repository = BigQueryBrandRepository()
        self.learning_repository = BigQueryLearningRepository()
        self.brand_analyzer = BrandAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    async def process_user_feedback(
        self, 
        brand_id: str, 
        feedback_data: Dict[str, Any]
    ) -> BrandRepresentation:
        """
        Process user feedback to improve brand representation.
        
        Args:
            brand_id: ID of brand to update
            feedback_data: User feedback about brand accuracy
            
        Returns:
            Updated BrandRepresentation incorporating feedback
        """
        self.logger.info(f"Processing user feedback for brand {brand_id}")
        
        try:
            # Get current brand representation
            current_brand = await self.brand_repository.get_brand_by_id(brand_id)
            if not current_brand:
                raise ValueError(f"Brand {brand_id} not found")
            
            # Record learning event
            learning_event = BrandLearningEvent(
                brand_id=brand_id,
                event_type='user_feedback',
                event_data=feedback_data,
                processed=False,
                created_at=datetime.utcnow()
            )
            
            await self.learning_repository.save_learning_event(learning_event)
            
            # Apply feedback to brand representation
            updated_brand = await self.brand_analyzer.update_brand_with_feedback(
                current_brand, feedback_data
            )
            
            # Save updated brand
            final_brand = await self.brand_repository.update_brand(updated_brand)
            
            # Mark learning event as processed
            await self.learning_repository.mark_event_processed(learning_event.event_id)
            
            self.logger.info(f"Feedback processing complete. Brand version: {final_brand.version}")
            return final_brand
            
        except Exception as e:
            self.logger.error(f"Error processing user feedback: {str(e)}")
            raise
    
    async def record_content_interaction(
        self, 
        brand_id: str, 
        generation_id: str, 
        interaction_type: str, 
        interaction_data: Dict[str, Any]
    ) -> str:
        """
        Record user interaction with generated content for learning.
        
        Args:
            brand_id: ID of brand
            generation_id: ID of content generation
            interaction_type: Type of interaction (edit, regenerate, approve, etc.)
            interaction_data: Details of the interaction
            
        Returns:
            Learning event ID
        """
        self.logger.info(f"Recording content interaction for brand {brand_id}")
        
        try:
            # Create learning event
            learning_event = BrandLearningEvent(
                brand_id=brand_id,
                event_type=f'content_{interaction_type}',
                event_data={
                    'generation_id': generation_id,
                    'interaction_type': interaction_type,
                    **interaction_data
                },
                processed=False,
                created_at=datetime.utcnow()
            )
            
            event_id = await self.learning_repository.save_learning_event(learning_event)
            
            self.logger.info(f"Content interaction recorded. Event ID: {event_id}")
            return event_id
            
        except Exception as e:
            self.logger.error(f"Error recording content interaction: {str(e)}")
            raise
    
    async def analyze_learning_patterns(self, brand_id: str) -> Dict[str, Any]:
        """
        Analyze user patterns to identify brand improvement opportunities.
        
        Args:
            brand_id: ID of brand to analyze
            
        Returns:
            Dictionary containing learning insights and recommendations
        """
        self.logger.info(f"Analyzing learning patterns for brand {brand_id}")
        
        try:
            # Get learning patterns from repository
            patterns = await self.learning_repository.get_learning_patterns(brand_id)
            
            # Analyze patterns for insights
            insights = {
                'total_interactions': sum(pattern['count'] for pattern in patterns.values()),
                'most_common_interaction': max(patterns.keys(), key=lambda k: patterns[k]['count']) if patterns else None,
                'recent_activity_level': self._calculate_activity_level(patterns),
                'improvement_areas': self._identify_improvement_areas(patterns),
                'patterns': patterns
            }
            
            self.logger.info(f"Learning analysis complete. {insights['total_interactions']} total interactions analyzed")
            return insights
            
        except Exception as e:
            self.logger.error(f"Error analyzing learning patterns: {str(e)}")
            raise
    
    def _calculate_activity_level(self, patterns: Dict[str, Any]) -> str:
        """Calculate user activity level based on patterns."""
        if not patterns:
            return 'inactive'
        
        total_events = sum(pattern['count'] for pattern in patterns.values())
        avg_age = sum(pattern['avg_age_minutes'] for pattern in patterns.values()) / len(patterns)
        
        if total_events >= 10 and avg_age <= 1440:  # 10+ events in last day
            return 'very_active'
        elif total_events >= 5 and avg_age <= 10080:  # 5+ events in last week
            return 'active'
        elif total_events >= 2 and avg_age <= 43200:  # 2+ events in last month
            return 'moderate'
        else:
            return 'low'
    
    def _identify_improvement_areas(self, patterns: Dict[str, Any]) -> List[str]:
        """Identify areas for brand improvement based on interaction patterns."""
        improvements = []
        
        # High regeneration rate suggests brand accuracy issues
        if 'content_regenerate' in patterns:
            regenerate_rate = patterns['content_regenerate']['count']
            total_generations = sum(
                patterns.get(f'content_{action}', {}).get('count', 0) 
                for action in ['generate', 'regenerate']
            )
            if total_generations > 0 and regenerate_rate / total_generations > 0.3:
                improvements.append('brand_theme_accuracy')
        
        # Frequent edits suggest voice/tone misalignment
        if 'content_edit' in patterns and patterns['content_edit']['count'] > 5:
            improvements.append('voice_tone_alignment')
        
        # Lack of approvals suggests overall dissatisfaction
        if 'content_approve' in patterns:
            approve_rate = patterns['content_approve']['count']
            total_interactions = sum(pattern['count'] for pattern in patterns.values())
            if total_interactions > 0 and approve_rate / total_interactions < 0.2:
                improvements.append('overall_brand_representation')
        
        return improvements


class ContentGenerationUseCase:
    """
    Use case for one-click cross-surface professional content generation.
    
    Orchestrates the complete workflow for User Story 2: generating consistent
    content across CV summary, LinkedIn summary, and portfolio introduction
    with <30 second performance target.
    """
    
    def __init__(self):
        """Initialize use case with required dependencies."""
        self.content_generator = ContentGenerator()
        self.consistency_analyzer = ConsistencyAnalyzer()
        self.brand_repository = BigQueryBrandRepository()
        self.content_repository = BigQueryContentGenerationRepository()
        self.surface_repository = BigQueryProfessionalSurfaceRepository()
        self.learning_repository = BigQueryLearningRepository()
        self.logger = logging.getLogger(__name__)
    
    async def generate_cross_surface_content(
        self, 
        brand_id: str,
        surface_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        One-click generation across all professional surfaces.
        
        Args:
            brand_id: ID of brand representation to generate from
            surface_types: Optional list of surface types; defaults to all active
            
        Returns:
            Complete generation results with content, consistency analysis, and performance metrics
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Starting cross-surface content generation for brand {brand_id}")
        
        try:
            # Step 1: Retrieve brand representation
            brand = await self.brand_repository.get_brand_by_id(brand_id)
            if not brand:
                raise ValueError(f"Brand {brand_id} not found")
            
            # Step 2: Get target surfaces
            if surface_types:
                surfaces = []
                for surface_type in surface_types:
                    surface = await self.surface_repository.get_surface_by_type(surface_type)
                    if surface:
                        surfaces.append(surface)
            else:
                surfaces = await self.surface_repository.get_active_surfaces()
            
            if not surfaces:
                raise ValueError("No surfaces available for content generation")
            
            self.logger.info(f"Generating content for {len(surfaces)} surfaces: {[s.surface_type for s in surfaces]}")
            
            # Step 3: Archive existing active content for these surfaces
            await self._archive_existing_content(brand_id, [s.surface_id for s in surfaces])
            
            # Step 4: Generate content for all surfaces
            content_generations = await self.content_generator.generate_cross_surface_content(brand, surfaces)
            
            # Step 5: Validate cross-surface consistency
            consistency_result = await self.consistency_analyzer.validate_cross_surface_consistency(
                content_generations, brand
            )
            
            # Step 6: Store generated content
            stored_generations = []
            for generation in content_generations:
                generation_id = await self.content_repository.save_generation(generation)
                generation.generation_id = generation_id
                stored_generations.append(generation)
            
            # Step 7: Record learning event for generation
            await self._record_generation_event(brand_id, stored_generations, consistency_result)
            
            # Step 8: Calculate performance metrics
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            performance_metrics = self._calculate_performance_metrics(
                generation_time, len(surfaces), consistency_result
            )
            
            # Step 9: Compile comprehensive results
            generation_results = {
                'success': True,
                'brand_id': brand_id,
                'generated_content': [
                    {
                        'generation_id': gen.generation_id,
                        'surface_type': gen.generation_metadata.get('surface_type'),
                        'surface_id': gen.surface_id,
                        'content': gen.content,
                        'word_count': len(gen.content.split()),
                        'metadata': gen.generation_metadata
                    }
                    for gen in stored_generations
                ],
                'consistency_analysis': consistency_result,
                'performance_metrics': performance_metrics,
                'generation_timestamp': start_time.isoformat(),
                'surfaces_generated': len(surfaces),
                'meets_performance_target': generation_time <= 30.0
            }
            
            self.logger.info(f"Cross-surface generation complete in {generation_time:.2f}s with consistency score {consistency_result['overall_score']:.3f}")
            
            return generation_results
            
        except Exception as e:
            self.logger.error(f"Cross-surface content generation failed: {str(e)}")
            raise
    
    async def regenerate_surface_content(
        self, 
        brand_id: str, 
        surface_type: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Regenerate content for a specific surface with optional feedback.
        
        Args:
            brand_id: ID of brand representation
            surface_type: Type of surface to regenerate
            feedback: Optional user feedback for improvement
            
        Returns:
            Regeneration results with quality comparison
        """
        self.logger.info(f"Regenerating content for surface {surface_type} with feedback: {bool(feedback)}")
        
        try:
            # Get brand and surface
            brand = await self.brand_repository.get_brand_by_id(brand_id)
            if not brand:
                raise ValueError(f"Brand {brand_id} not found")
            
            surface = await self.surface_repository.get_surface_by_type(surface_type)
            if not surface:
                raise ValueError(f"Surface type {surface_type} not found")
            
            # Get existing content for comparison
            existing_generation = await self.content_repository.get_active_generation(brand_id, surface.surface_id)
            
            # Generate new content
            new_generation = await self.content_generator.regenerate_surface_content(
                brand, surface, feedback
            )
            
            # Store new generation
            generation_id = await self.content_repository.save_generation(new_generation)
            new_generation.generation_id = generation_id
            
            # Archive old generation if it exists
            if existing_generation:
                await self.content_repository.archive_generation(existing_generation.generation_id)
            
            # Compare quality if we have previous version
            comparison_result = None
            if existing_generation:
                comparison_result = await self.consistency_analyzer.compare_content_versions(
                    existing_generation, new_generation, brand
                )
            
            # Record learning event
            await self._record_regeneration_event(brand_id, new_generation, feedback, comparison_result)
            
            regeneration_results = {
                'success': True,
                'brand_id': brand_id,
                'surface_type': surface_type,
                'new_generation': {
                    'generation_id': new_generation.generation_id,
                    'content': new_generation.content,
                    'word_count': len(new_generation.content.split()),
                    'metadata': new_generation.generation_metadata
                },
                'quality_comparison': comparison_result,
                'feedback_provided': bool(feedback),
                'regeneration_timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Surface regeneration complete for {surface_type}")
            
            return regeneration_results
            
        except Exception as e:
            self.logger.error(f"Surface regeneration failed: {str(e)}")
            raise
    
    async def validate_brand_content_portfolio(self, brand_id: str) -> Dict[str, Any]:
        """
        Validate the complete content portfolio for a brand across all surfaces.
        
        Args:
            brand_id: ID of brand to validate
            
        Returns:
            Comprehensive portfolio validation results
        """
        self.logger.info(f"Validating brand content portfolio for brand {brand_id}")
        
        try:
            # Get brand and all content
            brand = await self.brand_repository.get_brand_by_id(brand_id)
            if not brand:
                raise ValueError(f"Brand {brand_id} not found")
            
            all_content = await self.content_repository.get_generations_by_brand(brand_id)
            
            # Filter to active content only
            active_content = [gen for gen in all_content if gen.is_active]
            
            if len(active_content) < 2:
                return {
                    'portfolio_complete': False,
                    'active_surfaces': len(active_content),
                    'message': 'Insufficient content for portfolio validation',
                    'validation_timestamp': datetime.utcnow().isoformat()
                }
            
            # Validate cross-surface consistency
            consistency_result = await self.consistency_analyzer.validate_cross_surface_consistency(
                active_content, brand
            )
            
            # Validate individual surface quality
            individual_validations = []
            for content in active_content:
                surface_validation = await self.consistency_analyzer.validate_single_surface_quality(
                    content, brand
                )
                individual_validations.append({
                    'surface_type': content.generation_metadata.get('surface_type'),
                    'generation_id': content.generation_id,
                    'quality_score': surface_validation['overall_quality'],
                    'quality_level': surface_validation['quality_level'],
                    'needs_improvement': surface_validation['needs_improvement']
                })
            
            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(
                consistency_result, individual_validations, active_content
            )
            
            portfolio_validation = {
                'portfolio_complete': True,
                'portfolio_quality': portfolio_metrics,
                'consistency_analysis': consistency_result,
                'individual_surface_quality': individual_validations,
                'active_surfaces': len(active_content),
                'surface_types': [content.generation_metadata.get('surface_type') for content in active_content],
                'validation_timestamp': datetime.utcnow().isoformat(),
                'requires_improvement': portfolio_metrics['overall_score'] < 0.7
            }
            
            self.logger.info(f"Portfolio validation complete. Overall score: {portfolio_metrics['overall_score']:.3f}")
            
            return portfolio_validation
            
        except Exception as e:
            self.logger.error(f"Portfolio validation failed: {str(e)}")
            raise
    
    async def _archive_existing_content(self, brand_id: str, surface_ids: List[str]) -> None:
        """Archive existing active content for specified surfaces."""
        
        for surface_id in surface_ids:
            existing_content = await self.content_repository.get_active_generation(brand_id, surface_id)
            if existing_content:
                await self.content_repository.archive_generation(existing_content.generation_id)
                self.logger.debug(f"Archived existing content for surface {surface_id}")
    
    async def _record_generation_event(
        self, 
        brand_id: str, 
        generations: List[ContentGeneration],
        consistency_result: Dict[str, Any]
    ) -> None:
        """Record learning event for content generation."""
        
        try:
            from domain.entities import BrandLearningEvent
            
            event = BrandLearningEvent(
                brand_id=brand_id,
                event_type='content_generation',
                event_data={
                    'generation_method': 'cross_surface_batch',
                    'surfaces_generated': len(generations),
                    'consistency_score': consistency_result['overall_score'],
                    'surface_types': [gen.generation_metadata.get('surface_type') for gen in generations],
                    'performance_target_met': consistency_result.get('meets_performance_target', False)
                },
                processed=False,
                created_at=datetime.utcnow()
            )
            
            await self.learning_repository.save_learning_event(event)
            
        except Exception as e:
            self.logger.warning(f"Failed to record generation event: {str(e)}")
    
    async def _record_regeneration_event(
        self, 
        brand_id: str, 
        generation: ContentGeneration,
        feedback: Optional[str],
        comparison_result: Optional[Dict[str, Any]]
    ) -> None:
        """Record learning event for content regeneration."""
        
        try:
            from domain.entities import BrandLearningEvent
            
            event_data = {
                'generation_method': 'regeneration',
                'surface_type': generation.generation_metadata.get('surface_type'),
                'feedback_provided': bool(feedback),
                'generation_id': generation.generation_id
            }
            
            if feedback:
                event_data['feedback_length'] = len(feedback)
            
            if comparison_result:
                event_data['quality_improved'] = comparison_result.get('is_improvement', False)
                event_data['improvement_score'] = comparison_result.get('improvement_score', 0.0)
            
            event = BrandLearningEvent(
                brand_id=brand_id,
                event_type='content_regeneration',
                event_data=event_data,
                processed=False,
                created_at=datetime.utcnow()
            )
            
            await self.learning_repository.save_learning_event(event)
            
        except Exception as e:
            self.logger.warning(f"Failed to record regeneration event: {str(e)}")
    
    def _calculate_performance_metrics(
        self, 
        generation_time: float, 
        surface_count: int,
        consistency_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate performance metrics for generation operation."""
        
        target_time = 30.0  # 30 second target
        
        return {
            'generation_time_seconds': generation_time,
            'target_time_seconds': target_time,
            'meets_performance_target': generation_time <= target_time,
            'time_per_surface_seconds': generation_time / max(surface_count, 1),
            'consistency_score': consistency_result['overall_score'],
            'performance_rating': self._get_performance_rating(generation_time, consistency_result['overall_score']),
            'surfaces_generated': surface_count
        }
    
    def _calculate_portfolio_metrics(
        self, 
        consistency_result: Dict[str, Any],
        individual_validations: List[Dict[str, Any]],
        active_content: List[ContentGeneration]
    ) -> Dict[str, Any]:
        """Calculate overall portfolio quality metrics."""
        
        # Average individual quality scores
        individual_scores = [validation['quality_score'] for validation in individual_validations]
        avg_individual_quality = sum(individual_scores) / len(individual_scores) if individual_scores else 0.0
        
        # Weight consistency and individual quality
        overall_score = (consistency_result['overall_score'] * 0.6) + (avg_individual_quality * 0.4)
        
        return {
            'overall_score': overall_score,
            'consistency_score': consistency_result['overall_score'],
            'avg_individual_quality': avg_individual_quality,
            'quality_level': self._get_quality_level(overall_score),
            'surfaces_needing_improvement': len([v for v in individual_validations if v['needs_improvement']]),
            'portfolio_completeness': len(active_content) >= 3  # CV, LinkedIn, Portfolio minimum
        }
    
    def _get_performance_rating(self, generation_time: float, consistency_score: float) -> str:
        """Get performance rating based on time and quality."""
        
        if generation_time <= 20 and consistency_score >= 0.9:
            return 'excellent'
        elif generation_time <= 30 and consistency_score >= 0.8:
            return 'good'
        elif generation_time <= 45 and consistency_score >= 0.7:
            return 'acceptable'
        else:
            return 'needs_improvement'
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level from numeric score."""
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.8:
            return 'good'
        elif score >= 0.7:
            return 'acceptable'
        else:
            return 'needs_improvement'