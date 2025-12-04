-- Professional Themes Schema
-- Individual extracted concepts representing career focus, expertise areas, or value propositions

CREATE TABLE IF NOT EXISTS `professional_themes` (
  theme_id STRING NOT NULL,
  theme_name STRING NOT NULL,
  theme_category STRING NOT NULL,
  description STRING NOT NULL,
  keywords ARRAY<STRING> NOT NULL,
  confidence_score FLOAT64 NOT NULL,
  source_evidence STRING NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_at)
CLUSTER BY theme_category;
