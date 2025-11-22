-- BigQuery table schema for transformed LinkedIn job postings from BrightData
-- This table is designed for querying and analytics on job posting data

CREATE TABLE IF NOT EXISTS `sylvan-replica-478802-p4.brightdata_jobs.job_postings` (
  -- Primary identifiers
  job_posting_id STRING NOT NULL,
  url STRING,
  
  -- Job details
  job_title STRING,
  job_summary STRING,
  job_description_formatted STRING,
  job_location STRING,
  
  -- Job characteristics
  job_seniority_level STRING,
  job_function STRING,
  job_employment_type STRING,
  job_industries STRING,
  
  -- Salary information
  base_salary_min_amount FLOAT64,
  base_salary_max_amount FLOAT64,
  base_salary_currency STRING,
  base_salary_payment_period STRING,
  
  -- Company information
  company_id STRING,
  company_name STRING,
  company_url STRING,
  company_logo STRING,
  
  -- Job posting metadata
  job_posted_time STRING,  -- e.g., "1 week ago"
  job_posted_date TIMESTAMP,
  job_num_applicants INT64,
  
  -- Application details
  apply_link STRING,
  application_availability BOOL,
  is_easy_apply BOOL,
  
  -- Job poster (if available)
  job_poster_name STRING,
  job_poster_title STRING,
  job_poster_url STRING,
  
  -- Discovery metadata (from BrightData search)
  discovery_location STRING,
  discovery_keyword STRING,
  discovery_country STRING,
  discovery_time_range STRING,
  discovery_job_type STRING,
  discovery_remote STRING,
  discovery_experience_level STRING,
  
  -- Internal tracking
  scrape_request_id STRING,  -- Links back to scrape_requests table
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  
  -- Additional fields
  country_code STRING,
  title_id STRING,
  salary_standards STRING
)
PARTITION BY DATE(job_posted_date)
CLUSTER BY company_name, job_location, job_employment_type
OPTIONS(
  description="Transformed LinkedIn job postings scraped via BrightData"
);

-- Create a view for easy querying of active jobs
CREATE OR REPLACE VIEW `sylvan-replica-478802-p4.brightdata_jobs.active_job_postings` AS
SELECT 
  *,
  DATE_DIFF(CURRENT_DATE(), DATE(job_posted_date), DAY) AS days_since_posted
FROM `sylvan-replica-478802-p4.brightdata_jobs.job_postings`
WHERE job_posted_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
ORDER BY job_posted_date DESC;
