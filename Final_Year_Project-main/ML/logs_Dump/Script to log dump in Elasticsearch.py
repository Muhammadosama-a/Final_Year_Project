from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import json
import urllib3

# Suppress SSL warnings (optional for insecure connections)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Connect to Elasticsearch
es = Elasticsearch(
    hosts=["https://172.12.2.13/app/home#/"],  # Use HTTPS if SSL is enabled
    basic_auth=("elastic", "mDkIsrfdPCqHX9XTeDbj"),  # Elasticsearch credentials
    verify_certs=False  # Set to False to disable SSL verification (Quick fix for development)
    # ca_certs="/path/to/certificate.pem"  # Uncomment for trusted certificates
)

# Load logs from a JSON file
log_file = "logs.json"  # Replace with your log file's path
try:
    with open(log_file, "r") as file:
        logs = json.load(file)  # Read all logs from the file
except Exception as e:
    print(f"Error reading log file: {e}")
    logs = []

# Prepare logs for bulk indexing
actions = [
    {"_index": "logs-index", "_source": log}  # Use "logs-index" or any desired index name
    for log in logs
]

# Dump all logs to Elasticsearch
try:
    bulk(es, actions)
    print(f"Successfully dumped {len(actions)} logs into Elasticsearch.")
except Exception as e:
    print(f"Error dumping logs: {e}")
