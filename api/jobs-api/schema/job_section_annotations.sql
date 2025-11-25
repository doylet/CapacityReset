-- Section Annotations Table for ML Training Data
-- This table stores developer annotations of job posting sections
-- to train ML models for automatic section detection

CREATE TABLE IF NOT EXISTS `your-project.your_dataset.job_section_annotations` (
  annotation_id STRING NOT NULL,
  job_posting_id STRING NOT NULL,
  section_text STRING NOT NULL,
  section_start_index INT64 NOT NULL,
  section_end_index INT64 NOT NULL,
  label STRING NOT NULL,
  contains_skills BOOL NOT NULL,
  annotator_id STRING NOT NULL,
  notes STRING,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  
  -- Metadata for partitioning
  _partition_date DATE NOT NULL DEFAULT CURRENT_DATE()
)
PARTITION BY _partition_date
OPTIONS(
  description="Section annotations for ML training data - identifies skill-relevant sections in job postings",
  require_partition_filter=false
);

-- Index for querying by job posting
CREATE INDEX IF NOT EXISTS idx_job_posting 
ON `your-project.your_dataset.job_section_annotations`(job_posting_id);

-- Index for querying by label
CREATE INDEX IF NOT EXISTS idx_label 
ON `your-project.your_dataset.job_section_annotations`(label);

-- Index for querying by creation date
CREATE INDEX IF NOT EXISTS idx_created_at 
ON `your-project.your_dataset.job_section_annotations`(created_at DESC);

-- Index for querying by annotator
CREATE INDEX IF NOT EXISTS idx_annotator 
ON `your-project.your_dataset.job_section_annotations`(annotator_id);

-- Index for filtering by skill-relevance
CREATE INDEX IF NOT EXISTS idx_contains_skills 
ON `your-project.your_dataset.job_section_annotations`(contains_skills);
