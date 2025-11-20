import os
import json
import urllib.request
import urllib.error

BRIGHTDATA_API_TOKEN = os.environ.get("BRIGHTDATA_API_TOKEN", "")
BRIGHTDATA_DATASET_ID = os.environ.get("BRIGHTDATA_DATASET_ID", "gd_lpfll7v5hcqtkxl6l")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "")

# Optional: load full service account JSON from env or Secret Manager
GCS_SA_CLIENT_EMAIL = os.environ.get("GCS_SA_CLIENT_EMAIL", "")
GCS_SA_PRIVATE_KEY = os.environ.get("GCS_SA_PRIVATE_KEY", "")  # with \n newlines already escaped


def build_request():
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "input": [
            {
                "location": "brisbane",
                "keyword": '"product management"',
                "country": "AU",
                "time_range": "Any time",
                "job_type": "Full-time",
                "remote": "Remote",
                "experience_level": "",
                "company": "",
                "location_radius": "",
            },
            {
                "location": "sydney",
                "keyword": '"product management"',
                "country": "AU",
                "time_range": "Any time",
                "job_type": "Full-time",
                "remote": "Remote",
                "experience_level": "",
                "company": "",
                "location_radius": "",
            },
            {
                "location": "melbourne",
                "keyword": '"product management"',
                "country": "AU",
                "time_range": "Any time",
                "job_type": "Full-time",
                "remote": "Remote",
                "experience_level": "",
                "company": "",
                "location_radius": "",
            },
        ],
        "deliver": {
            "type": "gcs",
            "filename": {
                "extension": "json",
                "template":"{[datetime]}-{[job-id]}"},
            "bucket": GCS_BUCKET,
            "credentials": {
                "client_email": GCS_SA_CLIENT_EMAIL,
                "private_key": GCS_SA_PRIVATE_KEY,
            },
            "directory": "raw/",
        },
    }

    data = json.dumps(payload).encode("utf-8")

    url = (
        "https://api.brightdata.com/datasets/v3/trigger"
        f"?dataset_id={BRIGHTDATA_DATASET_ID}"
        "&notify=false&include_errors=true"
        "&type=discover_new&discover_by=keyword"
    )

    return urllib.request.Request(url, headers=headers, data=data)


def call_brightdata():
    request = build_request()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            # Log parsed JSON for debugging
            try:
                parsed = json.loads(body)
                print(parsed)
            except json.JSONDecodeError:
                print("Non-JSON response:", body)
            return body, 200
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"Bright Data HTTPError {e.code}: {error_body}")
        return json.dumps({"error": error_body, "status": e.code}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return json.dumps({"error": str(e)}), 500
