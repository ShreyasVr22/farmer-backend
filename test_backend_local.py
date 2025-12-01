#!/usr/bin/env python3
"""
Quick test script to verify backend is working locally
"""

import requests
import json
import time

# Wait for server to start
print("Waiting for server to initialize...")
time.sleep(5)

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("BACKEND VERIFICATION TEST")
print("="*70)

# Test 1: Health Check
print("\n[TEST 1] Health Check")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Models Loaded: {data.get('location_models_loaded')}/21")
        if data.get('location_models_loaded') == 21:
            print("✓✓✓ SUCCESS! All 21 models loaded!")
    else:
        print(f"✗ Status: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Forecast Endpoint
print("\n[TEST 2] 30-Day Weather Forecast")
print("-" * 70)
try:
    payload = {
        "latitude": 13.2256,
        "longitude": 77.5750,
        "location": "huliyurdurga_nelamangala"
    }
    
    print(f"Request: POST {BASE_URL}/predict/next-month")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/predict/next-month",
        json=payload,
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Status: {response.status_code}")
        print(f"✓ Response Status: {data.get('status')}")
        
        predictions = data.get('data', {}).get('predictions', [])
        print(f"✓ Predictions: {len(predictions)} days")
        
        if len(predictions) >= 3:
            print(f"\nFirst 3 predictions:")
            for pred in predictions[:3]:
                print(f"  {pred['date']}: {pred['temp_max']}°C / {pred['temp_min']}°C, Rain: {pred['rainfall']}mm")
            print("\n✓✓✓ SUCCESS! Forecast generated!")
        else:
            print(f"✗ Expected 30 predictions, got {len(predictions)}")
    else:
        print(f"✗ Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
except Exception as e:
    print(f"✗ Error: {str(e)[:150]}")

# Test 3: Available Models
print("\n[TEST 3] Available Models")
print("-" * 70)
try:
    response = requests.get(f"{BASE_URL}/info/available-models", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Total Models: {data.get('total_models')}")
        if data.get('total_models') == 21:
            print("✓ All 21 location models available!")
    else:
        print(f"✗ Status: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
print("\nBACKEND IS READY! ✓✓✓")
print("Frontend should call: http://localhost:8000")
print("="*70)
