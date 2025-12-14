-- Job Clustering Analysis Queries

-- 1. Overview of all clusters with sample jobs
SELECT 
  jc.cluster_id,
  jc.cluster_name,
  jc.cluster_size,
  COUNT(DISTINCT jc.job_posting_id) as jobs_in_cluster,
  ARRAY_AGG(DISTINCT jp.job_title ORDER BY jp.job_title LIMIT 5) as sample_titles,
  ARRAY_AGG(DISTINCT jp.company_name ORDER BY jp.company_name LIMIT 5) as sample_companies
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` jc
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp
  ON jc.job_posting_id = jp.job_posting_id
GROUP BY jc.cluster_id, jc.cluster_name, jc.cluster_size
ORDER BY jc.cluster_size DESC;

-- 2. Get detailed keywords for a specific cluster
SELECT 
  cluster_id,
  cluster_name,
  cluster_size,
  cluster_keywords
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
WHERE cluster_id = 6  -- Replace with desired cluster_id
LIMIT 1;

-- 3. Find all jobs in a specific cluster with their details
SELECT 
  jc.cluster_id,
  jc.cluster_name,
  jp.job_posting_id,
  jp.job_title,
  jp.company_name,
  jp.job_location,
  jp.salary_low,
  jp.salary_high,
  jp.job_url
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` jc
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp
  ON jc.job_posting_id = jp.job_posting_id
WHERE jc.cluster_name LIKE '%Product%'  -- Filter by cluster name
ORDER BY jp.company_name, jp.job_title;

-- 4. Jobs with both skills and cluster assignments
SELECT 
  jp.job_title,
  jp.company_name,
  jc.cluster_name,
  ARRAY_AGG(DISTINCT js.skill_name ORDER BY js.confidence_score DESC LIMIT 10) as top_skills
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` jc
  ON jp.job_posting_id = jc.job_posting_id
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_skills` js
  ON jp.job_posting_id = js.job_posting_id
WHERE js.confidence_score > 0.6
GROUP BY jp.job_title, jp.company_name, jc.cluster_name
ORDER BY jp.job_title
LIMIT 20;

-- 5. Skill distribution by cluster
SELECT 
  jc.cluster_name,
  js.skill_category,
  COUNT(DISTINCT js.skill_name) as unique_skills,
  ARRAY_AGG(DISTINCT js.skill_name ORDER BY js.skill_name LIMIT 10) as top_skills
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` jc
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_skills` js
  ON jc.job_posting_id = js.job_posting_id
WHERE js.confidence_score > 0.6
GROUP BY jc.cluster_name, js.skill_category
ORDER BY jc.cluster_name, unique_skills DESC;

-- 6. Latest clustering run metadata
SELECT 
  je.enrichment_id,
  je.created_at,
  je.enrichment_version,
  je.metadata,
  COUNT(DISTINCT jc.job_posting_id) as jobs_clustered
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_enrichments` je
LEFT JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` jc
  ON je.enrichment_id = jc.enrichment_id
WHERE je.enrichment_type = 'job_clustering'
  AND je.status = 'success'
GROUP BY je.enrichment_id, je.created_at, je.enrichment_version, je.metadata
ORDER BY je.created_at DESC
LIMIT 1;

-- 7. Compare clusters to find career progression paths
-- Example: Find similar jobs in different clusters (potential career moves)
WITH cluster_pairs AS (
  SELECT DISTINCT
    c1.cluster_name as from_cluster,
    c2.cluster_name as to_cluster,
    c1.job_posting_id as job1_id,
    c2.job_posting_id as job2_id
  FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` c1
  CROSS JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` c2
  WHERE c1.cluster_id < c2.cluster_id
  LIMIT 100
)
SELECT 
  cp.from_cluster,
  cp.to_cluster,
  jp1.job_title as job1_title,
  jp2.job_title as job2_title,
  jp1.company_name as company1,
  jp2.company_name as company2
FROM cluster_pairs cp
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp1
  ON cp.job1_id = jp1.job_posting_id
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp2
  ON cp.job2_id = jp2.job_posting_id
LIMIT 20;

-- 8. Cluster health metrics
SELECT 
  cluster_id,
  cluster_name,
  COUNT(*) as total_assignments,
  COUNT(DISTINCT job_posting_id) as unique_jobs,
  MIN(created_at) as first_assignment,
  MAX(created_at) as last_assignment
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
GROUP BY cluster_id, cluster_name
ORDER BY cluster_id;

-- ==============================================================================
-- CLUSTER VERSION FILTERING QUERIES
-- ==============================================================================

-- 9. Get active cluster assignments only
SELECT 
  jc.cluster_id,
  jc.cluster_name,
  jc.cluster_version,
  jc.cluster_run_id,
  COUNT(DISTINCT jc.job_posting_id) as jobs_in_cluster,
  ARRAY_AGG(DISTINCT jp.job_title ORDER BY jp.job_title LIMIT 5) as sample_titles
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` jc
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp
  ON jc.job_posting_id = jp.job_posting_id
WHERE jc.is_active = TRUE
GROUP BY jc.cluster_id, jc.cluster_name, jc.cluster_version, jc.cluster_run_id
ORDER BY jc.cluster_size DESC;

-- 10. Get cluster assignments for a specific run
-- Parameters: @run_id (STRING)
SELECT 
  job_posting_id,
  cluster_id,
  cluster_name,
  cluster_keywords,
  cluster_size,
  is_active
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
WHERE cluster_run_id = @run_id
ORDER BY cluster_id, job_posting_id;

-- 11. Get all cluster runs with their statistics
SELECT 
  cluster_run_id,
  cluster_model_id,
  cluster_version,
  MIN(created_at) as run_timestamp,
  COUNT(DISTINCT job_posting_id) as total_jobs,
  COUNT(DISTINCT cluster_id) as num_clusters,
  MAX(CASE WHEN is_active THEN 1 ELSE 0 END) as is_current_run
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
GROUP BY cluster_run_id, cluster_model_id, cluster_version
ORDER BY cluster_version DESC;

-- 12. Calculate cluster stability between two runs
-- Parameters: @old_run_id, @new_run_id (STRING)
WITH old_assignments AS (
  SELECT job_posting_id, cluster_id
  FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
  WHERE cluster_run_id = @old_run_id
),
new_assignments AS (
  SELECT job_posting_id, cluster_id
  FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
  WHERE cluster_run_id = @new_run_id
),
comparison AS (
  SELECT 
    o.job_posting_id,
    o.cluster_id as old_cluster,
    n.cluster_id as new_cluster,
    CASE WHEN o.cluster_id = n.cluster_id THEN 1 ELSE 0 END as is_stable
  FROM old_assignments o
  JOIN new_assignments n USING (job_posting_id)
)
SELECT 
  COUNT(*) as total_compared,
  SUM(is_stable) as unchanged,
  COUNT(*) - SUM(is_stable) as changed,
  ROUND(SUM(is_stable) / COUNT(*), 4) as stability_score
FROM comparison;

-- 13. Track cluster migrations between runs
-- Parameters: @old_run_id, @new_run_id (STRING)
WITH migrations AS (
  SELECT 
    old.cluster_id as from_cluster,
    old.cluster_name as from_cluster_name,
    new.cluster_id as to_cluster,
    new.cluster_name as to_cluster_name,
    COUNT(*) as job_count
  FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` old
  JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_clusters` new
    ON old.job_posting_id = new.job_posting_id
  WHERE old.cluster_run_id = @old_run_id
    AND new.cluster_run_id = @new_run_id
    AND old.cluster_id != new.cluster_id
  GROUP BY old.cluster_id, old.cluster_name, new.cluster_id, new.cluster_name
)
SELECT *
FROM migrations
ORDER BY job_count DESC;

-- 14. Get cluster history for a specific job
-- Parameters: @job_id (STRING)
SELECT 
  cluster_run_id,
  cluster_version,
  cluster_id,
  cluster_name,
  is_active,
  created_at
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
WHERE job_posting_id = @job_id
ORDER BY cluster_version DESC;

-- 15. Find volatile jobs (jobs that frequently change clusters)
WITH job_cluster_changes AS (
  SELECT 
    job_posting_id,
    COUNT(DISTINCT cluster_id) as unique_clusters,
    COUNT(*) as assignment_count,
    ARRAY_AGG(DISTINCT cluster_name) as cluster_history
  FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
  GROUP BY job_posting_id
  HAVING COUNT(DISTINCT cluster_id) > 1
)
SELECT 
  jcc.*,
  jp.job_title,
  jp.company_name
FROM job_cluster_changes jcc
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp
  ON jcc.job_posting_id = jp.job_posting_id
ORDER BY unique_clusters DESC
LIMIT 50;

-- 16. Get model version statistics for clustering
SELECT 
  cluster_model_id,
  COUNT(DISTINCT cluster_run_id) as total_runs,
  COUNT(DISTINCT job_posting_id) as total_jobs_clustered,
  MIN(created_at) as first_run,
  MAX(created_at) as last_run
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
GROUP BY cluster_model_id
ORDER BY last_run DESC;
