-- Table to store individual BrightData search queries
-- Each payload object becomes a separate record
CREATE TABLE IF NOT EXISTS `sylvan-replica-478802-p4.brightdata_jobs.request_queries` (
  -- Request identification
  request_id STRING NOT NULL,
  query_index INT64 NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  
  -- Search parameters
  location STRING NOT NULL,
  keyword STRING NOT NULL,
  country STRING,
  time_range STRING,
  job_type STRING,
  remote STRING,
  experience_level STRING,
  company STRING,
  location_radius STRING,
  
  -- Request metadata
  dataset_id STRING NOT NULL,
  gcs_prefix STRING NOT NULL,
  
  -- API response
  brightdata_response JSON,
  status STRING NOT NULL,
  
  -- Processing status
  processed BOOLEAN DEFAULT FALSE,
  processed_at TIMESTAMP,
  
  -- Composite primary key
  PRIMARY KEY (request_id, query_index) NOT ENFORCED
)
PARTITION BY DATE(timestamp)
CLUSTER BY location, keyword, processed;
