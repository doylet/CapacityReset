-- Brand Representations Schema
-- Core professional identity model containing extracted themes, voice characteristics, and narrative structure

CREATE TABLE IF NOT EXISTS `brand_representations` (
  brand_id STRING NOT NULL,
  user_id STRING NOT NULL,
  source_document_url STRING NOT NULL,
  linkedin_profile_url STRING,
  professional_themes JSON NOT NULL,
  voice_characteristics JSON NOT NULL,
  narrative_arc JSON NOT NULL,
  confidence_scores JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  version INTEGER NOT NULL DEFAULT 1
)
PARTITION BY DATE(created_at)
CLUSTER BY user_id;
