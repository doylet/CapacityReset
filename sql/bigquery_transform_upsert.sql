-- Transform and upsert LinkedIn job postings from raw BrightData responses
-- This merges data from the scrape_requests table into the job_postings table

MERGE `sylvan-replica-478802-p4.brightdata_jobs.job_postings` AS target
USING (
  -- Parse the JSON array in brightdata_response and flatten it
  SELECT
    request_id AS scrape_request_id,
    JSON_VALUE(job, '$.job_posting_id') AS job_posting_id,
    JSON_VALUE(job, '$.url') AS url,
    
    -- Job details
    JSON_VALUE(job, '$.job_title') AS job_title,
    JSON_VALUE(job, '$.job_summary') AS job_summary,
    JSON_VALUE(job, '$.job_description_formatted') AS job_description_formatted,
    JSON_VALUE(job, '$.job_location') AS job_location,
    
    -- Job characteristics
    JSON_VALUE(job, '$.job_seniority_level') AS job_seniority_level,
    JSON_VALUE(job, '$.job_function') AS job_function,
    JSON_VALUE(job, '$.job_employment_type') AS job_employment_type,
    JSON_VALUE(job, '$.job_industries') AS job_industries,
    
    -- Salary information
    SAFE_CAST(JSON_VALUE(job, '$.base_salary.min_amount') AS FLOAT64) AS base_salary_min_amount,
    SAFE_CAST(JSON_VALUE(job, '$.base_salary.max_amount') AS FLOAT64) AS base_salary_max_amount,
    JSON_VALUE(job, '$.base_salary.currency') AS base_salary_currency,
    JSON_VALUE(job, '$.base_salary.payment_period') AS base_salary_payment_period,
    
    -- Company information
    JSON_VALUE(job, '$.company_id') AS company_id,
    JSON_VALUE(job, '$.company_name') AS company_name,
    JSON_VALUE(job, '$.company_url') AS company_url,
    JSON_VALUE(job, '$.company_logo') AS company_logo,
    
    -- Job posting metadata
    JSON_VALUE(job, '$.job_posted_time') AS job_posted_time,
    SAFE.PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', JSON_VALUE(job, '$.job_posted_date')) AS job_posted_date,
    SAFE_CAST(JSON_VALUE(job, '$.job_num_applicants') AS INT64) AS job_num_applicants,
    
    -- Application details
    JSON_VALUE(job, '$.apply_link') AS apply_link,
    SAFE_CAST(JSON_VALUE(job, '$.application_availability') AS BOOL) AS application_availability,
    SAFE_CAST(JSON_VALUE(job, '$.is_easy_apply') AS BOOL) AS is_easy_apply,
    
    -- Job poster
    JSON_VALUE(job, '$.job_poster.name') AS job_poster_name,
    JSON_VALUE(job, '$.job_poster.title') AS job_poster_title,
    JSON_VALUE(job, '$.job_poster.url') AS job_poster_url,
    
    -- Discovery metadata
    JSON_VALUE(job, '$.discovery_input.location') AS discovery_location,
    JSON_VALUE(job, '$.discovery_input.keyword') AS discovery_keyword,
    JSON_VALUE(job, '$.discovery_input.country') AS discovery_country,
    JSON_VALUE(job, '$.discovery_input.time_range') AS discovery_time_range,
    JSON_VALUE(job, '$.discovery_input.job_type') AS discovery_job_type,
    JSON_VALUE(job, '$.discovery_input.remote') AS discovery_remote,
    JSON_VALUE(job, '$.discovery_input.experience_level') AS discovery_experience_level,
    
    -- Additional fields
    JSON_VALUE(job, '$.country_code') AS country_code,
    JSON_VALUE(job, '$.title_id') AS title_id,
    JSON_VALUE(job, '$.salary_standards') AS salary_standards,
    
    CURRENT_TIMESTAMP() AS ingestion_timestamp
    
  FROM `sylvan-replica-478802-p4.brightdata_jobs.scrape_requests`,
  UNNEST(JSON_QUERY_ARRAY(brightdata_response)) AS job
  WHERE status = '200'  -- Only process successful responses
    AND JSON_VALUE(job, '$.job_posting_id') IS NOT NULL  -- Must have a job_posting_id
) AS source

ON target.job_posting_id = source.job_posting_id

-- Update existing records if the new data is more recent
WHEN MATCHED AND source.ingestion_timestamp > target.ingestion_timestamp THEN
  UPDATE SET
    url = source.url,
    job_title = source.job_title,
    job_summary = source.job_summary,
    job_description_formatted = source.job_description_formatted,
    job_location = source.job_location,
    job_seniority_level = source.job_seniority_level,
    job_function = source.job_function,
    job_employment_type = source.job_employment_type,
    job_industries = source.job_industries,
    base_salary_min_amount = source.base_salary_min_amount,
    base_salary_max_amount = source.base_salary_max_amount,
    base_salary_currency = source.base_salary_currency,
    base_salary_payment_period = source.base_salary_payment_period,
    company_id = source.company_id,
    company_name = source.company_name,
    company_url = source.company_url,
    company_logo = source.company_logo,
    job_posted_time = source.job_posted_time,
    job_posted_date = source.job_posted_date,
    job_num_applicants = source.job_num_applicants,
    apply_link = source.apply_link,
    application_availability = source.application_availability,
    is_easy_apply = source.is_easy_apply,
    job_poster_name = source.job_poster_name,
    job_poster_title = source.job_poster_title,
    job_poster_url = source.job_poster_url,
    discovery_location = source.discovery_location,
    discovery_keyword = source.discovery_keyword,
    discovery_country = source.discovery_country,
    discovery_time_range = source.discovery_time_range,
    discovery_job_type = source.discovery_job_type,
    discovery_remote = source.discovery_remote,
    discovery_experience_level = source.discovery_experience_level,
    scrape_request_id = source.scrape_request_id,
    ingestion_timestamp = source.ingestion_timestamp,
    country_code = source.country_code,
    title_id = source.title_id,
    salary_standards = source.salary_standards

-- Insert new records
WHEN NOT MATCHED THEN
  INSERT (
    scrape_request_id,
    job_posting_id,
    url,
    job_title,
    job_summary,
    job_description_formatted,
    job_location,
    job_seniority_level,
    job_function,
    job_employment_type,
    job_industries,
    base_salary_min_amount,
    base_salary_max_amount,
    base_salary_currency,
    base_salary_payment_period,
    company_id,
    company_name,
    company_url,
    company_logo,
    job_posted_time,
    job_posted_date,
    job_num_applicants,
    apply_link,
    application_availability,
    is_easy_apply,
    job_poster_name,
    job_poster_title,
    job_poster_url,
    discovery_location,
    discovery_keyword,
    discovery_country,
    discovery_time_range,
    discovery_job_type,
    discovery_remote,
    discovery_experience_level,
    country_code,
    title_id,
    salary_standards,
    ingestion_timestamp
  )
  VALUES (
    source.scrape_request_id,
    source.job_posting_id,
    source.url,
    source.job_title,
    source.job_summary,
    source.job_description_formatted,
    source.job_location,
    source.job_seniority_level,
    source.job_function,
    source.job_employment_type,
    source.job_industries,
    source.base_salary_min_amount,
    source.base_salary_max_amount,
    source.base_salary_currency,
    source.base_salary_payment_period,
    source.company_id,
    source.company_name,
    source.company_url,
    source.company_logo,
    source.job_posted_time,
    source.job_posted_date,
    source.job_num_applicants,
    source.apply_link,
    source.application_availability,
    source.is_easy_apply,
    source.job_poster_name,
    source.job_poster_title,
    source.job_poster_url,
    source.discovery_location,
    source.discovery_keyword,
    source.discovery_country,
    source.discovery_time_range,
    source.discovery_job_type,
    source.discovery_remote,
    source.discovery_experience_level,
    source.country_code,
    source.title_id,
    source.salary_standards,
    source.ingestion_timestamp
  );
