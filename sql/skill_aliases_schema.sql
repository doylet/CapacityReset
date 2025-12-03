-- Skill Aliases Schema
-- BigQuery table for skill alias to canonical name mappings
--
-- This table supports:
-- - Alias resolution during skills extraction
-- - User feedback for new alias suggestions
-- - Confidence-weighted alias matching
--
-- Version: 1.0
-- Date: 2025-12-03

-- Create skill_aliases table
CREATE TABLE IF NOT EXISTS `brightdata_jobs.skill_aliases` (
    -- Primary key
    alias_id STRING NOT NULL,
    
    -- Alias mapping
    alias_text STRING NOT NULL,          -- e.g., "K8s", "GCP", "JS"
    canonical_name STRING NOT NULL,       -- e.g., "Kubernetes", "Google Cloud Platform"
    
    -- Classification
    skill_category STRING NOT NULL,       -- Category of the canonical skill
    
    -- Metadata
    source STRING,                        -- "manual" | "user_feedback" | "auto_detected"
    confidence FLOAT64,                   -- 0.0-1.0, confidence in this mapping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    created_by STRING,                    -- User who added (if manual)
    
    -- Status
    is_active BOOL DEFAULT TRUE,          -- Can be deactivated without deletion
    
    -- Usage tracking
    usage_count INT64 DEFAULT 0,          -- How many times this alias was resolved
    last_used_at TIMESTAMP
);

-- Create index on alias_text for case-insensitive lookup
-- Note: BigQuery handles case-insensitive matching in queries with LOWER()
CREATE INDEX IF NOT EXISTS idx_alias_text
ON `brightdata_jobs.skill_aliases` (alias_text);

-- Create index for canonical name lookup
CREATE INDEX IF NOT EXISTS idx_canonical_name
ON `brightdata_jobs.skill_aliases` (canonical_name);

-- Create index for category filtering
CREATE INDEX IF NOT EXISTS idx_alias_category
ON `brightdata_jobs.skill_aliases` (skill_category, is_active);

-- View: Active aliases by category
CREATE OR REPLACE VIEW `brightdata_jobs.v_active_aliases` AS
SELECT 
    alias_text,
    canonical_name,
    skill_category,
    confidence,
    source,
    usage_count
FROM `brightdata_jobs.skill_aliases`
WHERE is_active = TRUE
ORDER BY skill_category, canonical_name, confidence DESC;

-- View: Most used aliases
CREATE OR REPLACE VIEW `brightdata_jobs.v_alias_usage_stats` AS
SELECT 
    alias_text,
    canonical_name,
    skill_category,
    usage_count,
    last_used_at,
    confidence
FROM `brightdata_jobs.skill_aliases`
WHERE is_active = TRUE
ORDER BY usage_count DESC
LIMIT 100;

-- Sample data for initial population (optional)
-- INSERT INTO `brightdata_jobs.skill_aliases` (alias_id, alias_text, canonical_name, skill_category, source, confidence)
-- VALUES
--     (GENERATE_UUID(), 'K8s', 'Kubernetes', 'devops_tools', 'manual', 1.0),
--     (GENERATE_UUID(), 'GCP', 'Google Cloud Platform', 'cloud_platforms', 'manual', 1.0),
--     (GENERATE_UUID(), 'JS', 'JavaScript', 'programming_languages', 'manual', 1.0);
