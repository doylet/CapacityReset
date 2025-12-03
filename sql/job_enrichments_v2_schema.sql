-- Job Enrichments V2 Schema Extension
-- Extends job_enrichments table with model version tracking fields
-- 
-- This schema supports:
-- - Model version identification for all enrichments
-- - Backward compatibility with legacy enrichments
-- - Query filtering by version for re-enrichment workflows
--
-- Version: 2.0
-- Date: 2025-12-03

-- Create extended job_enrichments table if it doesn't exist
-- Uses IF NOT EXISTS pattern for idempotency
CREATE TABLE IF NOT EXISTS `brightdata_jobs.job_enrichments` (
    -- Primary key
    enrichment_id STRING NOT NULL,
    
    -- Foreign key reference to job_postings
    job_posting_id STRING NOT NULL,
    
    -- Enrichment type (polymorphic discriminator)
    -- Values: skills_extraction, embeddings, clustering, section_classification
    enrichment_type STRING NOT NULL,
    
    -- Status tracking
    status STRING NOT NULL,  -- pending, processing, success, failed
    
    -- Version tracking (NEW)
    model_id STRING,         -- e.g., "skills_extractor"
    model_version STRING,    -- e.g., "v4.0-unified-config-enhanced"
    enrichment_version STRING,  -- Denormalized: "{model_id}_{model_version}" for query performance
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    
    -- Flexible metadata storage
    metadata JSON,           -- Type-specific metadata (JSON format)
    
    -- Error handling
    error_message STRING,
    
    -- Processing metrics
    processing_time_ms INT64,
    retry_count INT64 DEFAULT 0
);

-- Create composite index for version-based queries
-- Allows efficient filtering by enrichment type and version
CREATE INDEX IF NOT EXISTS idx_enrichments_type_version
ON `brightdata_jobs.job_enrichments` (enrichment_type, enrichment_version);

-- Create index for job lookup with version filtering
CREATE INDEX IF NOT EXISTS idx_enrichments_job_type_version
ON `brightdata_jobs.job_enrichments` (job_posting_id, enrichment_type, enrichment_version);

-- Create index for status-based queries
CREATE INDEX IF NOT EXISTS idx_enrichments_status
ON `brightdata_jobs.job_enrichments` (status, enrichment_type);

-- Views for common query patterns

-- View: Jobs needing re-enrichment (missing specific version)
-- Usage: Query this view with @current_version parameter
CREATE OR REPLACE VIEW `brightdata_jobs.v_jobs_needing_enrichment` AS
SELECT 
    jp.job_posting_id,
    jp.job_title,
    jp.company_name,
    jp.job_summary,
    jp.job_description_formatted,
    jp.job_posted_date,
    je.enrichment_version AS current_version,
    je.created_at AS last_enriched_at
FROM `brightdata_jobs.job_postings` jp
LEFT JOIN `brightdata_jobs.job_enrichments` je
    ON jp.job_posting_id = je.job_posting_id
    AND je.enrichment_type = 'skills_extraction'
    AND je.status = 'success'
WHERE jp.job_summary IS NOT NULL
    AND jp.job_description_formatted IS NOT NULL
ORDER BY jp.job_posted_date DESC;

-- View: Enrichment version distribution
CREATE OR REPLACE VIEW `brightdata_jobs.v_enrichment_version_stats` AS
SELECT 
    enrichment_type,
    enrichment_version,
    COUNT(*) AS enrichment_count,
    MIN(created_at) AS first_enriched,
    MAX(created_at) AS last_enriched
FROM `brightdata_jobs.job_enrichments`
WHERE status = 'success'
GROUP BY enrichment_type, enrichment_version
ORDER BY enrichment_type, enrichment_count DESC;
