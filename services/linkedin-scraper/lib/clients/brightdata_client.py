import json
import urllib.request
import urllib.error
import uuid
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from lib.gcloud_env_client import (
    BRIGHTDATA_API_TOKEN,
    BRIGHTDATA_DATASET_ID,
    GCS_BUCKET,
    GCS_SA_CLIENT_EMAIL,
    GCS_SA_PRIVATE_KEY,
)


@dataclass
class JobSearchQuery:
    """Parameters for a single job search query."""
    location: str
    keyword: str
    country: str = "AU"
    time_range: str = "Any time"
    job_type: str = "Full-time"
    remote: str = "Remote"
    experience_level: str = ""
    company: str = ""
    location_radius: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API payload."""
        return {
            "location": self.location,
            "keyword": self.keyword,
            "country": self.country,
            "time_range": self.time_range,
            "job_type": self.job_type,
            "remote": self.remote,
            "experience_level": self.experience_level,
            "company": self.company,
            "location_radius": self.location_radius,
        }


@dataclass
class BrightDataConfig:
    """Configuration for BrightData API request."""
    queries: List[JobSearchQuery] = field(default_factory=list)
    notify: bool = False
    include_errors: bool = True
    request_type: str = "discover_new"
    discover_by: str = "keyword"
    gcs_filename_extension: str = "json"
    gcs_filename_template: str = "{[datetime]}"
    
    @staticmethod
    def default_product_management_queries() -> List[JobSearchQuery]:
        """Default queries for product management roles in AU."""
        return [
            JobSearchQuery(location="brisbane", keyword='"product management"'),
            JobSearchQuery(location="sydney", keyword='"product management"'),
            JobSearchQuery(location="melbourne", keyword='"product management"'),
        ]


def build_request(
    queries: Optional[List[JobSearchQuery]] = None,
    config: Optional[BrightDataConfig] = None
):
    """
    Build BrightData API request with configurable parameters.
    
    Args:
        queries: List of job search queries. If None, uses default product management queries.
        config: BrightData configuration. If None, uses default config.
        
    Returns:
        Tuple of (urllib Request object, request_id string)
    """
    # Use defaults if not provided
    if config is None:
        config = BrightDataConfig()
    
    if queries is None:
        queries = BrightDataConfig.default_product_management_queries()
    
    # Update config with provided queries
    config.queries = queries
    
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}",
        "Content-Type": "application/json",
    }

    request_id = str(uuid.uuid4())
    gcs_prefix = f"raw/{request_id}/"

    payload = {
        "input": [query.to_dict() for query in config.queries],
        "deliver": {
            "type": "gcs",
            "filename": {
                "extension": config.gcs_filename_extension,
                "template": config.gcs_filename_template
            },
            "bucket": GCS_BUCKET,
            "credentials": {
                "client_email": GCS_SA_CLIENT_EMAIL,
                "private_key": GCS_SA_PRIVATE_KEY,
            },
            "directory": gcs_prefix,
        },
    }

    data = json.dumps(payload).encode("utf-8")

    url = (
        "https://api.brightdata.com/datasets/v3/trigger"
        f"?dataset_id={BRIGHTDATA_DATASET_ID}"
        f"&notify={'true' if config.notify else 'false'}"
        f"&include_errors={'true' if config.include_errors else 'false'}"
        f"&type={config.request_type}"
        f"&discover_by={config.discover_by}"
    )

    return urllib.request.Request(url, headers=headers, data=data), request_id


def call_brightdata(
    queries: Optional[List[JobSearchQuery]] = None,
    config: Optional[BrightDataConfig] = None
):
    """
    Call BrightData API with configurable parameters.
    
    Args:
        queries: List of job search queries. If None, uses default product management queries.
        config: BrightData configuration. If None, uses default config.
        
    Returns:
        Tuple of (response body, status code, request_id, queries_dict)
    """
    # Use defaults if not provided
    if queries is None:
        queries = BrightDataConfig.default_product_management_queries()
    
    request, request_id = build_request(queries, config)
    
    # Convert queries to dict list for logging
    queries_dict = [query.to_dict() for query in queries]
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            # Log parsed JSON for debugging
            try:
                parsed = json.loads(body)
                print(parsed)
            except json.JSONDecodeError:
                print("Non-JSON response:", body)
            return body, 200, request_id, queries_dict
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"Bright Data HTTPError {e.code}: {error_body}")
        return json.dumps({"error": error_body, "status": e.code}), 500, request_id, queries_dict
    except Exception as e:
        print(f"Unexpected error: {e}")
        return json.dumps({"error": str(e)}), 500, request_id, queries_dict
