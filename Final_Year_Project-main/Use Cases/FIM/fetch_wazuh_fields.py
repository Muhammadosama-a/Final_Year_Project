#!/usr/bin/env python3

from elasticsearch import Elasticsearch
import json
import datetime
import argparse

def fetch_wazuh_data():
    # Elasticsearch connection details
    es_host = "10.10.80.72"
    es_port = 9200
    es_user = "elastic"
    es_password = "mDkIsrfdPCqHX9XTeDbj"
    
    # Create a timestamp for the output file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"wazuh_data_{timestamp}.json"
    
    print(f"Connecting to Elasticsearch at {es_host}:{es_port}...")
    
    # Connect to Elasticsearch
    try:
        es = Elasticsearch(
            [f"{es_host}:{es_port}"],
            http_auth=(es_user, es_password),
            use_ssl=True,
            verify_certs=False,
            timeout=30
        )
        
        # Check if connection was successful
        if not es.ping():
            print("Failed to connect to Elasticsearch. Please check your connection details.")
            return
        
        print("Connected to Elasticsearch successfully!")
        
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
        
        # Execute the search
        print("Fetching data from Elasticsearch...")
        
        # Initialize scroll
        page = es.search(
            index="wazuh-alerts-4.x-*",
            body=body,
            scroll='2m',
            size=1000
        )
        
        scroll_id = page['_scroll_id']
        hits = page['hits']['hits']
        hit_count = len(hits)
        
        # Check if we found any data
        if hit_count == 0:
            print("No matching data found.")
            return
        
        print(f"Found initial batch of {hit_count} records. Retrieving all data...")
        
        # Process and write results
        with open(output_file, 'w') as f:
            # Process initial batch
            for hit in hits:
                record = {
                    "_index": hit.get("_index", ""),
                    "agent": {
                        "id": get_nested_value(hit, ["_source", "agent", "id"], ""),
                        "ip": get_nested_value(hit, ["_source", "agent", "ip"], ""),
                        "name": get_nested_value(hit, ["_source", "agent", "name"], "")
                    },
                    "data": {
                        "win": {
                            "eventdata": {
                                "authenticationPackageName": get_nested_value(hit, ["_source", "data", "win", "eventdata", "authenticationPackageName"], ""),
                                "elevatedToken": get_nested_value(hit, ["_source", "data", "win", "eventdata", "elevatedToken"], "")
                            }
                        }
                    }
                }
                f.write(json.dumps(record) + "\n")
            
            # Continue scrolling and processing
            total_hits = hit_count
            while len(hits) > 0:
                page = es.scroll(scroll_id=scroll_id, scroll='2m')
                scroll_id = page['_scroll_id']
                hits = page['hits']['hits']
                hit_count = len(hits)
                
                for hit in hits:
                    record = {
                        "_index": hit.get("_index", ""),
                        "agent": {
                            "id": get_nested_value(hit, ["_source", "agent", "id"], ""),
                            "ip": get_nested_value(hit, ["_source", "agent", "ip"], ""),
                            "name": get_nested_value(hit, ["_source", "agent", "name"], "")
                        },
                        "data": {
                            "win": {
                                "eventdata": {
                                    "authenticationPackageName": get_nested_value(hit, ["_source", "data", "win", "eventdata", "authenticationPackageName"], ""),
                                    "elevatedToken": get_nested_value(hit, ["_source", "data", "win", "eventdata", "elevatedToken"], "")
                                }
                            }
                        }
                    }
                    f.write(json.dumps(record) + "\n")
                
                total_hits += hit_count
                print(f"Processed {total_hits} records so far...")
        
        # Clear the scroll
        es.clear_scroll(scroll_id=scroll_id)
        print(f"Successfully exported {total_hits} records to {output_file}")
    
    except Exception as e:
        print(f"Error: {str(e)}")

def get_nested_value(obj, path, default=""):
    """
    Safely retrieve a nested value from a dictionary
    """
    current = obj
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

if __name__ == "__main__":
    fetch_wazuh_data()
