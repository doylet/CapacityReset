import os
from flask import Flask, request
from api import call_brightdata

app = Flask(__name__)

@app.route('/')
def hello():
    return 'CapacityReset - LinkedIn Jobs BrightData Webscraper'

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/trigger', methods=['POST', 'GET'])
def trigger():
    """Endpoint to trigger the BrightData job"""
    body, status = call_brightdata()
    return body, status, {"Content-Type": "application/json"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
