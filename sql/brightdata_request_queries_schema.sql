-- Table to store individual BrightData search queries
-- Each query is a unique search that needs to be scraped
CREATE TABLE IF NOT EXISTS `sylvan-replica-478802-p4.brightdata_jobs.request_queries` (
  -- Primary key
  query_id STRING NOT NULL,
  
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
  
  -- Metadata
  created_at TIMESTAMP NOT NULL,
  created_by STRING,
  
  -- Scheduling
  scheduled_for TIMESTAMP,
  
  -- Scraping status
  scraped BOOLEAN NOT NULL DEFAULT FALSE,
  scraped_at TIMESTAMP,
  scrape_request_id STRING,
  
  -- Error tracking
  last_error STRING,
  retry_count INT64,
  
  -- Primary key
  PRIMARY KEY (query_id) NOT ENFORCED
)
PARTITION BY DATE(created_at)
CLUSTER BY scraped, location, keyword;
