-- Brand Learning Events Schema
-- Captured user interaction for continuous improvement of brand analysis and generation

CREATE TABLE IF NOT EXISTS `brand_learning_events` (
  event_id STRING NOT NULL,
  brand_id STRING NOT NULL,
  event_type STRING NOT NULL,
  event_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  surface_id STRING,
  theme_id STRING,
  event_data JSON NOT NULL,
  user_feedback STRING,
  processed BOOL NOT NULL DEFAULT FALSE
)
PARTITION BY DATE(event_timestamp)
CLUSTER BY brand_id, event_type;
