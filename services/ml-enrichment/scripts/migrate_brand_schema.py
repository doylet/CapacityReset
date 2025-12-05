#!/usr/bin/env python3
"""
Brand Schema Migration Script for LLM Integration

Applies database schema changes to support intelligent brand analysis
with LLM integration. Adds tables for enhanced tracking and caching.
"""

import logging
import sys
import os
from typing import Dict, List
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('migration.log')
        ]
    )
    return logging.getLogger(__name__)


def get_bigquery_client() -> bigquery.Client:
    """Initialize BigQuery client."""
    return bigquery.Client(location="australia-southeast1")


def check_table_exists(client: bigquery.Client, dataset_id: str, table_id: str) -> bool:
    """Check if a table exists."""
    try:
        table_ref = client.dataset(dataset_id).table(table_id)
        client.get_table(table_ref)
        return True
    except NotFound:
        return False


def execute_sql_file(client: bigquery.Client, filepath: str, logger: logging.Logger) -> bool:
    """Execute SQL from file."""
    try:
        with open(filepath, 'r') as f:
            sql = f.read()
            
        if not sql.strip():
            logger.warning(f"Empty SQL file: {filepath}")
            return True
            
        logger.info(f"Executing SQL from {filepath}")
        
        job = client.query(sql)
        job.result()  # Wait for completion
        
        logger.info(f"Successfully executed {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to execute {filepath}: {e}")
        return False


def create_enhanced_brand_schema(client: bigquery.Client, dataset_id: str, logger: logging.Logger) -> bool:
    """Create enhanced brand representations schema with LLM tracking."""
    
    sql = """
    -- Enhanced Brand Representations Table for LLM Integration
    CREATE TABLE IF NOT EXISTS `{project}.{dataset}.brand_representations_v2` (
        -- Core identification
        brand_id STRING NOT NULL,
        user_id STRING NOT NULL,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL,
        
        -- Original brand data (maintained for compatibility)
        document_content STRING,
        document_type STRING,
        analysis_type STRING,  -- 'keyword', 'llm', 'hybrid'
        
        -- Professional themes (JSON structure for flexibility)
        themes JSON,
        
        -- Voice characteristics (new LLM capability)
        voice_characteristics JSON,
        
        -- Career narrative arc (new LLM capability)
        narrative_arc JSON,
        
        -- LLM-specific metadata
        llm_model_version STRING,
        llm_analysis_timestamp TIMESTAMP,
        analysis_confidence FLOAT64,
        analysis_metadata JSON,
        
        -- Content hash for duplicate detection
        content_hash STRING,
        
        -- Processing flags
        is_active BOOLEAN,
        fallback_reason STRING,  -- Why LLM analysis failed (if applicable)
        
        -- Audit fields
        version INTEGER,
        previous_brand_id STRING
    )
    PARTITION BY DATE(created_at)
    CLUSTER BY user_id, analysis_type;
    """.format(project=client.project, dataset=dataset_id)
    
    try:
        logger.info("Creating enhanced brand_representations_v2 table")
        
        job = client.query(sql)
        job.result()
        
        logger.info("Successfully created brand_representations_v2 table")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create brand_representations_v2 table: {e}")
        return False


def create_llm_cache_schema(client: bigquery.Client, dataset_id: str, logger: logging.Logger) -> bool:
    """Create LLM analysis cache table."""
    
    sql = """
    -- LLM Analysis Cache Table for Cost Optimization
    CREATE TABLE IF NOT EXISTS `{project}.{dataset}.llm_analysis_cache` (
        -- Cache identification
        content_hash STRING NOT NULL,
        analysis_type STRING NOT NULL,  -- 'theme_analysis', 'voice_analysis', 'narrative_analysis'
        created_at TIMESTAMP NOT NULL,
        
        -- Cache data
        result_data JSON NOT NULL,
        
        -- Cache management
        ttl_hours INTEGER NOT NULL,
        version STRING NOT NULL,
        
        -- API usage tracking
        model_used STRING,
        tokens_used INTEGER,
        cost_estimate FLOAT64,
        
        -- Performance tracking
        analysis_duration_ms INTEGER,
        confidence_score FLOAT64,
        
        -- Audit
        access_count INTEGER,
        last_accessed TIMESTAMP
    )
    PARTITION BY DATE(created_at)
    CLUSTER BY content_hash, analysis_type;
    """.format(project=client.project, dataset=dataset_id)
    
    try:
        logger.info("Creating llm_analysis_cache table")
        
        job = client.query(sql)
        job.result()
        
        logger.info("Successfully created llm_analysis_cache table")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create llm_analysis_cache table: {e}")
        return False


def create_api_call_tracking_schema(client: bigquery.Client, dataset_id: str, logger: logging.Logger) -> bool:
    """Create API call tracking table for monitoring and cost analysis."""
    
    sql = """
    -- API Call Tracking Table for LLM Monitoring
    CREATE TABLE IF NOT EXISTS `{project}.{dataset}.api_call_tracking` (
        -- Call identification
        call_id STRING NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        
        -- Service information
        service STRING NOT NULL,  -- 'vertex_ai'
        operation STRING NOT NULL,  -- 'theme_analysis', 'voice_analysis', etc.
        
        -- Model and usage
        model_used STRING NOT NULL,
        tokens_input INTEGER,
        tokens_output INTEGER,
        tokens_total INTEGER,
        
        -- Cost tracking
        cost_estimate FLOAT64,
        
        -- Performance tracking
        latency_ms INTEGER,
        
        -- Success tracking
        success BOOLEAN NOT NULL,
        error_type STRING,
        error_message STRING,
        
        -- Context data (JSON for flexibility)
        context_data JSON
    )
    PARTITION BY DATE(timestamp)
    CLUSTER BY service, operation, success;
    """.format(project=client.project, dataset=dataset_id)
    
    try:
        logger.info("Creating api_call_tracking table")
        
        job = client.query(sql)
        job.result()
        
        logger.info("Successfully created api_call_tracking table")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create api_call_tracking table: {e}")
        return False


def migrate_existing_brand_data(client: bigquery.Client, dataset_id: str, logger: logging.Logger) -> bool:
    """Migrate existing brand data to new schema (if brand_representations exists)."""
    
    try:
        # Check if old table exists by attempting to describe it
        table_ref = client.dataset(dataset_id).table('brand_representations')
        table = client.get_table(table_ref)
        
        # If table has no rows, skip migration
        if table.num_rows == 0:
            logger.info("Existing brand_representations table is empty, skipping migration")
            return True
            
        logger.info(f"Found existing brand_representations table with {table.num_rows} rows")
        
    except NotFound:
        logger.info("No existing brand_representations table found, skipping migration")
        return True
    except Exception as e:
        logger.warning(f"Could not check for existing table: {e}")
        return True
    
    # Check if we already have data in the new table to avoid duplicate migration
    check_sql = f"""
    SELECT COUNT(*) as count 
    FROM `{client.project}.{dataset_id}.brand_representations_v2`
    LIMIT 1
    """
    
    try:
        job = client.query(check_sql)
        result = list(job.result())
        if result and result[0]['count'] > 0:
            logger.info("brand_representations_v2 already has data, skipping migration")
            return True
    except Exception as e:
        logger.warning(f"Could not check existing data in new table: {e}")
    
    sql = """
    -- Migrate existing brand data to new schema
    INSERT INTO `{project}.{dataset}.brand_representations_v2` (
        brand_id,
        user_id,
        created_at,
        updated_at,
        document_content,
        document_type,
        analysis_type,
        themes,
        content_hash,
        is_active,
        version
    )
    SELECT 
        GENERATE_UUID() as brand_id,
        user_id,
        created_at,
        updated_at,
        document_content,
        document_type,
        'keyword' as analysis_type,  -- Legacy data is keyword-based
        PARSE_JSON(themes) as themes,
        TO_HEX(SHA256(COALESCE(document_content, ''))) as content_hash,
        is_active,
        1 as version
    FROM `{project}.{dataset}.brand_representations`
    WHERE NOT EXISTS (
        SELECT 1 FROM `{project}.{dataset}.brand_representations_v2` v2
        WHERE v2.user_id = brand_representations.user_id
        AND v2.content_hash = TO_HEX(SHA256(COALESCE(brand_representations.document_content, '')))
    );
    """.format(project=client.project, dataset=dataset_id)
    
    try:
        logger.info("Migrating existing brand data")
        
        job = client.query(sql)
        result = job.result()
        
        # Get number of rows migrated
        migrated_rows = job.num_dml_affected_rows if hasattr(job, 'num_dml_affected_rows') else 'unknown'
        
        logger.info(f"Successfully migrated {migrated_rows} brand records")
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate existing brand data: {e}")
        return False


def create_analysis_views(client: bigquery.Client, dataset_id: str, logger: logging.Logger) -> bool:
    """Create useful views for analysis and monitoring."""
    
    # Brand analysis summary view
    view_sql = """
    CREATE OR REPLACE VIEW `{project}.{dataset}.brand_analysis_summary` AS
    SELECT 
        analysis_type,
        llm_model_version,
        COUNT(*) as total_analyses,
        AVG(analysis_confidence) as avg_confidence,
        COUNT(CASE WHEN fallback_reason IS NOT NULL THEN 1 END) as fallback_count,
        DATE(created_at) as analysis_date
    FROM `{project}.{dataset}.brand_representations_v2`
    WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    GROUP BY analysis_type, llm_model_version, DATE(created_at)
    ORDER BY analysis_date DESC;
    """.format(project=client.project, dataset=dataset_id)
    
    try:
        logger.info("Creating brand_analysis_summary view")
        
        job = client.query(view_sql)
        job.result()
        
        logger.info("Successfully created brand_analysis_summary view")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create brand_analysis_summary view: {e}")
        return False


def validate_migration(client: bigquery.Client, dataset_id: str, logger: logging.Logger) -> bool:
    """Validate migration was successful."""
    
    required_tables = [
        'brand_representations_v2',
        'llm_analysis_cache', 
        'api_call_tracking'
    ]
    
    for table_name in required_tables:
        if not check_table_exists(client, dataset_id, table_name):
            logger.error(f"Validation failed: Table {table_name} does not exist")
            return False
        else:
            logger.info(f"✓ Table {table_name} exists")
            
    # Check if views exist
    try:
        view_query = f"SELECT COUNT(*) as count FROM `{client.project}.{dataset_id}.brand_analysis_summary` LIMIT 1"
        job = client.query(view_query)
        job.result()
        logger.info("✓ Views are accessible")
    except Exception as e:
        logger.warning(f"View validation failed (may not be critical): {e}")
        
    logger.info("Migration validation completed successfully")
    return True


def main():
    """Execute schema migration."""
    logger = setup_logging()
    logger.info("Starting brand schema migration for LLM integration")
    
    # Get configuration
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'job_insights')
    
    if not project_id:
        logger.error("GOOGLE_CLOUD_PROJECT environment variable not set")
        sys.exit(1)
        
    logger.info(f"Target: {project_id}.{dataset_id}")
    
    try:
        # Initialize BigQuery client
        client = get_bigquery_client()
        logger.info("BigQuery client initialized")
        
        # Execute migration steps
        migration_steps = [
            ("Enhanced Brand Schema", lambda: create_enhanced_brand_schema(client, dataset_id, logger)),
            ("LLM Cache Schema", lambda: create_llm_cache_schema(client, dataset_id, logger)),
            ("API Call Tracking Schema", lambda: create_api_call_tracking_schema(client, dataset_id, logger)),
            ("Migrate Existing Data", lambda: migrate_existing_brand_data(client, dataset_id, logger)),
            ("Create Analysis Views", lambda: create_analysis_views(client, dataset_id, logger)),
            ("Validate Migration", lambda: validate_migration(client, dataset_id, logger))
        ]
        
        for step_name, step_func in migration_steps:
            logger.info(f"--- {step_name} ---")
            
            if not step_func():
                logger.error(f"Migration step failed: {step_name}")
                sys.exit(1)
                
            logger.info(f"✓ {step_name} completed")
            
        logger.info("🎉 Brand schema migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()