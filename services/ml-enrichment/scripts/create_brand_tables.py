"""
Create BigQuery tables for AI Brand Roadmap feature.

This script creates:
1. brand_representations - Core professional identity storage
2. professional_themes - Extracted career themes and strengths
3. professional_surfaces - Target platforms for content generation
4. content_generations - Generated branded content
5. brand_learning_events - User feedback for continuous improvement
6. brand_theme_associations - Many-to-many brand-theme relationships
"""

from google.cloud import bigquery
import os


def create_brand_tables(project_id: str = None):
    """Create all brand-related tables with proper schemas."""
    
    if project_id is None:
        project_id = os.environ.get("GCP_PROJECT_ID", "sylvan-replica-478802-p4")
    
    client = bigquery.Client(project=project_id)
    dataset_id = f"{project_id}.brightdata_jobs"
    
    print(f"Creating brand tables in dataset: {dataset_id}")
    
    # 1. Brand Representations table
    brand_table_id = f"{dataset_id}.brand_representations"
    brand_schema = [
        bigquery.SchemaField("brand_id", "STRING", mode="REQUIRED", 
                            description="Unique identifier for this brand"),
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED", 
                            description="Owner reference"),
        bigquery.SchemaField("source_document_url", "STRING", mode="REQUIRED", 
                            description="GCS path to uploaded CV/resume"),
        bigquery.SchemaField("linkedin_profile_url", "STRING", mode="NULLABLE", 
                            description="Optional LinkedIn profile data"),
        bigquery.SchemaField("professional_themes", "JSON", mode="REQUIRED", 
                            description="Array of extracted career themes and strengths"),
        bigquery.SchemaField("voice_characteristics", "JSON", mode="REQUIRED", 
                            description="Tone, style, and communication patterns"),
        bigquery.SchemaField("narrative_arc", "JSON", mode="REQUIRED", 
                            description="Career story structure and key messages"),
        bigquery.SchemaField("confidence_scores", "JSON", mode="REQUIRED", 
                            description="Analysis confidence by theme/characteristic"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", 
                            description="Initial analysis timestamp"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED", 
                            description="Last modification time"),
        bigquery.SchemaField("version", "INTEGER", mode="REQUIRED", 
                            description="Brand representation version for evolution tracking"),
    ]
    
    brand_table = bigquery.Table(brand_table_id, schema=brand_schema)
    brand_table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="created_at"
    )
    brand_table.clustering_fields = ["user_id"]
    
    brand_table = client.create_table(brand_table, exists_ok=True)
    print(f"✓ Created table {brand_table_id}")
    
    # 2. Professional Themes table
    themes_table_id = f"{dataset_id}.professional_themes"
    themes_schema = [
        bigquery.SchemaField("theme_id", "STRING", mode="REQUIRED", 
                            description="Unique identifier for this theme"),
        bigquery.SchemaField("theme_name", "STRING", mode="REQUIRED", 
                            description="Human-readable theme label"),
        bigquery.SchemaField("theme_category", "STRING", mode="REQUIRED", 
                            description="Category: skill, industry, role, value_proposition, achievement"),
        bigquery.SchemaField("description", "STRING", mode="REQUIRED", 
                            description="Detailed theme explanation"),
        bigquery.SchemaField("keywords", "STRING", mode="REPEATED", 
                            description="Associated terms and phrases"),
        bigquery.SchemaField("confidence_score", "FLOAT64", mode="REQUIRED", 
                            description="Extraction confidence (0.0-1.0)"),
        bigquery.SchemaField("source_evidence", "STRING", mode="REQUIRED", 
                            description="Document text supporting this theme"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", 
                            description="Theme extraction time"),
    ]
    
    themes_table = bigquery.Table(themes_table_id, schema=themes_schema)
    themes_table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="created_at"
    )
    themes_table.clustering_fields = ["theme_category"]
    
    themes_table = client.create_table(themes_table, exists_ok=True)
    print(f"✓ Created table {themes_table_id}")
    
    # 3. Professional Surfaces table
    surfaces_table_id = f"{dataset_id}.professional_surfaces"
    surfaces_schema = [
        bigquery.SchemaField("surface_id", "STRING", mode="REQUIRED", 
                            description="Unique identifier for this surface"),
        bigquery.SchemaField("surface_type", "STRING", mode="REQUIRED", 
                            description="Platform type: cv_summary, linkedin_summary, portfolio_intro"),
        bigquery.SchemaField("surface_name", "STRING", mode="REQUIRED", 
                            description="Display name"),
        bigquery.SchemaField("content_requirements", "JSON", mode="REQUIRED", 
                            description="Character limits, tone guidelines, structure rules"),
        bigquery.SchemaField("template_structure", "STRING", mode="REQUIRED", 
                            description="Generation template with placeholders"),
        bigquery.SchemaField("validation_rules", "JSON", mode="REQUIRED", 
                            description="Content validation criteria"),
        bigquery.SchemaField("active", "BOOLEAN", mode="REQUIRED", 
                            description="Whether surface is available for generation"),
    ]
    
    surfaces_table = bigquery.Table(surfaces_table_id, schema=surfaces_schema)
    surfaces_table.clustering_fields = ["surface_type"]
    
    surfaces_table = client.create_table(surfaces_table, exists_ok=True)
    print(f"✓ Created table {surfaces_table_id}")
    
    # 4. Content Generations table
    content_table_id = f"{dataset_id}.content_generations"
    content_schema = [
        bigquery.SchemaField("generation_id", "STRING", mode="REQUIRED", 
                            description="Unique identifier for this generation"),
        bigquery.SchemaField("brand_id", "STRING", mode="REQUIRED", 
                            description="Source brand representation"),
        bigquery.SchemaField("surface_id", "STRING", mode="REQUIRED", 
                            description="Target surface reference"),
        bigquery.SchemaField("content_text", "STRING", mode="REQUIRED", 
                            description="Generated content"),
        bigquery.SchemaField("generation_timestamp", "TIMESTAMP", mode="REQUIRED", 
                            description="Creation time"),
        bigquery.SchemaField("generation_version", "INTEGER", mode="REQUIRED", 
                            description="Version number for regenerations"),
        bigquery.SchemaField("generation_prompt", "STRING", mode="REQUIRED", 
                            description="LLM prompt used for generation"),
        bigquery.SchemaField("consistency_score", "FLOAT64", mode="NULLABLE", 
                            description="Cross-surface consistency rating"),
        bigquery.SchemaField("user_satisfaction_rating", "INTEGER", mode="NULLABLE", 
                            description="User feedback score (1-5)"),
        bigquery.SchemaField("edit_count", "INTEGER", mode="REQUIRED", 
                            description="Number of user modifications"),
        bigquery.SchemaField("word_count", "INTEGER", mode="REQUIRED", 
                            description="Content length"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED", 
                            description="Status: draft, active, archived"),
    ]
    
    content_table = bigquery.Table(content_table_id, schema=content_schema)
    content_table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="generation_timestamp"
    )
    content_table.clustering_fields = ["brand_id", "surface_id"]
    
    content_table = client.create_table(content_table, exists_ok=True)
    print(f"✓ Created table {content_table_id}")
    
    # 5. Brand Learning Events table
    events_table_id = f"{dataset_id}.brand_learning_events"
    events_schema = [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED", 
                            description="Unique identifier for this event"),
        bigquery.SchemaField("brand_id", "STRING", mode="REQUIRED", 
                            description="Associated brand representation"),
        bigquery.SchemaField("event_type", "STRING", mode="REQUIRED", 
                            description="Event type: edit, regeneration, preference_change, rating"),
        bigquery.SchemaField("event_timestamp", "TIMESTAMP", mode="REQUIRED", 
                            description="Interaction time"),
        bigquery.SchemaField("surface_id", "STRING", mode="NULLABLE", 
                            description="Related surface if applicable"),
        bigquery.SchemaField("theme_id", "STRING", mode="NULLABLE", 
                            description="Related theme if applicable"),
        bigquery.SchemaField("event_data", "JSON", mode="REQUIRED", 
                            description="Type-specific data (edits, feedback, preferences)"),
        bigquery.SchemaField("user_feedback", "STRING", mode="NULLABLE", 
                            description="Optional user explanation"),
        bigquery.SchemaField("processed", "BOOLEAN", mode="REQUIRED", 
                            description="Whether event has been integrated into learning"),
    ]
    
    events_table = bigquery.Table(events_table_id, schema=events_schema)
    events_table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="event_timestamp"
    )
    events_table.clustering_fields = ["brand_id", "event_type"]
    
    events_table = client.create_table(events_table, exists_ok=True)
    print(f"✓ Created table {events_table_id}")
    
    # 6. Brand Theme Associations table
    associations_table_id = f"{dataset_id}.brand_theme_associations"
    associations_schema = [
        bigquery.SchemaField("brand_id", "STRING", mode="REQUIRED", 
                            description="Brand reference"),
        bigquery.SchemaField("theme_id", "STRING", mode="REQUIRED", 
                            description="Theme reference"),
        bigquery.SchemaField("relevance_score", "FLOAT64", mode="REQUIRED", 
                            description="Theme relevance to this brand (0.0-1.0)"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", 
                            description="Association creation time"),
    ]
    
    associations_table = bigquery.Table(associations_table_id, schema=associations_schema)
    associations_table.clustering_fields = ["brand_id"]
    
    associations_table = client.create_table(associations_table, exists_ok=True)
    print(f"✓ Created table {associations_table_id}")
    
    print("\n✅ All brand tables created successfully!")
    print("\nAI Brand Roadmap Architecture:")
    print("- brand_representations: Core professional identity storage")
    print("- professional_themes: Extracted career themes and strengths")
    print("- professional_surfaces: Target platforms (CV, LinkedIn, Portfolio)")
    print("- content_generations: Generated branded content with versioning")
    print("- brand_learning_events: User feedback for continuous improvement")
    print("- brand_theme_associations: Brand-theme relationships")
    print("\nPerformance targets:")
    print("- Brand analysis: <10 minutes")
    print("- Content generation: <30 seconds")
    print("- Cross-surface consistency: >90%")


def insert_default_surfaces(project_id: str = None):
    """Insert default professional surfaces into the database."""
    
    if project_id is None:
        project_id = os.environ.get("GCP_PROJECT_ID", "sylvan-replica-478802-p4")
    
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.brightdata_jobs.professional_surfaces"
    
    surfaces = [
        {
            "surface_id": "surf-cv-summary-001",
            "surface_type": "cv_summary",
            "surface_name": "CV Professional Summary",
            "content_requirements": {
                "min_length": 100,
                "max_length": 300,
                "tone_guidelines": ["professional", "achievement-focused"],
                "structure_requirements": ["opening_statement", "key_achievements", "value_proposition"]
            },
            "template_structure": "A results-driven {career_focus} professional...",
            "validation_rules": {
                "required_elements": ["career_focus", "experience_indication", "value_statement"],
                "forbidden_phrases": ["I am", "My name is"]
            },
            "active": True
        },
        {
            "surface_id": "surf-linkedin-summary-001",
            "surface_type": "linkedin_summary",
            "surface_name": "LinkedIn Summary",
            "content_requirements": {
                "min_length": 150,
                "max_length": 500,
                "tone_guidelines": ["conversational", "professional", "authentic"],
                "structure_requirements": ["hook", "story", "expertise", "call_to_action"]
            },
            "template_structure": "{hook_statement}\n\n{career_story}...",
            "validation_rules": {
                "required_elements": ["personal_hook", "expertise_areas", "call_to_action"],
                "forbidden_phrases": [],
                "encourages_first_person": True
            },
            "active": True
        },
        {
            "surface_id": "surf-portfolio-intro-001",
            "surface_type": "portfolio_intro",
            "surface_name": "Portfolio Introduction",
            "content_requirements": {
                "min_length": 100,
                "max_length": 250,
                "tone_guidelines": ["creative", "professional", "engaging"],
                "structure_requirements": ["introduction", "expertise", "value_statement"]
            },
            "template_structure": "Hello, I am {professional_title}...",
            "validation_rules": {
                "required_elements": ["professional_identity", "expertise_overview", "portfolio_invitation"],
                "forbidden_phrases": []
            },
            "active": True
        }
    ]
    
    # Convert to JSON-serializable format
    import json
    rows_to_insert = []
    for surface in surfaces:
        row = {
            "surface_id": surface["surface_id"],
            "surface_type": surface["surface_type"],
            "surface_name": surface["surface_name"],
            "content_requirements": json.dumps(surface["content_requirements"]),
            "template_structure": surface["template_structure"],
            "validation_rules": json.dumps(surface["validation_rules"]),
            "active": surface["active"]
        }
        rows_to_insert.append(row)
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print(f"Errors inserting default surfaces: {errors}")
    else:
        print(f"✓ Inserted {len(rows_to_insert)} default professional surfaces")


if __name__ == "__main__":
    import sys
    
    project_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    create_brand_tables(project_id)
    
    # Optionally insert default surfaces
    if len(sys.argv) > 2 and sys.argv[2] == "--with-data":
        insert_default_surfaces(project_id)
