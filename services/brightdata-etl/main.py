"""
BrightData ETL Service - Transform raw LinkedIn job postings from GCS into structured BigQuery table

HTTP endpoint that:
1. Reads unprocessed scrape requests from BigQuery
2. Loads JSON files from GCS for each request
3. Transforms and upserts job postings into job_postings table
4. Marks requests as processed
"""
import functions_framework
from google.cloud import bigquery
from google.cloud import storage
from google.cloud import logging as cloud_logging
import logging
import json
import os

client = cloud_logging.Client(
    project="sylvan-replica-478802-p4",
)
client.setup_logging()

def load_json_from_gcs(bucket_name, gcs_prefix):
    """Load JSON files from GCS directory."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # List all files in the prefix
    blobs = bucket.list_blobs(prefix=gcs_prefix)
    
    all_jobs = []
    for blob in blobs:
        if blob.name.endswith('.json'):
            content = blob.download_as_text()
            jobs = json.loads(content)
            # BrightData returns array of jobs
            if isinstance(jobs, list):
                all_jobs.extend(jobs)
            else:
                all_jobs.append(jobs)
    
    return all_jobs


def transform_and_load_jobs(bigquery_client, jobs, scrape_request_id, project_id):
    """Transform job data and insert into BigQuery."""
    if not jobs:
        return 0
    
    rows_to_insert = []
    for job in jobs:
        # Only process if has job_posting_id
        if not job.get('job_posting_id'):
            continue
            
        row = {
            'scrape_request_id': scrape_request_id,
            'job_posting_id': str(job.get('job_posting_id')) if job.get('job_posting_id') else None,
            'url': job.get('url'),
            'job_title': job.get('job_title'),
            'job_summary': job.get('job_summary'),
            'job_description_formatted': job.get('job_description_formatted'),
            'job_location': job.get('job_location'),
            'job_seniority_level': job.get('job_seniority_level'),
            'job_function': job.get('job_function'),
            'job_employment_type': job.get('job_employment_type'),
            'job_industries': job.get('job_industries'),
            'company_id': str(job.get('company_id')) if job.get('company_id') else None,
            'company_name': job.get('company_name'),
            'company_url': job.get('company_url'),
            'company_logo': job.get('company_logo'),
            'job_posted_time': job.get('job_posted_time'),
            'job_posted_date': job.get('job_posted_date'),
            'job_num_applicants': int(job.get('job_num_applicants')) if job.get('job_num_applicants') else None,
            'apply_link': job.get('apply_link'),
            'application_availability': job.get('application_availability'),
            'is_easy_apply': job.get('is_easy_apply'),
            'country_code': job.get('country_code'),
            'title_id': str(job.get('title_id')) if job.get('title_id') else None,
            'salary_standards': job.get('salary_standards'),
        }
        
        # Handle nested objects with type conversion
        if 'base_salary' in job and job['base_salary']:
            min_amt = job['base_salary'].get('min_amount')
            max_amt = job['base_salary'].get('max_amount')
            row['base_salary_min_amount'] = float(min_amt) if min_amt else None
            row['base_salary_max_amount'] = float(max_amt) if max_amt else None
            row['base_salary_currency'] = job['base_salary'].get('currency')
            row['base_salary_payment_period'] = job['base_salary'].get('payment_period')
        
        if 'job_poster' in job and job['job_poster']:
            row['job_poster_name'] = job['job_poster'].get('name')
            row['job_poster_title'] = job['job_poster'].get('title')
            row['job_poster_url'] = job['job_poster'].get('url')
        
        if 'discovery_input' in job and job['discovery_input']:
            row['discovery_location'] = job['discovery_input'].get('location')
            row['discovery_keyword'] = job['discovery_input'].get('keyword')
            row['discovery_country'] = job['discovery_input'].get('country')
            row['discovery_time_range'] = job['discovery_input'].get('time_range')
            row['discovery_job_type'] = job['discovery_input'].get('job_type')
            row['discovery_remote'] = job['discovery_input'].get('remote')
            row['discovery_experience_level'] = job['discovery_input'].get('experience_level')
        
        rows_to_insert.append(row)
    
    if not rows_to_insert:
        return 0
    
    # Use MERGE for upsert
    table_id = f"{project_id}.brightdata_jobs.job_postings"
    
    # Create temp table with data
    temp_table_id = f"{project_id}.brightdata_jobs._temp_etl_{scrape_request_id.replace('-', '_')}"
    
    # Insert into temp table
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    load_job = bigquery_client.load_table_from_json(
        rows_to_insert, 
        temp_table_id,
        job_config=job_config
    )
    load_job.result()
    
    # MERGE from temp to main
    merge_query = f"""
    MERGE `{table_id}` AS target
    USING `{temp_table_id}` AS source
    ON target.job_posting_id = CAST(source.job_posting_id AS STRING)
    WHEN MATCHED THEN
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
        country_code = source.country_code,
        title_id = source.title_id,
        salary_standards = source.salary_standards,
        ingestion_timestamp = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
      INSERT (
        scrape_request_id, job_posting_id, url, job_title, job_summary,
        job_description_formatted, job_location, job_seniority_level,
        job_function, job_employment_type, job_industries,
        base_salary_min_amount, base_salary_max_amount, base_salary_currency,
        base_salary_payment_period, company_id, company_name, company_url,
        company_logo, job_posted_time, job_posted_date, job_num_applicants,
        apply_link, application_availability, is_easy_apply, job_poster_name,
        job_poster_title, job_poster_url, discovery_location, discovery_keyword,
        discovery_country, discovery_time_range, discovery_job_type,
        discovery_remote, discovery_experience_level, country_code, title_id,
        salary_standards, ingestion_timestamp
      )
      VALUES (
        source.scrape_request_id, source.job_posting_id, source.url,
        source.job_title, source.job_summary, source.job_description_formatted,
        source.job_location, source.job_seniority_level, source.job_function,
        source.job_employment_type, source.job_industries,
        source.base_salary_min_amount, source.base_salary_max_amount,
        source.base_salary_currency, source.base_salary_payment_period,
        source.company_id, source.company_name, source.company_url,
        source.company_logo, source.job_posted_time, source.job_posted_date,
        source.job_num_applicants, source.apply_link,
        source.application_availability, source.is_easy_apply,
        source.job_poster_name, source.job_poster_title, source.job_poster_url,
        source.discovery_location, source.discovery_keyword,
        source.discovery_country, source.discovery_time_range,
        source.discovery_job_type, source.discovery_remote,
        source.discovery_experience_level, source.country_code, source.title_id,
        source.salary_standards, CURRENT_TIMESTAMP()
      )
    """
    
    merge_job = bigquery_client.query(merge_query)
    merge_job.result()
    
    # Delete temp table
    bigquery_client.delete_table(temp_table_id, not_found_ok=True)
    
    return merge_job.num_dml_affected_rows


@functions_framework.http
def main(request):
    """
    HTTP Cloud Function to transform LinkedIn job postings from GCS.
    
    Processes unprocessed scrape requests by:
    1. Loading JSON from GCS
    2. Transforming and loading into job_postings table
    3. Marking request as processed
    
    Returns:
        JSON response with transformation results
    """
    try:
        bigquery_client = bigquery.Client()
        project_id = os.environ.get('GCP_PROJECT', 'sylvan-replica-478802-p4')
        bucket_name = os.environ.get('GCS_BUCKET', 'brightdata-linkedin-job-postings-raw')
        
        # Get unprocessed requests with gcs_prefix
        query = f"""
        SELECT request_id, gcs_prefix
        FROM `{project_id}.brightdata_jobs.scrape_requests`
        WHERE status = '200'
          AND gcs_prefix IS NOT NULL
          AND (processed IS NULL OR CAST(processed AS STRING) = 'false')
        ORDER BY timestamp ASC
        """
        
        print("Fetching unprocessed scrape requests...")
        query_job = bigquery_client.query(query)
        requests = list(query_job.result())
        
        if not requests:
            print("No unprocessed requests found")
            return {
                "status": "success",
                "requests_processed": 0,
                "jobs_affected": 0,
                "message": "No unprocessed requests to transform"
            }, 200
        
        print(f"Found {len(requests)} unprocessed requests")
        
        total_jobs_affected = 0
        processed_request_ids = []
        
        for row in requests:
            request_id = row['request_id']
            gcs_prefix = row['gcs_prefix']
            
            print(f"Processing request {request_id} from {gcs_prefix}")
            
            try:
                # Load jobs from GCS
                jobs = load_json_from_gcs(bucket_name, gcs_prefix)
                print(f"Loaded {len(jobs)} jobs from GCS")
                
                # Transform and load
                rows_affected = transform_and_load_jobs(bigquery_client, jobs, request_id, project_id)
                total_jobs_affected += rows_affected
                print(f"Processed {rows_affected} job postings")
                
                # Mark as processed
                update_query = f"""
                UPDATE `{project_id}.brightdata_jobs.scrape_requests`
                SET processed = 'true', processed_at = CURRENT_TIMESTAMP()
                WHERE request_id = '{request_id}'
                """
                bigquery_client.query(update_query).result()
                
                processed_request_ids.append(request_id)
                
            except Exception as e:
                print(f"Error processing request {request_id}: {str(e)}")
                logging.error(f"Error processing request {request_id}: {str(e)}")
                continue
        
        print(f"ETL completed. Processed {len(processed_request_ids)} requests, {total_jobs_affected} jobs affected")
        
        return {
            "status": "success",
            "requests_processed": len(processed_request_ids),
            "jobs_affected": total_jobs_affected,
            "message": f"Successfully processed {len(processed_request_ids)} requests and transformed {total_jobs_affected} job postings"
        }, 200
        
    except Exception as e:
        error_msg = f"ETL transformation failed: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }, 500
