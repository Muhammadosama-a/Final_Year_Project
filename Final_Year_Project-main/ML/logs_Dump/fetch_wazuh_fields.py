from elasticsearch import Elasticsearch
import json
import datetime
import os
import argparse

def fetch_wazuh_specific_fields(host, port, username, password, output_file=None, use_ssl=True):
    """
    Connect to Elasticsearch and fetch specific Wazuh log fields
    """
    # Set up connection parameters
    connection_params = {
        'hosts': [f'{host}:{port}'],
        'http_auth': (username, password),
        'timeout': 30
    }
    
    if use_ssl:
        connection_params['use_ssl'] = True
        connection_params['verify_certs'] = False  # For development only
    
    try:
        # Connect to Elasticsearch
        es = Elasticsearch(**connection_params)
        if not es.ping():
            print("Failed to connect to Elasticsearch")
            return
        
        print(f"Successfully connected to Elasticsearch at {host}:{port}")
        
        # Define the query to fetch specific fields
        body = {
            "_source": [
                "_index",
                "agent.id",
                "agent.ip",
                "agent.name",
                "data.win.eventdata.authenticationPackageName",
                "data.win.eventdata.elevatedToken"
            ],
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "data.win.eventdata.authenticationPackageName"}},
                        {"exists": {"field": "data.win.eventdata.elevatedToken"}}
                    ]
                }
            },
            "sort": [
                {"@timestamp": {"order": "desc"}}
            ]
        }
        
        # Use the scroll API for handling large result sets
        page = es.search(
            index="wazuh-alerts-4.x-*",
            body=body,
            scroll='2m',
            size=1000
        )
        
        scroll_id = page['_scroll_id']
        hits = page['hits']['hits']
        total_hits = page['hits']['total']['value'] if isinstance(page['hits']['total'], dict) else page['hits']['total']
        
        print(f"Found {total_hits} matching records")
        
        # Set up output file
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"wazuh_specific_fields_{timestamp}.json"
        
        # Process and write results
        count = 0
        with open(output_file, 'w') as f:
            while hits:
                for hit in hits:
                    result = {
                        "_index": hit.get("_index", ""),
                        "agent": {
                            "id": get_nested_field(hit, "_source.agent.id", ""),
                            "ip": get_nested_field(hit, "_source.agent.ip", ""),
                            "name": get_nested_field(hit, "_source.agent.name", "")
                        },
                        "data": {
                            "win": {
                                "eventdata": {
                                    "authenticationPackageName": get_nested_field(hit, "_source.data.win.eventdata.authenticationPackageName", ""),
                                    "elevatedToken": get_nested_field(hit, "_source.data.win.eventdata.elevatedToken", "")
                                }
                            }
                        }
                    }
                    f.write(json.dumps(result) + "\n")
                    count += 1
                
                # Get next batch
                page = es.scroll(scroll_id=scroll_id, scroll='2m')
                scroll_id = page['_scroll_id']
                hits = page['hits']['hits']
                
                # Print progress
                if count % 1000 == 0:
                    print(f"Processed {count} records so far...")
        
        # Clear the scroll when done
        es.clear_scroll(scroll_id=scroll_id)
        print(f"Successfully exported {count} records to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")

def get_nested_field(hit, field_path, default_value=""):
    """
    Safely extract nested field values from Elasticsearch hits
    """
    parts = field_path.split(".")
    current = hit
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default_value
    
    return current

def main():
    parser = argparse.ArgumentParser(description='Fetch specific Wazuh fields from Elasticsearch')
    
    # Connection params
    parser.add_argument('--host', required=True, help='Elasticsearch host')
    parser.add_argument('--port', default=9200, type=int, help='Elasticsearch port')
    parser.add_argument('--user', required=True, help='Elasticsearch username')
    parser.add_argument('--password', required=True, help='Elasticsearch password')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL connection')
    
    # Output params
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    fetch_wazuh_specific_fields(
        args.host,
        args.port,
        args.user,
        args.password,
        args.output,
        not args.no_ssl
    )

if __name__ == "__main__":
    main()