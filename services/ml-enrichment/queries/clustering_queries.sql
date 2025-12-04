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

-- =============================================================================
-- VERSION-BASED CLUSTER QUERIES (for cluster stability analysis)
-- =============================================================================

-- 9. Get clusters by run ID
-- Parameters: @cluster_run_id
SELECT 
  cluster_assignment_id,
  job_posting_id,
  cluster_id,
  cluster_name,
  cluster_size,
  cluster_keywords,
  cluster_run_id,
  cluster_model_id,
  cluster_version,
  is_active,
  created_at
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
WHERE cluster_run_id = @cluster_run_id
ORDER BY cluster_id, job_posting_id;

-- 10. Get only active cluster assignments
SELECT 
  job_posting_id,
  cluster_id,
  cluster_name,
  cluster_run_id,
  cluster_version
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
WHERE is_active = TRUE
ORDER BY cluster_id;

-- 11. Compare cluster assignments between two runs
-- Parameters: @old_run_id, @new_run_id
SELECT 
  COALESCE(old.job_posting_id, new.job_posting_id) AS job_posting_id,
  old.cluster_id AS old_cluster,
  old.cluster_name AS old_cluster_name,
  new.cluster_id AS new_cluster,
  new.cluster_name AS new_cluster_name,
  CASE 
    WHEN old.cluster_id IS NULL THEN 'new'
    WHEN new.cluster_id IS NULL THEN 'removed'
    WHEN old.cluster_id = new.cluster_id THEN 'stable'
    ELSE 'changed'
  END AS status
FROM (
  SELECT * FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
  WHERE cluster_run_id = @old_run_id
) old
FULL OUTER JOIN (
  SELECT * FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
  WHERE cluster_run_id = @new_run_id
) new
ON old.job_posting_id = new.job_posting_id
ORDER BY status, job_posting_id;

-- 12. Cluster stability summary between runs
-- Parameters: @old_run_id, @new_run_id
WITH comparison AS (
  SELECT 
    CASE 
      WHEN old.cluster_id IS NULL THEN 'new'
      WHEN new.cluster_id IS NULL THEN 'removed'
      WHEN old.cluster_id = new.cluster_id THEN 'stable'
      ELSE 'changed'
    END AS status
  FROM (
    SELECT * FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
    WHERE cluster_run_id = @old_run_id
  ) old
  FULL OUTER JOIN (
    SELECT * FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
    WHERE cluster_run_id = @new_run_id
  ) new
  ON old.job_posting_id = new.job_posting_id
)
SELECT 
  status,
  COUNT(*) AS job_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM comparison
GROUP BY status
ORDER BY job_count DESC;

-- 13. Cluster version history for a specific job
-- Parameters: @job_posting_id
SELECT 
  cluster_id,
  cluster_name,
  cluster_run_id,
  cluster_model_id,
  cluster_version,
  is_active,
  created_at
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
WHERE job_posting_id = @job_posting_id
ORDER BY cluster_version DESC;

-- 14. List all cluster runs with summary
SELECT 
  cluster_run_id,
  cluster_model_id,
  MIN(created_at) AS run_start,
  MAX(created_at) AS run_end,
  COUNT(DISTINCT job_posting_id) AS jobs_clustered,
  COUNT(DISTINCT cluster_id) AS clusters_created,
  COUNTIF(is_active) AS active_assignments
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
GROUP BY cluster_run_id, cluster_model_id
ORDER BY run_start DESC;

-- 15. Cluster size changes across runs
-- Parameters: @old_run_id, @new_run_id
SELECT 
  COALESCE(old.cluster_name, new.cluster_name) AS cluster_name,
  old.size AS old_size,
  new.size AS new_size,
  (COALESCE(new.size, 0) - COALESCE(old.size, 0)) AS size_change
FROM (
  SELECT cluster_name, COUNT(*) AS size
  FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
  WHERE cluster_run_id = @old_run_id
  GROUP BY cluster_name
) old
FULL OUTER JOIN (
  SELECT cluster_name, COUNT(*) AS size
  FROM `sylvan-replica-478802-p4.brightdata_jobs.job_clusters`
  WHERE cluster_run_id = @new_run_id
  GROUP BY cluster_name
) new
ON old.cluster_name = new.cluster_name
ORDER BY ABS(COALESCE(new.size, 0) - COALESCE(old.size, 0)) DESC;
