-- Content Generations Schema
-- Individual piece of branded content with metadata, version tracking, and feedback history

CREATE TABLE IF NOT EXISTS `content_generations` (
  generation_id STRING NOT NULL,
  brand_id STRING NOT NULL,
  surface_id STRING NOT NULL,
  content_text STRING NOT NULL,
  generation_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  generation_version INTEGER NOT NULL DEFAULT 1,
  generation_prompt STRING NOT NULL,
  consistency_score FLOAT64,
  user_satisfaction_rating INTEGER,
  edit_count INTEGER NOT NULL DEFAULT 0,
  word_count INTEGER NOT NULL,
  status STRING NOT NULL DEFAULT 'draft'
)
PARTITION BY DATE(generation_timestamp)
CLUSTER BY brand_id, surface_id;
