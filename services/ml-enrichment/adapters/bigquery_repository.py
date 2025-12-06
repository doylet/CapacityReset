"""
BigQuery Brand Adapters - Persistence implementation for Brand entities

Implements brand repository interfaces using BigQuery as the data source.
Follows hexagonal architecture with domain ports/adapters separation.
"""

import os
import sys
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
import json
import uuid
from google.cloud import bigquery

# Import domain entities and repository interfaces
sys.path.insert(0, '/Users/thomasdoyle/Daintree/frameworks/gcloud/CapacityReset/api/jobs-api')

if TYPE_CHECKING:
    from domain.entities import (  # type: ignore
        BrandRepresentation, ProfessionalTheme, ProfessionalSurface,
        ContentGeneration, BrandLearningEvent
    )
    from domain.repositories import (  # type: ignore
        BrandRepository, ContentGenerationRepository, LearningRepository,
        ProfessionalSurfaceRepository
    )
else:
    try:
        from domain.entities import (  # type: ignore
            BrandRepresentation, ProfessionalTheme, ProfessionalSurface,
            ContentGeneration, BrandLearningEvent
        )
        from domain.repositories import (  # type: ignore
            BrandRepository, ContentGenerationRepository, LearningRepository,
            ProfessionalSurfaceRepository
        )
    except ImportError as e:
        print(f"Warning: Could not import domain modules: {e}")
        # Define minimal classes for linting if imports fail
        class BrandRepresentation: pass  # type: ignore
        class ProfessionalTheme: pass  # type: ignore
        class ProfessionalSurface: pass  # type: ignore
        class ContentGeneration: pass  # type: ignore
        class BrandLearningEvent: pass  # type: ignore
        class BrandRepository: pass  # type: ignore
        class ContentGenerationRepository: pass  # type: ignore
        class LearningRepository: pass  # type: ignore
        class ProfessionalSurfaceRepository: pass  # type: ignore


# BigQuery configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "sylvan-replica-478802-p4")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "brightdata_jobs")
FULL_DATASET = f"{PROJECT_ID}.{DATASET_ID}"


class BigQueryBrandRepository(BrandRepository):
    """BigQuery implementation of BrandRepository."""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
    
    async def save_brand_representation(self, brand: BrandRepresentation) -> str:
        """Store brand representation, return brand_id."""
        if not brand.brand_id:
            brand.brand_id = str(uuid.uuid4())
        
        brand.updated_at = datetime.utcnow()
        if not brand.created_at:
            brand.created_at = brand.updated_at
        
        # Insert brand representation
        brand_query = f"""
        INSERT INTO `{FULL_DATASET}.brand_representations`
        (brand_id, user_id, source_document_url, linkedin_profile_url, 
         professional_themes, voice_characteristics, narrative_arc, 
         confidence_scores, created_at, updated_at, version)
        VALUES 
        (@brand_id, @user_id, @source_document_url, @linkedin_profile_url,
         @professional_themes, @voice_characteristics, @narrative_arc,
         @confidence_scores, @created_at, @updated_at, @version)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("brand_id", "STRING", brand.brand_id),
                bigquery.ScalarQueryParameter("user_id", "STRING", brand.user_id),
                bigquery.ScalarQueryParameter("source_document_url", "STRING", brand.source_document_url),
                bigquery.ScalarQueryParameter("linkedin_profile_url", "STRING", brand.linkedin_profile_url),
                bigquery.ScalarQueryParameter("professional_themes", "JSON", json.dumps(brand.professional_themes or [])),
                bigquery.ScalarQueryParameter("voice_characteristics", "JSON", json.dumps(brand.voice_characteristics or {})),
                bigquery.ScalarQueryParameter("narrative_arc", "JSON", json.dumps(brand.narrative_arc or {})),
                bigquery.ScalarQueryParameter("confidence_scores", "JSON", json.dumps(brand.confidence_scores or {})),
                bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", brand.created_at),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", brand.updated_at),
                bigquery.ScalarQueryParameter("version", "INTEGER", brand.version or 1),
            ]
        )
        
        query_job = self.client.query(brand_query, job_config=job_config)
        query_job.result()  # Wait for completion
        
        return brand.brand_id
    
    async def get_brand_by_id(self, brand_id: str) -> Optional[BrandRepresentation]:
        """Retrieve brand representation by ID."""
        query = f"""
        SELECT 
            brand_id, user_id, source_document_url, linkedin_profile_url,
            professional_themes, voice_characteristics, narrative_arc,
            confidence_scores, created_at, updated_at, version
        FROM `{FULL_DATASET}.brand_representations`
        WHERE brand_id = @brand_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("brand_id", "STRING", brand_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        for row in results:
            return BrandRepresentation(
                brand_id=row.brand_id,
                user_id=row.user_id,
                source_document_url=row.source_document_url,
                linkedin_profile_url=row.linkedin_profile_url,
                professional_themes=json.loads(row.professional_themes or "[]"),
                voice_characteristics=json.loads(row.voice_characteristics or "{}"),
                narrative_arc=json.loads(row.narrative_arc or "{}"),
                confidence_scores=json.loads(row.confidence_scores or "{}"),
                created_at=row.created_at,
                updated_at=row.updated_at,
                version=row.version
            )
        
        return None
    
    async def get_brand_by_user(self, user_id: str) -> Optional[BrandRepresentation]:
        """Retrieve user's current brand representation."""
        query = f"""
        SELECT 
            brand_id, user_id, source_document_url, linkedin_profile_url,
            professional_themes, voice_characteristics, narrative_arc,
            confidence_scores, created_at, updated_at, version
        FROM `{FULL_DATASET}.brand_representations`
        WHERE user_id = @user_id
        ORDER BY updated_at DESC
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        for row in results:
            return BrandRepresentation(
                brand_id=row.brand_id,
                user_id=row.user_id,
                source_document_url=row.source_document_url,
                linkedin_profile_url=row.linkedin_profile_url,
                professional_themes=json.loads(row.professional_themes or "[]"),
                voice_characteristics=json.loads(row.voice_characteristics or "{}"),
                narrative_arc=json.loads(row.narrative_arc or "{}"),
                confidence_scores=json.loads(row.confidence_scores or "{}"),
                created_at=row.created_at,
                updated_at=row.updated_at,
                version=row.version
            )
        
        return None
    
    async def update_brand_themes(self, brand_id: str, themes: List[ProfessionalTheme]) -> bool:
        """Update themes for existing brand."""
        themes_json = json.dumps([theme.__dict__ if hasattr(theme, '__dict__') else theme for theme in themes])
        
        query = f"""
        UPDATE `{FULL_DATASET}.brand_representations`
        SET 
            professional_themes = @themes,
            updated_at = @updated_at
        WHERE brand_id = @brand_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("brand_id", "STRING", brand_id),
                bigquery.ScalarQueryParameter("themes", "JSON", themes_json),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", datetime.utcnow()),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        result = query_job.result()
        
        return query_job.num_dml_affected_rows > 0
    
    async def update_brand(self, brand: BrandRepresentation) -> BrandRepresentation:
        """Update an existing brand representation."""
        brand.updated_at = datetime.utcnow()
        
        query = f"""
        UPDATE `{FULL_DATASET}.brand_representations`
        SET 
            source_document_url = @source_document_url,
            linkedin_profile_url = @linkedin_profile_url,
            professional_themes = @professional_themes,
            voice_characteristics = @voice_characteristics,
            narrative_arc = @narrative_arc,
            confidence_scores = @confidence_scores,
            updated_at = @updated_at,
            version = @version
        WHERE brand_id = @brand_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("brand_id", "STRING", brand.brand_id),
                bigquery.ScalarQueryParameter("source_document_url", "STRING", brand.source_document_url),
                bigquery.ScalarQueryParameter("linkedin_profile_url", "STRING", brand.linkedin_profile_url),
                bigquery.ScalarQueryParameter("professional_themes", "JSON", json.dumps(brand.professional_themes or [])),
                bigquery.ScalarQueryParameter("voice_characteristics", "JSON", json.dumps(brand.voice_characteristics or {})),
                bigquery.ScalarQueryParameter("narrative_arc", "JSON", json.dumps(brand.narrative_arc or {})),
                bigquery.ScalarQueryParameter("confidence_scores", "JSON", json.dumps(brand.confidence_scores or {})),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", brand.updated_at),
                bigquery.ScalarQueryParameter("version", "INTEGER", (brand.version or 0) + 1),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        result = query_job.result()
        
        if query_job.num_dml_affected_rows > 0:
            brand.version = (brand.version or 0) + 1
            return brand
        
        raise ValueError(f"Brand {brand.brand_id} not found for update")
    
    async def get_brand_history(self, brand_id: str) -> List[BrandRepresentation]:
        """Retrieve brand evolution history."""
        query = f"""
        SELECT 
            brand_id, user_id, source_document_url, linkedin_profile_url,
            professional_themes, voice_characteristics, narrative_arc,
            confidence_scores, created_at, updated_at, version
        FROM `{FULL_DATASET}.brand_representations`
        WHERE brand_id = @brand_id
        ORDER BY version ASC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("brand_id", "STRING", brand_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        brands = []
        for row in results:
            brands.append(BrandRepresentation(
                brand_id=row.brand_id,
                user_id=row.user_id,
                source_document_url=row.source_document_url,
                linkedin_profile_url=row.linkedin_profile_url,
                professional_themes=json.loads(row.professional_themes or "[]"),
                voice_characteristics=json.loads(row.voice_characteristics or "{}"),
                narrative_arc=json.loads(row.narrative_arc or "{}"),
                confidence_scores=json.loads(row.confidence_scores or "{}"),
                created_at=row.created_at,
                updated_at=row.updated_at,
                version=row.version
            ))
        
        return brands


class BigQueryContentGenerationRepository(ContentGenerationRepository):
    """BigQuery implementation of ContentGenerationRepository."""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
    
    async def save_generation(self, generation: ContentGeneration) -> str:
        """Store generated content, return generation_id."""
        if not generation.generation_id:
            generation.generation_id = str(uuid.uuid4())
        
        generation.created_at = datetime.utcnow()
        
        query = f"""
        INSERT INTO `{FULL_DATASET}.content_generations`
        (generation_id, brand_id, surface_id, content, generation_metadata,
         is_active, user_edited, user_feedback, created_at)
        VALUES 
        (@generation_id, @brand_id, @surface_id, @content, @generation_metadata,
         @is_active, @user_edited, @user_feedback, @created_at)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("generation_id", "STRING", generation.generation_id),
                bigquery.ScalarQueryParameter("brand_id", "STRING", generation.brand_id),
                bigquery.ScalarQueryParameter("surface_id", "STRING", generation.surface_id),
                bigquery.ScalarQueryParameter("content", "STRING", generation.content),
                bigquery.ScalarQueryParameter("generation_metadata", "JSON", json.dumps(generation.generation_metadata or {})),
                bigquery.ScalarQueryParameter("is_active", "BOOLEAN", generation.is_active),
                bigquery.ScalarQueryParameter("user_edited", "BOOLEAN", generation.user_edited or False),
                bigquery.ScalarQueryParameter("user_feedback", "STRING", generation.user_feedback),
                bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", generation.created_at),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()  # Wait for completion
        
        return generation.generation_id
    
    async def get_generation_by_id(self, generation_id: str) -> Optional[ContentGeneration]:
        """Retrieve content generation by ID."""
        query = f"""
        SELECT 
            generation_id, brand_id, surface_id, content, generation_metadata,
            is_active, user_edited, user_feedback, created_at
        FROM `{FULL_DATASET}.content_generations`
        WHERE generation_id = @generation_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("generation_id", "STRING", generation_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        for row in results:
            return ContentGeneration(
                generation_id=row.generation_id,
                brand_id=row.brand_id,
                surface_id=row.surface_id,
                content=row.content,
                generation_metadata=json.loads(row.generation_metadata or "{}"),
                is_active=row.is_active,
                user_edited=row.user_edited,
                user_feedback=row.user_feedback,
                created_at=row.created_at
            )
        
        return None
    
    async def get_generations_by_brand(self, brand_id: str) -> List[ContentGeneration]:
        """Retrieve all content for a brand."""
        query = f"""
        SELECT 
            generation_id, brand_id, surface_id, content, generation_metadata,
            is_active, user_edited, user_feedback, created_at
        FROM `{FULL_DATASET}.content_generations`
        WHERE brand_id = @brand_id
        ORDER BY created_at DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("brand_id", "STRING", brand_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        generations = []
        for row in results:
            generations.append(ContentGeneration(
                generation_id=row.generation_id,
                brand_id=row.brand_id,
                surface_id=row.surface_id,
                content=row.content,
                generation_metadata=json.loads(row.generation_metadata or "{}"),
                is_active=row.is_active,
                user_edited=row.user_edited,
                user_feedback=row.user_feedback,
                created_at=row.created_at
            ))
        
        return generations
    
    async def get_active_generation(self, brand_id: str, surface_id: str) -> Optional[ContentGeneration]:
        """Get current active content for surface."""
        query = f"""
        SELECT 
            generation_id, brand_id, surface_id, content, generation_metadata,
            is_active, user_edited, user_feedback, created_at
        FROM `{FULL_DATASET}.content_generations`
        WHERE brand_id = @brand_id 
          AND surface_id = @surface_id 
          AND is_active = TRUE
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("brand_id", "STRING", brand_id),
                bigquery.ScalarQueryParameter("surface_id", "STRING", surface_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        for row in results:
            return ContentGeneration(
                generation_id=row.generation_id,
                brand_id=row.brand_id,
                surface_id=row.surface_id,
                content=row.content,
                generation_metadata=json.loads(row.generation_metadata or "{}"),
                is_active=row.is_active,
                user_edited=row.user_edited,
                user_feedback=row.user_feedback,
                created_at=row.created_at
            )
        
        return None
    
    async def archive_generation(self, generation_id: str) -> bool:
        """Archive old generation when regenerating."""
        query = f"""
        UPDATE `{FULL_DATASET}.content_generations`
        SET is_active = FALSE
        WHERE generation_id = @generation_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("generation_id", "STRING", generation_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        result = query_job.result()
        
        return query_job.num_dml_affected_rows > 0
    
    async def update_generation(self, generation: ContentGeneration) -> ContentGeneration:
        """Update an existing content generation."""
        query = f"""
        UPDATE `{FULL_DATASET}.content_generations`
        SET 
            content = @content,
            generation_metadata = @generation_metadata,
            is_active = @is_active,
            user_edited = @user_edited,
            user_feedback = @user_feedback
        WHERE generation_id = @generation_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("generation_id", "STRING", generation.generation_id),
                bigquery.ScalarQueryParameter("content", "STRING", generation.content),
                bigquery.ScalarQueryParameter("generation_metadata", "JSON", json.dumps(generation.generation_metadata or {})),
                bigquery.ScalarQueryParameter("is_active", "BOOLEAN", generation.is_active),
                bigquery.ScalarQueryParameter("user_edited", "BOOLEAN", generation.user_edited or False),
                bigquery.ScalarQueryParameter("user_feedback", "STRING", generation.user_feedback),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        result = query_job.result()
        
        if query_job.num_dml_affected_rows > 0:
            return generation
        
        raise ValueError(f"Generation {generation.generation_id} not found for update")


class BigQueryLearningRepository(LearningRepository):
    """BigQuery implementation of LearningRepository."""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
    
    async def save_learning_event(self, event: BrandLearningEvent) -> str:
        """Store user interaction event."""
        if not event.event_id:
            event.event_id = str(uuid.uuid4())
        
        event.created_at = datetime.utcnow()
        
        query = f"""
        INSERT INTO `{FULL_DATASET}.brand_learning_events`
        (event_id, brand_id, event_type, event_data, processed, created_at)
        VALUES 
        (@event_id, @brand_id, @event_type, @event_data, @processed, @created_at)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("event_id", "STRING", event.event_id),
                bigquery.ScalarQueryParameter("brand_id", "STRING", event.brand_id),
                bigquery.ScalarQueryParameter("event_type", "STRING", event.event_type),
                bigquery.ScalarQueryParameter("event_data", "JSON", json.dumps(event.event_data or {})),
                bigquery.ScalarQueryParameter("processed", "BOOLEAN", event.processed or False),
                bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", event.created_at),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()  # Wait for completion
        
        return event.event_id
    
    async def get_unprocessed_events(self, brand_id: str) -> List[BrandLearningEvent]:
        """Retrieve events needing integration."""
        query = f"""
        SELECT 
            event_id, brand_id, event_type, event_data, processed, created_at
        FROM `{FULL_DATASET}.brand_learning_events`
        WHERE brand_id = @brand_id AND processed = FALSE
        ORDER BY created_at ASC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("brand_id", "STRING", brand_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        events = []
        for row in results:
            events.append(BrandLearningEvent(
                event_id=row.event_id,
                brand_id=row.brand_id,
                event_type=row.event_type,
                event_data=json.loads(row.event_data or "{}"),
                processed=row.processed,
                created_at=row.created_at
            ))
        
        return events
    
    async def mark_event_processed(self, event_id: str) -> bool:
        """Mark event as integrated into learning."""
        query = f"""
        UPDATE `{FULL_DATASET}.brand_learning_events`
        SET processed = TRUE
        WHERE event_id = @event_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("event_id", "STRING", event_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        result = query_job.result()
        
        return query_job.num_dml_affected_rows > 0
    
    async def get_learning_patterns(self, brand_id: str) -> Dict[str, Any]:
        """Analyze user patterns for improvement."""
        query = f"""
        SELECT 
            event_type,
            COUNT(*) as event_count,
            AVG(TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, MINUTE)) as avg_age_minutes,
            ARRAY_AGG(event_data ORDER BY created_at DESC LIMIT 10) as recent_events
        FROM `{FULL_DATASET}.brand_learning_events`
        WHERE brand_id = @brand_id
        GROUP BY event_type
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("brand_id", "STRING", brand_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        patterns = {}
        for row in results:
            patterns[row.event_type] = {
                'count': row.event_count,
                'avg_age_minutes': row.avg_age_minutes,
                'recent_events': [json.loads(event) for event in row.recent_events]
            }
        
        return patterns


class BigQueryProfessionalSurfaceRepository(ProfessionalSurfaceRepository):
    """BigQuery implementation of ProfessionalSurfaceRepository."""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
    
    async def get_all_surfaces(self) -> List[ProfessionalSurface]:
        """Get all available professional surfaces."""
        query = f"""
        SELECT 
            surface_id, surface_name, surface_type, description,
            requirements, is_active, display_order
        FROM `{FULL_DATASET}.professional_surfaces`
        ORDER BY display_order
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        surfaces = []
        for row in results:
            surfaces.append(ProfessionalSurface(
                surface_id=row.surface_id,
                surface_name=row.surface_name,
                surface_type=row.surface_type,
                description=row.description,
                requirements=json.loads(row.requirements or "{}"),
                is_active=row.is_active,
                display_order=row.display_order
            ))
        
        return surfaces
    
    async def get_surface_by_id(self, surface_id: str) -> Optional[ProfessionalSurface]:
        """Get a specific surface by ID."""
        query = f"""
        SELECT 
            surface_id, surface_name, surface_type, description,
            requirements, is_active, display_order
        FROM `{FULL_DATASET}.professional_surfaces`
        WHERE surface_id = @surface_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("surface_id", "STRING", surface_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        for row in results:
            return ProfessionalSurface(
                surface_id=row.surface_id,
                surface_name=row.surface_name,
                surface_type=row.surface_type,
                description=row.description,
                requirements=json.loads(row.requirements or "{}"),
                is_active=row.is_active,
                display_order=row.display_order
            )
        
        return None
    
    async def get_surface_by_type(self, surface_type: str) -> Optional[ProfessionalSurface]:
        """Get a specific surface by type."""
        query = f"""
        SELECT 
            surface_id, surface_name, surface_type, description,
            requirements, is_active, display_order
        FROM `{FULL_DATASET}.professional_surfaces`
        WHERE surface_type = @surface_type AND is_active = TRUE
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("surface_type", "STRING", surface_type)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        for row in results:
            return ProfessionalSurface(
                surface_id=row.surface_id,
                surface_name=row.surface_name,
                surface_type=row.surface_type,
                description=row.description,
                requirements=json.loads(row.requirements or "{}"),
                is_active=row.is_active,
                display_order=row.display_order
            )
        
        return None
    
    async def get_active_surfaces(self) -> List[ProfessionalSurface]:
        """Get all active surfaces available for generation."""
        query = f"""
        SELECT 
            surface_id, surface_name, surface_type, description,
            requirements, is_active, display_order
        FROM `{FULL_DATASET}.professional_surfaces`
        WHERE is_active = TRUE
        ORDER BY display_order
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        surfaces = []
        for row in results:
            surfaces.append(ProfessionalSurface(
                surface_id=row.surface_id,
                surface_name=row.surface_name,
                surface_type=row.surface_type,
                description=row.description,
                requirements=json.loads(row.requirements or "{}"),
                is_active=row.is_active,
                display_order=row.display_order
            ))
        
        return surfaces