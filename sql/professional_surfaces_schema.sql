-- Professional Surfaces Schema
-- Target platform or document type with specific formatting and tone requirements

CREATE TABLE IF NOT EXISTS `professional_surfaces` (
  surface_id STRING NOT NULL,
  surface_type STRING NOT NULL,
  surface_name STRING NOT NULL,
  content_requirements JSON NOT NULL,
  template_structure STRING NOT NULL,
  validation_rules JSON NOT NULL,
  active BOOL NOT NULL DEFAULT TRUE
)
CLUSTER BY surface_type;
