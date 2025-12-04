-- Evaluation Queries
-- SQL queries for ML model evaluation results and historical analysis
-- 
-- These queries support:
-- - Retrieving historical evaluation results
-- - Comparing model versions
-- - Tracking performance over time
--
-- Version: 1.0
-- Date: 2025-12-03

-- =============================================================================
-- RETRIEVE EVALUATION RESULTS
-- =============================================================================

-- Query: Get latest evaluation for a model
-- Parameters: @model_id
SELECT 
    evaluation_id,
    model_id,
    model_version,
    dataset_version,
    dataset_path,
    sample_count,
    overall_precision,
    overall_recall,
    overall_f1,
    category_metrics,
    evaluation_date,
    execution_time_seconds,
    is_ci_run,
    ci_build_id,
    threshold_passed,
    created_at
FROM `brightdata_jobs.evaluation_results`
WHERE model_id = @model_id
ORDER BY evaluation_date DESC
LIMIT 1;


-- Query: Get evaluation history for a model
-- Parameters: @model_id, @limit
SELECT 
    evaluation_id,
    model_id,
    model_version,
    dataset_version,
    sample_count,
    overall_precision,
    overall_recall,
    overall_f1,
    evaluation_date,
    is_ci_run,
    threshold_passed
FROM `brightdata_jobs.evaluation_results`
WHERE model_id = @model_id
ORDER BY evaluation_date DESC
LIMIT @limit;


-- Query: Get all evaluations for a specific model version
-- Parameters: @model_id, @model_version
SELECT 
    evaluation_id,
    dataset_version,
    sample_count,
    overall_precision,
    overall_recall,
    overall_f1,
    category_metrics,
    evaluation_date,
    execution_time_seconds
FROM `brightdata_jobs.evaluation_results`
WHERE model_id = @model_id
    AND model_version = @model_version
ORDER BY evaluation_date DESC;


-- =============================================================================
-- PERFORMANCE TRENDS
-- =============================================================================

-- Query: Track F1 score over time
-- Parameters: @model_id, @days_back
SELECT 
    DATE(evaluation_date) AS eval_date,
    model_version,
    AVG(overall_f1) AS avg_f1,
    AVG(overall_precision) AS avg_precision,
    AVG(overall_recall) AS avg_recall,
    COUNT(*) AS eval_count
FROM `brightdata_jobs.evaluation_results`
WHERE model_id = @model_id
    AND evaluation_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days_back DAY)
GROUP BY DATE(evaluation_date), model_version
ORDER BY eval_date DESC;


-- Query: Compare metrics across model versions
-- Parameters: @model_id
SELECT 
    model_version,
    COUNT(*) AS eval_count,
    AVG(overall_f1) AS avg_f1,
    MIN(overall_f1) AS min_f1,
    MAX(overall_f1) AS max_f1,
    AVG(overall_precision) AS avg_precision,
    AVG(overall_recall) AS avg_recall,
    AVG(execution_time_seconds) AS avg_execution_time
FROM `brightdata_jobs.evaluation_results`
WHERE model_id = @model_id
GROUP BY model_version
ORDER BY MAX(evaluation_date) DESC;


-- Query: Performance regression detection
-- Parameters: @model_id, @threshold
WITH latest_versions AS (
    SELECT 
        model_version,
        AVG(overall_f1) AS avg_f1,
        ROW_NUMBER() OVER (ORDER BY MAX(evaluation_date) DESC) AS version_rank
    FROM `brightdata_jobs.evaluation_results`
    WHERE model_id = @model_id
    GROUP BY model_version
)
SELECT 
    current.model_version AS current_version,
    previous.model_version AS previous_version,
    current.avg_f1 AS current_f1,
    previous.avg_f1 AS previous_f1,
    (current.avg_f1 - previous.avg_f1) AS f1_change,
    CASE 
        WHEN (current.avg_f1 - previous.avg_f1) < -@threshold THEN 'REGRESSION'
        WHEN (current.avg_f1 - previous.avg_f1) > @threshold THEN 'IMPROVEMENT'
        ELSE 'STABLE'
    END AS status
FROM latest_versions current
LEFT JOIN latest_versions previous
    ON current.version_rank = previous.version_rank - 1
WHERE current.version_rank = 1;


-- =============================================================================
-- CI/CD QUERIES
-- =============================================================================

-- Query: Get CI evaluation results
-- Parameters: @limit
SELECT 
    evaluation_id,
    model_id,
    model_version,
    overall_f1,
    threshold_passed,
    ci_build_id,
    evaluation_date,
    execution_time_seconds
FROM `brightdata_jobs.evaluation_results`
WHERE is_ci_run = TRUE
ORDER BY evaluation_date DESC
LIMIT @limit;


-- Query: CI pass rate by model
-- Parameters: @model_id, @days_back
SELECT 
    model_version,
    COUNT(*) AS total_ci_runs,
    COUNTIF(threshold_passed = TRUE) AS passed,
    COUNTIF(threshold_passed = FALSE) AS failed,
    ROUND(COUNTIF(threshold_passed = TRUE) * 100.0 / COUNT(*), 2) AS pass_rate_percent
FROM `brightdata_jobs.evaluation_results`
WHERE is_ci_run = TRUE
    AND model_id = @model_id
    AND evaluation_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days_back DAY)
GROUP BY model_version
ORDER BY MAX(evaluation_date) DESC;


-- Query: Failed CI evaluations
-- Parameters: @model_id, @limit
SELECT 
    evaluation_id,
    model_version,
    overall_f1,
    ci_build_id,
    evaluation_date,
    dataset_version
FROM `brightdata_jobs.evaluation_results`
WHERE is_ci_run = TRUE
    AND threshold_passed = FALSE
    AND model_id = @model_id
ORDER BY evaluation_date DESC
LIMIT @limit;


-- =============================================================================
-- CATEGORY ANALYSIS
-- =============================================================================

-- Query: Extract category metrics (requires JSON parsing)
-- Parameters: @evaluation_id
SELECT 
    evaluation_id,
    model_version,
    overall_f1,
    JSON_EXTRACT_SCALAR(category_metrics, '$.programming_languages.f1') AS programming_f1,
    JSON_EXTRACT_SCALAR(category_metrics, '$.web_frameworks.f1') AS frameworks_f1,
    JSON_EXTRACT_SCALAR(category_metrics, '$.databases.f1') AS databases_f1,
    JSON_EXTRACT_SCALAR(category_metrics, '$.cloud_platforms.f1') AS cloud_f1,
    JSON_EXTRACT_SCALAR(category_metrics, '$.devops_tools.f1') AS devops_f1
FROM `brightdata_jobs.evaluation_results`
WHERE evaluation_id = @evaluation_id;


-- Query: Category performance trends
-- Parameters: @model_id, @category
SELECT 
    DATE(evaluation_date) AS eval_date,
    model_version,
    CAST(JSON_EXTRACT_SCALAR(category_metrics, CONCAT('$.', @category, '.f1')) AS FLOAT64) AS category_f1,
    CAST(JSON_EXTRACT_SCALAR(category_metrics, CONCAT('$.', @category, '.support')) AS INT64) AS category_support
FROM `brightdata_jobs.evaluation_results`
WHERE model_id = @model_id
    AND category_metrics IS NOT NULL
ORDER BY eval_date DESC;


-- =============================================================================
-- DATASET ANALYSIS
-- =============================================================================

-- Query: Evaluations by dataset version
-- Parameters: @dataset_version
SELECT 
    evaluation_id,
    model_id,
    model_version,
    overall_f1,
    sample_count,
    evaluation_date
FROM `brightdata_jobs.evaluation_results`
WHERE dataset_version = @dataset_version
ORDER BY evaluation_date DESC;


-- Query: Dataset version comparison
-- Parameters: @model_id
SELECT 
    dataset_version,
    COUNT(*) AS eval_count,
    AVG(overall_f1) AS avg_f1,
    AVG(sample_count) AS avg_samples,
    MIN(evaluation_date) AS first_used,
    MAX(evaluation_date) AS last_used
FROM `brightdata_jobs.evaluation_results`
WHERE model_id = @model_id
GROUP BY dataset_version
ORDER BY last_used DESC;


-- =============================================================================
-- SUMMARY STATISTICS
-- =============================================================================

-- Query: Overall evaluation summary
SELECT 
    model_id,
    COUNT(*) AS total_evaluations,
    COUNT(DISTINCT model_version) AS versions_evaluated,
    AVG(overall_f1) AS overall_avg_f1,
    MAX(overall_f1) AS best_f1,
    AVG(execution_time_seconds) AS avg_execution_time,
    MIN(evaluation_date) AS first_evaluation,
    MAX(evaluation_date) AS last_evaluation
FROM `brightdata_jobs.evaluation_results`
GROUP BY model_id
ORDER BY total_evaluations DESC;
