-- Evaluation Queries
-- Queries for analyzing ML model performance over time

-- 1. Get all evaluations for a model
SELECT 
    evaluation_id,
    model_version,
    dataset_version,
    sample_count,
    overall_precision,
    overall_recall,
    overall_f1,
    evaluation_date,
    execution_time_seconds,
    is_ci_run,
    threshold_passed
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
WHERE model_id = 'skills_extractor'
ORDER BY evaluation_date DESC
LIMIT 20;

-- 2. Get latest evaluation per model version
WITH latest_per_version AS (
    SELECT 
        model_version,
        MAX(evaluation_date) as latest_date
    FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
    WHERE model_id = 'skills_extractor'
    GROUP BY model_version
)
SELECT 
    e.*
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results` e
JOIN latest_per_version lpv
    ON e.model_version = lpv.model_version
    AND e.evaluation_date = lpv.latest_date
ORDER BY e.evaluation_date DESC;

-- 3. Average metrics by model version
SELECT 
    model_version,
    COUNT(*) as eval_count,
    AVG(overall_precision) as avg_precision,
    AVG(overall_recall) as avg_recall,
    AVG(overall_f1) as avg_f1,
    MIN(overall_f1) as min_f1,
    MAX(overall_f1) as max_f1,
    STDDEV(overall_f1) as f1_stddev
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
WHERE model_id = 'skills_extractor'
GROUP BY model_version
ORDER BY MAX(evaluation_date) DESC;

-- 4. F1 score trend over time (daily aggregation)
SELECT 
    DATE(evaluation_date) as eval_date,
    model_version,
    AVG(overall_f1) as avg_f1,
    COUNT(*) as eval_count
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
WHERE model_id = 'skills_extractor'
    AND evaluation_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY eval_date, model_version
ORDER BY eval_date DESC;

-- 5. CI pipeline run history
SELECT 
    evaluation_id,
    model_version,
    ci_build_id,
    ci_pipeline_name,
    overall_f1,
    threshold_f1,
    threshold_passed,
    evaluation_date,
    execution_time_seconds
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
WHERE is_ci_run = TRUE
ORDER BY evaluation_date DESC
LIMIT 50;

-- 6. Failed CI runs (threshold not met)
SELECT 
    evaluation_id,
    model_version,
    ci_build_id,
    overall_f1,
    threshold_f1,
    evaluation_date,
    notes
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
WHERE is_ci_run = TRUE
    AND threshold_passed = FALSE
ORDER BY evaluation_date DESC;

-- 7. Compare two model versions
-- Parameters: @version_a, @version_b
WITH version_stats AS (
    SELECT 
        model_version,
        COUNT(*) as eval_count,
        AVG(overall_precision) as avg_precision,
        AVG(overall_recall) as avg_recall,
        AVG(overall_f1) as avg_f1
    FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
    WHERE model_id = 'skills_extractor'
        AND model_version IN (@version_a, @version_b)
    GROUP BY model_version
)
SELECT 
    a.model_version as version_a,
    b.model_version as version_b,
    a.avg_f1 as f1_a,
    b.avg_f1 as f1_b,
    b.avg_f1 - a.avg_f1 as f1_improvement,
    b.avg_precision - a.avg_precision as precision_improvement,
    b.avg_recall - a.avg_recall as recall_improvement
FROM version_stats a, version_stats b
WHERE a.model_version = @version_a
    AND b.model_version = @version_b;

-- 8. Per-category performance (requires parsing JSON)
SELECT 
    evaluation_id,
    model_version,
    evaluation_date,
    JSON_EXTRACT_SCALAR(category_metrics, '$.programming_languages.f1') as prog_lang_f1,
    JSON_EXTRACT_SCALAR(category_metrics, '$.cloud_platforms.f1') as cloud_f1,
    JSON_EXTRACT_SCALAR(category_metrics, '$.databases.f1') as databases_f1,
    JSON_EXTRACT_SCALAR(category_metrics, '$.devops_tools.f1') as devops_f1
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
WHERE model_id = 'skills_extractor'
    AND category_metrics IS NOT NULL
ORDER BY evaluation_date DESC
LIMIT 10;

-- 9. Evaluation performance metrics
SELECT 
    DATE(evaluation_date) as date,
    COUNT(*) as evaluations_run,
    AVG(execution_time_seconds) as avg_execution_time,
    SUM(sample_count) as total_samples_evaluated,
    AVG(sample_count) as avg_samples_per_eval
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
WHERE evaluation_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY date
ORDER BY date DESC;

-- 10. Get evaluation by ID
-- Parameter: @evaluation_id
SELECT *
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
WHERE evaluation_id = @evaluation_id;

-- 11. Evaluations by dataset version
SELECT 
    dataset_version,
    COUNT(*) as eval_count,
    AVG(overall_f1) as avg_f1,
    MIN(evaluation_date) as first_used,
    MAX(evaluation_date) as last_used
FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
WHERE model_id = 'skills_extractor'
GROUP BY dataset_version
ORDER BY last_used DESC;

-- 12. Find regressions (F1 dropped from previous eval)
WITH ordered_evals AS (
    SELECT 
        evaluation_id,
        model_version,
        overall_f1,
        evaluation_date,
        LAG(overall_f1) OVER (PARTITION BY model_id ORDER BY evaluation_date) as prev_f1
    FROM `sylvan-replica-478802-p4.brightdata_jobs.evaluation_results`
    WHERE model_id = 'skills_extractor'
)
SELECT 
    evaluation_id,
    model_version,
    overall_f1,
    prev_f1,
    prev_f1 - overall_f1 as regression_amount,
    evaluation_date
FROM ordered_evals
WHERE overall_f1 < prev_f1
    AND (prev_f1 - overall_f1) > 0.05  -- More than 5% drop
ORDER BY evaluation_date DESC;
