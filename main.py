import functions_framework
from api import call_brightdata

@functions_framework.http
def main(request):
    """HTTP Cloud Function entry point"""
    body, status = call_brightdata()
    return body, status, {"Content-Type": "application/json"}
