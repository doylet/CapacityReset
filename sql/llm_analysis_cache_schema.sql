-- LLM Analysis Cache Schema
-- Caches LLM responses to avoid redundant API calls for identical content

CREATE TABLE IF NOT EXISTS `brightdata_jobs.llm_analysis_cache` (
  -- Cache key (hash of content + prompt template + model)
  cache_key STRING NOT NULL,
  
  -- Input content and configuration
  content_hash STRING NOT NULL,  -- SHA-256 hash of analyzed content
  prompt_template_version STRING NOT NULL,  -- Version of prompt used
  llm_model_version STRING NOT NULL,  -- Gemini model version
  analysis_type STRING NOT NULL,  -- 'theme_extraction', 'voice_analysis', 'narrative_analysis', 'content_generation'
  
  -- LLM response data
  llm_response JSON NOT NULL,  -- Raw LLM response
  parsed_result JSON NOT NULL,  -- Structured parsed result
  confidence_score FLOAT64,  -- Overall confidence 0.0-1.0
  
  -- Metadata
  tokens_used INT64 NOT NULL,
  response_time_ms INT64 NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  last_accessed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  access_count INT64 NOT NULL DEFAULT 1,
  
  -- TTL and invalidation
  expires_at TIMESTAMP NOT NULL,
  invalidated BOOLEAN NOT NULL DEFAULT FALSE,
  invalidation_reason STRING,
  
  PRIMARY KEY (cache_key)
)
PARTITION BY DATE(created_at)
CLUSTER BY analysis_type, llm_model_version, expires_at;

-- Create indexes for cleanup queries
CREATE OR REPLACE VIEW `brightdata_jobs.expired_llm_cache` AS
SELECT cache_key, created_at, expires_at
FROM `brightdata_jobs.llm_analysis_cache`
WHERE expires_at < CURRENT_TIMESTAMP() OR invalidated = TRUE;

-- Create view for cache statistics
CREATE OR REPLACE VIEW `brightdata_jobs.llm_cache_stats` AS
SELECT 
  analysis_type,
  llm_model_version,
  DATE(created_at) as date,
  COUNT(*) as total_entries,
  SUM(access_count) as total_accesses,
  AVG(access_count) as avg_accesses_per_entry,
  SUM(tokens_used) as total_tokens,
  AVG(response_time_ms) as avg_response_time_ms,
  COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP() AND NOT invalidated THEN 1 END) as active_entries,
  COUNT(CASE WHEN expires_at <= CURRENT_TIMESTAMP() OR invalidated THEN 1 END) as expired_entries
FROM `brightdata_jobs.llm_analysis_cache`
GROUP BY analysis_type, llm_model_version, DATE(created_at)
ORDER BY date DESC, analysis_type, llm_model_version;