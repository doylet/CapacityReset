-- Brand Theme Associations Schema
-- Many-to-Many relationship between brands and themes

CREATE TABLE IF NOT EXISTS `brand_theme_associations` (
  brand_id STRING NOT NULL,
  theme_id STRING NOT NULL,
  relevance_score FLOAT64 NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY brand_id;
