"""
Fetch historical weather data from Open-Meteo API
For Bangalore Rural district
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import os
from pathlib import Path

# Bangalore Rural coordinates
BANGALORE_RURAL_LAT = 13.2256
BANGALORE_RURAL_LON = 77.5750

def fetch_historical_weather():
    """
    Fetch historical weather data from Open-Meteo for past 3 years
    Returns: pandas DataFrame with weather data
    """
    
    # Calculate date range: last 3 years
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365*10)
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    # FIXED: daily parameters should be comma-separated in a single string
    params = {
        "latitude": BANGALORE_RURAL_LAT,
        "longitude": BANGALORE_RURAL_LON,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m,relative_humidity_2m",
        "timezone": "Asia/Kolkata",
        "temperature_unit": "celsius"
    }
    
    try:
        print(f"Fetching data from {start_date} to {end_date}...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract daily data
        daily_data = data.get("daily", {})
        
        # Create DataFrame
        df = pd.DataFrame({
            "date": pd.to_datetime(daily_data["time"]),
            "temp_max": daily_data["temperature_2m_max"],
            "temp_min": daily_data["temperature_2m_min"],
            "rainfall": daily_data["precipitation_sum"],
            "wind_speed": daily_data["windspeed_10m"],
            "humidity": daily_data["relative_humidity_2m"]
        })
        
        # Save to CSV for backup
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        csv_path = data_dir / "bangalore_rural_weather.csv"
        df.to_csv(csv_path, index=False)
        
        print(f"✓ Fetched {len(df)} records from Open-Meteo")
        print(f"✓ Saved to {csv_path}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error fetching weather data: {e}")
        return None


def load_local_weather_data():
    """
    Load weather data from local CSV if available
    """
    csv_path = Path("data/bangalore_rural_weather.csv")
    
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"])
        print(f"[OK] Loaded {len(df)} records from local CSV")
        return df
    else:
        print("[ERROR] No local weather data found. Run fetch_historical_weather() first.")
        return None


def get_weather_data():
    """
    Get weather data - tries local first, then fetches from API
    """
    df = load_local_weather_data()
    
    if df is None or len(df) < 365:  # If less than 1 year of data
        print("Fetching fresh data from Open-Meteo...")
        df = fetch_historical_weather()
    
    return df
