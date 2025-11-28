import functions_framework
from lib import call_brightdata, log_request_to_bigquery


@functions_framework.http
def main(request):
    """HTTP Cloud Function."""
    body, status, request_id, queries = call_brightdata()

    """ Log the request and response to BigQuery """
    log_request_to_bigquery(body, status, request_id, queries)

    return body, status, {"Content-Type": "application/json"}
