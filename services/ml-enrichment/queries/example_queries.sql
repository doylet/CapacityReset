-- Example Queries for ML Enrichment Data

-- 1. Find jobs by required skills
SELECT 
  jp.job_posting_id,
  jp.job_title,
  jp.company_name,
  jp.job_location,
  ARRAY_AGG(DISTINCT js.skill_name ORDER BY js.skill_name) as required_skills,
  COUNT(DISTINCT js.skill_name) as total_skills
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_skills` js
  ON jp.job_posting_id = js.job_posting_id
WHERE js.skill_name IN ('Python', 'Aws', 'Kubernetes', 'Docker')
  AND js.confidence_score > 0.5
GROUP BY jp.job_posting_id, jp.job_title, jp.company_name, jp.job_location
HAVING COUNT(DISTINCT js.skill_name) >= 3
ORDER BY total_skills DESC, jp.job_posted_date DESC
LIMIT 20;

-- 2. Get skill distribution by category
SELECT 
  js.skill_category,
  COUNT(DISTINCT js.job_posting_id) as jobs_count,
  COUNT(*) as total_mentions,
  ARRAY_AGG(DISTINCT js.skill_name ORDER BY js.skill_name LIMIT 10) as top_skills
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_skills` js
WHERE js.confidence_score > 0.6
GROUP BY js.skill_category
ORDER BY jobs_count DESC;

-- 3. Find jobs similar to a specific job (semantic search using vector similarity)
-- Note: This requires BigQuery Vector Search which uses ML.DISTANCE or similar functions
-- First, get the embedding for the reference job
WITH reference_job AS (
  SELECT embedding
  FROM `sylvan-replica-478802-p4.brightdata_jobs.job_embeddings`
  WHERE job_posting_id = '4312986526'  -- Replace with actual job ID
    AND chunk_type = 'full_description'
  LIMIT 1
),
-- Then find similar jobs based on cosine similarity
similar_jobs AS (
  SELECT 
    je.job_posting_id,
    je.chunk_type,
    -- Cosine similarity: 1 - (cosine distance)
    -- Note: Implement proper vector similarity calculation
    1 - (
      -- This is a placeholder - BigQuery Vector Search has specific functions for this
      -- Use ML.DISTANCE or COSINE_DISTANCE when available
      0.0
    ) as similarity_score
  FROM `sylvan-replica-478802-p4.brightdata_jobs.job_embeddings` je
  CROSS JOIN reference_job ref
  WHERE je.chunk_type = 'full_description'
    AND je.job_posting_id != '4312986526'
)
SELECT 
  jp.job_posting_id,
  jp.job_title,
  jp.company_name,
  jp.job_location,
  jp.salary_low,
  jp.salary_high,
  sj.similarity_score
FROM similar_jobs sj
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp
  ON sj.job_posting_id = jp.job_posting_id
ORDER BY sj.similarity_score DESC
LIMIT 10;

-- 4. Jobs that need enrichment
SELECT 
  jp.job_posting_id,
  jp.job_title,
  jp.company_name,
  jp.job_posted_date,
  COUNTIF(je_skills.enrichment_id IS NOT NULL) > 0 as has_skills,
  COUNTIF(je_embed.enrichment_id IS NOT NULL) > 0 as has_embeddings
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp
LEFT JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_enrichments` je_skills
  ON jp.job_posting_id = je_skills.job_posting_id
  AND je_skills.enrichment_type = 'skills_extraction'
  AND je_skills.status = 'success'
LEFT JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_enrichments` je_embed
  ON jp.job_posting_id = je_embed.job_posting_id
  AND je_embed.enrichment_type = 'embeddings'
  AND je_embed.status = 'success'
WHERE jp.job_summary IS NOT NULL
  AND jp.job_description_formatted IS NOT NULL
GROUP BY jp.job_posting_id, jp.job_title, jp.company_name, jp.job_posted_date
HAVING NOT has_skills OR NOT has_embeddings
ORDER BY jp.job_posted_date DESC
LIMIT 100;

-- 5. Enrichment pipeline health check
SELECT 
  DATE(created_at) as enrichment_date,
  enrichment_type,
  status,
  COUNT(*) as count,
  AVG(CAST(JSON_EXTRACT_SCALAR(metadata, '$.skills_count') AS INT64)) as avg_skills_per_job,
  AVG(CAST(JSON_EXTRACT_SCALAR(metadata, '$.chunks_count') AS INT64)) as avg_chunks_per_job
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_enrichments`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY enrichment_date, enrichment_type, status
ORDER BY enrichment_date DESC, enrichment_type;

-- 6. Most in-demand skills
SELECT 
  js.skill_name,
  js.skill_category,
  COUNT(DISTINCT js.job_posting_id) as job_count,
  AVG(js.confidence_score) as avg_confidence,
  ROUND(COUNT(DISTINCT js.job_posting_id) * 100.0 / (
    SELECT COUNT(DISTINCT job_posting_id) 
    FROM `sylvan-replica-478802-p4.brightdata_jobs.job_skills`
  ), 2) as percentage_of_jobs
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_skills` js
WHERE js.confidence_score > 0.6
GROUP BY js.skill_name, js.skill_category
HAVING job_count >= 3
ORDER BY job_count DESC
LIMIT 50;

-- 7. Skills by company
SELECT 
  jp.company_name,
  js.skill_category,
  ARRAY_AGG(DISTINCT js.skill_name ORDER BY js.skill_name LIMIT 10) as skills,
  COUNT(DISTINCT jp.job_posting_id) as jobs_count
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_postings` jp
JOIN `sylvan-replica-478802-p4.brightdata_jobs.job_skills` js
  ON jp.job_posting_id = js.job_posting_id
WHERE js.confidence_score > 0.6
GROUP BY jp.company_name, js.skill_category
HAVING jobs_count >= 2
ORDER BY jp.company_name, jobs_count DESC;

-- 8. Embedding chunk analysis
SELECT 
  chunk_type,
  COUNT(*) as chunk_count,
  AVG(content_tokens) as avg_tokens,
  MIN(content_tokens) as min_tokens,
  MAX(content_tokens) as max_tokens
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_embeddings`
GROUP BY chunk_type
ORDER BY chunk_count DESC;
