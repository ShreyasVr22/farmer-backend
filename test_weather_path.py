#!/usr/bin/env python
"""Test weather data loading with absolute paths"""

from modules.weather_data import get_weather_data

data = get_weather_data()
if data is not None and len(data) > 0:
    print(f"✓ Weather data loaded successfully: {len(data)} records")
    print(f"✓ Date range: {data['date'].min()} to {data['date'].max()}")
else:
    print("✗ Failed to load weather data")
