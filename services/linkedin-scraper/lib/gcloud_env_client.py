import os

BRIGHTDATA_API_TOKEN = os.environ.get("BRIGHTDATA_API_TOKEN", "")
BRIGHTDATA_DATASET_ID = os.environ.get("BRIGHTDATA_DATASET_ID", "gd_lpfll7v5hcqtkxl6l")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "")

# Optional: load full service account JSON from env or Secret Manager
GCS_SA_CLIENT_EMAIL = os.environ.get("GCS_SA_CLIENT_EMAIL", "")
GCS_SA_PRIVATE_KEY = os.environ.get("GCS_SA_PRIVATE_KEY", "")  # with \n newlines already escaped


