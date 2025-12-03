-- Section Classifications Schema
-- BigQuery table for job posting section classification results
--
-- This table supports:
-- - Storing section-by-section classification results
-- - Training data for ML section classifier
-- - Analytics on section relevance patterns
--
-- Version: 1.0
-- Date: 2025-12-03

-- Create section_classifications table
CREATE TABLE IF NOT EXISTS `brightdata_jobs.section_classifications` (
    -- Primary key
    classification_id STRING NOT NULL,
    
    -- Foreign key reference to job_postings
    job_posting_id STRING NOT NULL,
    
    -- Section details
    section_text STRING NOT NULL,          -- The section content
    section_header STRING,                 -- Header if identifiable (e.g., "Requirements")
    section_index INT64 NOT NULL,          -- Order in document (0-based)
    
    -- Classification result
    is_skills_relevant BOOL NOT NULL,      -- Binary classification
    relevance_probability FLOAT64 NOT NULL, -- Confidence (0.0-1.0)
    
    -- Model information
    classifier_version STRING NOT NULL,    -- Version of classifier used
    classification_method STRING NOT NULL, -- "rule_based" | "ml_model"
    
    -- Additional metadata
    section_word_count INT64,              -- Number of words in section
    section_char_count INT64,              -- Number of characters
    detected_keywords ARRAY<STRING>,       -- Keywords that triggered classification
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    
    -- Optional: For training data labeling
    human_label BOOL,                      -- Human-provided label (for training)
    labeled_by STRING,                     -- Who provided the label
    labeled_at TIMESTAMP                   -- When the label was provided
);

-- Create index for job lookup
CREATE INDEX IF NOT EXISTS idx_section_job
ON `brightdata_jobs.section_classifications` (job_posting_id);

-- Create index for relevance filtering
CREATE INDEX IF NOT EXISTS idx_section_relevance
ON `brightdata_jobs.section_classifications` (is_skills_relevant, relevance_probability DESC);

-- Create index for classifier version tracking
CREATE INDEX IF NOT EXISTS idx_section_classifier
ON `brightdata_jobs.section_classifications` (classifier_version, classification_method);

-- Create index for training data queries (human_label)
CREATE INDEX IF NOT EXISTS idx_section_labeled
ON `brightdata_jobs.section_classifications` (human_label);

-- View: Skills-relevant sections
CREATE OR REPLACE VIEW `brightdata_jobs.v_skills_relevant_sections` AS
SELECT 
    job_posting_id,
    section_header,
    section_text,
    relevance_probability,
    section_index
FROM `brightdata_jobs.section_classifications`
WHERE is_skills_relevant = TRUE
    AND relevance_probability >= 0.5
ORDER BY job_posting_id, section_index;

-- View: Classification accuracy by method
CREATE OR REPLACE VIEW `brightdata_jobs.v_section_classifier_stats` AS
SELECT 
    classifier_version,
    classification_method,
    COUNT(*) AS total_classifications,
    COUNTIF(is_skills_relevant) AS relevant_count,
    COUNTIF(NOT is_skills_relevant) AS not_relevant_count,
    AVG(relevance_probability) AS avg_probability,
    MIN(created_at) AS first_classification,
    MAX(created_at) AS last_classification
FROM `brightdata_jobs.section_classifications`
GROUP BY classifier_version, classification_method
ORDER BY last_classification DESC;

-- View: Training data with human labels
CREATE OR REPLACE VIEW `brightdata_jobs.v_section_training_data` AS
SELECT 
    section_text,
    section_header,
    human_label AS is_skills_relevant,
    is_skills_relevant AS model_prediction,
    CASE 
        WHEN human_label = is_skills_relevant THEN 'correct'
        ELSE 'incorrect'
    END AS prediction_accuracy,
    relevance_probability AS model_confidence,
    labeled_by,
    labeled_at
FROM `brightdata_jobs.section_classifications`
WHERE human_label IS NOT NULL
ORDER BY labeled_at DESC;

-- View: Section header patterns
CREATE OR REPLACE VIEW `brightdata_jobs.v_section_header_patterns` AS
SELECT 
    LOWER(section_header) AS section_header_normalized,
    COUNT(*) AS occurrence_count,
    COUNTIF(is_skills_relevant) AS relevant_count,
    COUNTIF(NOT is_skills_relevant) AS not_relevant_count,
    AVG(CAST(is_skills_relevant AS INT64)) AS relevance_rate
FROM `brightdata_jobs.section_classifications`
WHERE section_header IS NOT NULL
GROUP BY LOWER(section_header)
HAVING COUNT(*) >= 10
ORDER BY occurrence_count DESC;
