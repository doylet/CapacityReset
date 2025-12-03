-- Version Queries
-- SQL queries for model version tracking and re-enrichment workflows
-- 
-- These queries support:
-- - Finding jobs that need re-enrichment for a new model version
-- - Analyzing enrichment version distribution
-- - Tracking version-based metrics
--
-- Version: 1.0
-- Date: 2025-12-03

-- =============================================================================
-- JOBS NEEDING RE-ENRICHMENT
-- =============================================================================

-- Query: Find jobs needing re-enrichment for a specific version
-- Parameters:
--   @target_version: The model version to check against
--   @enrichment_type: Type of enrichment ('skills_extraction', 'embeddings', etc.)
--   @limit: Maximum number of jobs to return
-- 
-- Returns jobs that either:
-- 1. Have no enrichment of the specified type
-- 2. Have enrichment with a different version
-- 3. Have failed enrichment
SELECT 
    jp.job_posting_id,
    jp.job_title,
    jp.company_name,
    jp.job_location,
    jp.job_summary,
    jp.job_description_formatted,
    jp.job_posted_date,
    je.enrichment_version AS current_version,
    je.status AS current_status,
    je.created_at AS last_enriched_at
FROM `brightdata_jobs.job_postings` jp
LEFT JOIN `brightdata_jobs.job_enrichments` je
    ON jp.job_posting_id = je.job_posting_id
    AND je.enrichment_type = @enrichment_type
    AND je.status = 'success'
    AND je.enrichment_version = @target_version
WHERE je.enrichment_id IS NULL
    AND jp.job_summary IS NOT NULL
    AND jp.job_description_formatted IS NOT NULL
ORDER BY jp.job_posted_date DESC
LIMIT @limit;


-- Query: Find all jobs with outdated enrichment versions
-- Parameters:
--   @current_version: The current/target version
--   @enrichment_type: Type of enrichment to check
-- 
-- Returns jobs that have enrichment but with older versions
SELECT 
    jp.job_posting_id,
    jp.job_title,
    je.enrichment_version AS old_version,
    je.created_at AS enriched_at,
    @current_version AS target_version
FROM `brightdata_jobs.job_postings` jp
INNER JOIN `brightdata_jobs.job_enrichments` je
    ON jp.job_posting_id = je.job_posting_id
    AND je.enrichment_type = @enrichment_type
    AND je.status = 'success'
WHERE je.enrichment_version != @current_version
    OR je.enrichment_version IS NULL
ORDER BY je.created_at ASC;


-- Query: Get re-enrichment progress for a version upgrade
-- Parameters:
--   @old_version: The version being replaced
--   @new_version: The new target version
--   @enrichment_type: Type of enrichment
SELECT 
    @old_version AS old_version,
    @new_version AS new_version,
    COUNT(DISTINCT CASE WHEN je.enrichment_version = @old_version THEN jp.job_posting_id END) AS jobs_with_old_version,
    COUNT(DISTINCT CASE WHEN je.enrichment_version = @new_version THEN jp.job_posting_id END) AS jobs_with_new_version,
    COUNT(DISTINCT CASE WHEN je.enrichment_version IS NULL AND je.status = 'success' THEN jp.job_posting_id END) AS jobs_with_legacy,
    COUNT(DISTINCT jp.job_posting_id) AS total_jobs
FROM `brightdata_jobs.job_postings` jp
LEFT JOIN `brightdata_jobs.job_enrichments` je
    ON jp.job_posting_id = je.job_posting_id
    AND je.enrichment_type = @enrichment_type;


-- =============================================================================
-- VERSION DISTRIBUTION ANALYSIS
-- =============================================================================

-- Query: Enrichment version distribution
-- Shows how many enrichments exist for each version
SELECT 
    enrichment_type,
    COALESCE(enrichment_version, 'legacy') AS version,
    COUNT(*) AS enrichment_count,
    COUNTIF(status = 'success') AS success_count,
    COUNTIF(status = 'failed') AS failed_count,
    MIN(created_at) AS first_enriched,
    MAX(created_at) AS last_enriched
FROM `brightdata_jobs.job_enrichments`
GROUP BY enrichment_type, enrichment_version
ORDER BY enrichment_type, enrichment_count DESC;


-- Query: Daily enrichment counts by version
-- Shows enrichment activity over time
SELECT 
    DATE(created_at) AS enrichment_date,
    enrichment_type,
    COALESCE(enrichment_version, 'legacy') AS version,
    COUNT(*) AS enrichment_count
FROM `brightdata_jobs.job_enrichments`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY DATE(created_at), enrichment_type, enrichment_version
ORDER BY enrichment_date DESC, enrichment_type;


-- Query: Version adoption rate
-- Shows percentage of jobs using each version
SELECT 
    enrichment_type,
    COALESCE(enrichment_version, 'legacy') AS version,
    COUNT(*) AS job_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY enrichment_type), 2) AS percentage
FROM `brightdata_jobs.job_enrichments`
WHERE status = 'success'
GROUP BY enrichment_type, enrichment_version
ORDER BY enrichment_type, job_count DESC;


-- =============================================================================
-- VERSION COMPARISON QUERIES
-- =============================================================================

-- Query: Compare skills extraction results between versions
-- Useful for validating model upgrades
-- Parameters:
--   @version_a: First version to compare
--   @version_b: Second version to compare
SELECT 
    jp.job_posting_id,
    jp.job_title,
    a.enrichment_version AS version_a,
    b.enrichment_version AS version_b,
    JSON_EXTRACT(a.metadata, '$.skills_count') AS skills_count_a,
    JSON_EXTRACT(b.metadata, '$.skills_count') AS skills_count_b
FROM `brightdata_jobs.job_postings` jp
INNER JOIN `brightdata_jobs.job_enrichments` a
    ON jp.job_posting_id = a.job_posting_id
    AND a.enrichment_type = 'skills_extraction'
    AND a.status = 'success'
    AND a.enrichment_version = @version_a
INNER JOIN `brightdata_jobs.job_enrichments` b
    ON jp.job_posting_id = b.job_posting_id
    AND b.enrichment_type = 'skills_extraction'
    AND b.status = 'success'
    AND b.enrichment_version = @version_b
LIMIT 100;


-- Query: Jobs with significant skill count changes between versions
-- Helps identify potential issues with model changes
SELECT 
    jp.job_posting_id,
    jp.job_title,
    CAST(JSON_EXTRACT(a.metadata, '$.skills_count') AS INT64) AS old_skills,
    CAST(JSON_EXTRACT(b.metadata, '$.skills_count') AS INT64) AS new_skills,
    CAST(JSON_EXTRACT(b.metadata, '$.skills_count') AS INT64) - 
    CAST(JSON_EXTRACT(a.metadata, '$.skills_count') AS INT64) AS skill_diff
FROM `brightdata_jobs.job_postings` jp
INNER JOIN `brightdata_jobs.job_enrichments` a
    ON jp.job_posting_id = a.job_posting_id
    AND a.enrichment_type = 'skills_extraction'
    AND a.status = 'success'
    AND a.enrichment_version = @old_version
INNER JOIN `brightdata_jobs.job_enrichments` b
    ON jp.job_posting_id = b.job_posting_id
    AND b.enrichment_type = 'skills_extraction'
    AND b.status = 'success'
    AND b.enrichment_version = @new_version
WHERE ABS(
    CAST(JSON_EXTRACT(b.metadata, '$.skills_count') AS INT64) - 
    CAST(JSON_EXTRACT(a.metadata, '$.skills_count') AS INT64)
) > 5
ORDER BY skill_diff DESC
LIMIT 50;


-- =============================================================================
-- LEGACY DATA MIGRATION QUERIES
-- =============================================================================

-- Query: Count legacy enrichments needing version tagging
SELECT 
    enrichment_type,
    COUNT(*) AS legacy_count
FROM `brightdata_jobs.job_enrichments`
WHERE enrichment_version IS NULL
    AND status = 'success'
GROUP BY enrichment_type;


-- Query: Tag legacy enrichments with 'legacy' version
-- Run this as part of migration
UPDATE `brightdata_jobs.job_enrichments`
SET 
    enrichment_version = 'legacy',
    model_id = enrichment_type,
    model_version = 'legacy'
WHERE enrichment_version IS NULL
    AND status = 'success';
