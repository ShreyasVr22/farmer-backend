#!/usr/bin/env python3
"""
Debug script to check what the API is returning for historical data
"""
import json
import requests
import sys

# Test the API
url = "http://127.0.0.1:8000/predict/next-month"
payload = {
    "latitude": 13.18,
    "longitude": 77.85,
    "location": "Kasaba, Doddaballapura"
}

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse JSON:")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    # Check for issues
    if data.get("status") == "success":
        summary = data.get("data", {}).get("summary", {})
        print(f"\nSummary Stats:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
            if value is None or (isinstance(value, float) and (value != value or value == float('inf'))):
                print(f"    ^ PROBLEM: {type(value)} - {value}")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
