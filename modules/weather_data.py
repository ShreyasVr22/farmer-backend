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
    Fetch historical weather data from Open-Meteo for past 5 years
    Returns: pandas DataFrame with weather data
    """
    
    # Calculate date range: last 5 years (reduced from 10 to avoid API 400 errors)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365*5)
    
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
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors in response
        if "error" in data and data["error"]:
            raise Exception(f"API Error: {data.get('reason', 'Unknown error')}")
        
        # Extract daily data
        daily_data = data.get("daily", {})
        
        if not daily_data or not daily_data.get("time"):
            raise Exception("Invalid response from Open-Meteo API")
        
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
        
    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout fetching weather data from Open-Meteo (API took too long)")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP Error fetching weather data: {e}")
        if e.response.status_code == 400:
            print(f"[ERROR] Bad Request - check date range or parameters")
        return None
    except Exception as e:
        print(f"[ERROR] Error fetching weather data: {e}")
        return None


def load_local_weather_data():
    """
    Load weather data from local CSV if available
    Tries multiple locations: bangalore_rural_weather.csv first, then any *_weather.csv
    """
    data_dir = Path("data")
    
    # Try primary file first
    csv_path = data_dir / "bangalore_rural_weather.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"])
        print(f"[OK] Loaded {len(df)} records from local CSV: {csv_path.name}")
        return df
    
    # Fallback: try to find any location-specific weather CSV
    csv_files = list(data_dir.glob("*_weather.csv"))
    if csv_files:
        csv_path = csv_files[0]  # Load the first available location
        try:
            df = pd.read_csv(csv_path)
            df["date"] = pd.to_datetime(df["date"])
            print(f"[OK] Loaded {len(df)} records from local CSV: {csv_path.name}")
            return df
        except Exception as e:
            print(f"[ERROR] Failed to load CSV {csv_path}: {e}")
            return None
    
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
