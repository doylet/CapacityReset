-- Migration: Add Version Fields to Job Enrichments
-- 
-- Purpose: Extend existing job_enrichments table with version tracking columns
-- and migrate existing records to have a "legacy" version identifier.
--
-- This migration is IDEMPOTENT - safe to run multiple times.
--
-- Version: 1
-- Date: 2025-12-03

-- Step 1: Add new columns (IF NOT EXISTS pattern via SAFE_ functions)
-- Note: BigQuery DDL does not support ADD COLUMN IF NOT EXISTS directly,
-- so we use ALTER TABLE which is safe for existing columns.

-- Add model_id column
ALTER TABLE `brightdata_jobs.job_enrichments`
ADD COLUMN IF NOT EXISTS model_id STRING;

-- Add model_version column  
ALTER TABLE `brightdata_jobs.job_enrichments`
ADD COLUMN IF NOT EXISTS model_version STRING;

-- Add enrichment_version column (denormalized for query performance)
ALTER TABLE `brightdata_jobs.job_enrichments`
ADD COLUMN IF NOT EXISTS enrichment_version STRING;

-- Add processing_time_ms column for performance tracking
ALTER TABLE `brightdata_jobs.job_enrichments`
ADD COLUMN IF NOT EXISTS processing_time_ms INT64;

-- Add retry_count column for reliability tracking
ALTER TABLE `brightdata_jobs.job_enrichments`
ADD COLUMN IF NOT EXISTS retry_count INT64;

-- Step 2: Migrate existing records to have legacy version
-- Only update records that don't have a version set yet
UPDATE `brightdata_jobs.job_enrichments`
SET 
    enrichment_version = 'legacy',
    model_id = enrichment_type,  -- Use enrichment_type as model_id for legacy
    model_version = 'legacy'
WHERE enrichment_version IS NULL
    AND status = 'success';

-- Step 3: Create indexes for new columns
-- Version-based queries
CREATE INDEX IF NOT EXISTS idx_enrichments_version
ON `brightdata_jobs.job_enrichments` (enrichment_version, enrichment_type);

-- Model tracking queries  
CREATE INDEX IF NOT EXISTS idx_enrichments_model
ON `brightdata_jobs.job_enrichments` (model_id, model_version);

-- Step 4: Verification query (optional - run to verify migration)
-- SELECT 
--     enrichment_type,
--     enrichment_version,
--     COUNT(*) as count,
--     MIN(created_at) as first_record,
--     MAX(created_at) as last_record
-- FROM `brightdata_jobs.job_enrichments`
-- GROUP BY enrichment_type, enrichment_version
-- ORDER BY enrichment_type, enrichment_version;

-- Migration complete
-- Note: After this migration:
-- - All existing successful enrichments will have enrichment_version = 'legacy'
-- - New enrichments should set enrichment_version to the model version
-- - Queries can filter by enrichment_version for re-enrichment workflows
