-- Enhanced Brand Representations Schema v2
-- Extends existing brand analysis with LLM metadata and tracking

-- Create enhanced brand_representations table with LLM support
CREATE TABLE IF NOT EXISTS `brightdata_jobs.brand_representations_v2` (
  job_posting_id STRING NOT NULL,
  analysis_type STRING NOT NULL,  -- 'keyword', 'llm', 'hybrid'
  
  -- Theme extraction results
  themes JSON,  -- [{"theme": "strategic leadership", "confidence": 0.95, "evidence": ["coordinated cross-functional initiatives"], "source": "llm"}]
  
  -- Voice characteristics
  voice_characteristics JSON,  -- {"tone": "professional", "formality": 0.8, "energy": 0.6, "communication_style": "data-driven"}
  
  -- Narrative arc analysis  
  narrative_arc JSON,  -- {"progression": "technical_to_leadership", "value_proposition": "innovation_driver", "future_positioning": "strategic_technologist"}
  
  -- Content generation results
  generated_content JSON,  -- {"linkedin_summary": "...", "cv_summary": "...", "portfolio_intro": "..."}
  
  -- LLM metadata
  llm_model_version STRING,  -- 'gemini-flash-1.5', 'gemini-pro-1.5'
  llm_tokens_used INT64,
  llm_processing_time_ms INT64,
  llm_confidence_score FLOAT64,  -- Overall analysis confidence 0.0-1.0
  
  -- Processing metadata
  analysis_version STRING NOT NULL,  -- For tracking model iterations
  processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  processing_status STRING NOT NULL,  -- 'success', 'partial', 'fallback', 'failed'
  fallback_reason STRING,  -- Reason if fell back to keyword analysis
  
  -- Feedback and learning
  user_feedback JSON,  -- {"theme_relevance": 5, "voice_accuracy": 4, "content_quality": 5}
  feedback_provided_at TIMESTAMP,
  
  PRIMARY KEY (job_posting_id, analysis_type)
)
PARTITION BY DATE(processed_at)
CLUSTER BY analysis_type, llm_model_version;

-- Create indexes for common query patterns
-- Note: BigQuery doesn't support traditional indexes, clustering handles this

-- Create view for current best analysis (prioritize LLM over keyword)
CREATE OR REPLACE VIEW `brightdata_jobs.current_brand_analysis` AS
SELECT 
  job_posting_id,
  CASE 
    WHEN llm_analysis.job_posting_id IS NOT NULL THEN 'llm'
    WHEN keyword_analysis.job_posting_id IS NOT NULL THEN 'keyword'
    ELSE NULL 
  END as best_analysis_type,
  COALESCE(llm_analysis.themes, keyword_analysis.themes) as themes,
  COALESCE(llm_analysis.voice_characteristics, keyword_analysis.voice_characteristics) as voice_characteristics,
  COALESCE(llm_analysis.narrative_arc, keyword_analysis.narrative_arc) as narrative_arc,
  COALESCE(llm_analysis.generated_content, keyword_analysis.generated_content) as generated_content,
  COALESCE(llm_analysis.analysis_version, keyword_analysis.analysis_version) as analysis_version,
  COALESCE(llm_analysis.processed_at, keyword_analysis.processed_at) as processed_at,
  llm_analysis.llm_model_version,
  llm_analysis.llm_confidence_score
FROM 
  (SELECT * FROM `brightdata_jobs.brand_representations_v2` 
   WHERE analysis_type = 'llm' AND processing_status = 'success') llm_analysis
FULL OUTER JOIN
  (SELECT * FROM `brightdata_jobs.brand_representations_v2` 
   WHERE analysis_type = 'keyword' AND processing_status = 'success') keyword_analysis
USING (job_posting_id);