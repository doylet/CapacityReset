import functions_framework
from lib.brightdata_api import call_brightdata
from lib.bigquery_client import log_request_to_bigquery


@functions_framework.http
def main(request):
    """HTTP Cloud Function."""
    body, status = call_brightdata()

    """ Log the request and response to BigQuery """
    log_request_to_bigquery(body, status)

    return body, status, {"Content-Type": "application/json"}
