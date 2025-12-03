-- Evaluation Results Schema
-- BigQuery table for ML model evaluation metrics tracking
--
-- This table supports:
-- - Historical evaluation result storage
-- - CI/CD pipeline integration
-- - Model performance comparison over time
-- - Per-category metrics breakdown
--
-- Version: 1.0
-- Date: 2025-12-03

-- Create evaluation_results table
CREATE TABLE IF NOT EXISTS `brightdata_jobs.evaluation_results` (
    -- Primary key
    evaluation_id STRING NOT NULL,
    
    -- Model identification
    model_id STRING NOT NULL,             -- e.g., "skills_extractor"
    model_version STRING NOT NULL,        -- e.g., "v4.0-unified-config-enhanced"
    
    -- Dataset information
    dataset_version STRING NOT NULL,      -- Version identifier for evaluation dataset
    dataset_path STRING,                  -- GCS path to dataset used
    sample_count INT64 NOT NULL,          -- Number of samples evaluated
    
    -- Overall metrics (macro-averaged)
    overall_precision FLOAT64 NOT NULL,   -- 0.0-1.0
    overall_recall FLOAT64 NOT NULL,      -- 0.0-1.0
    overall_f1 FLOAT64 NOT NULL,          -- 0.0-1.0
    overall_accuracy FLOAT64,             -- 0.0-1.0 (optional)
    
    -- Per-category breakdown stored as JSON
    -- Example: {"programming_languages": {"precision": 0.85, "recall": 0.90, "f1": 0.87, "support": 50}}
    category_metrics JSON,
    
    -- Execution information
    evaluation_date TIMESTAMP NOT NULL,
    execution_time_seconds FLOAT64,
    
    -- CI/CD integration
    is_ci_run BOOL DEFAULT FALSE,
    ci_build_id STRING,
    ci_pipeline_name STRING,
    threshold_f1 FLOAT64,                 -- F1 threshold used for CI gate
    threshold_passed BOOL,                -- Did it meet the threshold?
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    notes STRING,                         -- Optional notes about this evaluation
    
    -- Environment information
    environment STRING,                   -- "production", "staging", "development"
    gcp_project STRING
);

-- Create index for model version lookup
CREATE INDEX IF NOT EXISTS idx_eval_model_version
ON `brightdata_jobs.evaluation_results` (model_id, model_version);

-- Create index for date-based queries
CREATE INDEX IF NOT EXISTS idx_eval_model_date
ON `brightdata_jobs.evaluation_results` (model_id, evaluation_date DESC);

-- Create index for CI run filtering
CREATE INDEX IF NOT EXISTS idx_eval_ci_runs
ON `brightdata_jobs.evaluation_results` (is_ci_run, model_id, evaluation_date DESC);

-- View: Latest evaluation per model
CREATE OR REPLACE VIEW `brightdata_jobs.v_latest_evaluations` AS
SELECT 
    e.model_id,
    e.model_version,
    e.overall_precision,
    e.overall_recall,
    e.overall_f1,
    e.sample_count,
    e.evaluation_date,
    e.threshold_passed
FROM `brightdata_jobs.evaluation_results` e
INNER JOIN (
    SELECT model_id, MAX(evaluation_date) AS max_date
    FROM `brightdata_jobs.evaluation_results`
    GROUP BY model_id
) latest ON e.model_id = latest.model_id AND e.evaluation_date = latest.max_date;

-- View: Evaluation history for trending
CREATE OR REPLACE VIEW `brightdata_jobs.v_evaluation_trends` AS
SELECT 
    model_id,
    model_version,
    evaluation_date,
    overall_f1,
    overall_precision,
    overall_recall,
    sample_count,
    is_ci_run
FROM `brightdata_jobs.evaluation_results`
WHERE evaluation_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
ORDER BY model_id, evaluation_date DESC;

-- View: CI pipeline results
CREATE OR REPLACE VIEW `brightdata_jobs.v_ci_evaluation_results` AS
SELECT 
    model_id,
    model_version,
    ci_build_id,
    ci_pipeline_name,
    overall_f1,
    threshold_f1,
    threshold_passed,
    evaluation_date,
    execution_time_seconds
FROM `brightdata_jobs.evaluation_results`
WHERE is_ci_run = TRUE
ORDER BY evaluation_date DESC;
