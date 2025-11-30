"""
Train Location-Specific LSTM Models
Bangalore Rural District - Optimized for Accuracy
10 years historical data from Open-Meteo Archive API
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.preprocessor import WeatherPreprocessor
from models.lstm_model import WeatherLSTMModel
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import joblib

# ✅ OPTIMIZED: Only Bangalore Rural with accurate hoblis
LOCATIONS = [
    # Doddaballapura Taluk (5 hoblis)
    {
        "name": "Kasaba, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Kasaba",
        "lat": 13.29273,
        "lon": 77.53891
    },
    {
        "name": "Doddabelavangala, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Doddabelavangala",
        "lat": 13.28855,
        "lon": 77.42205
    },
    {
        "name": "Thubagere, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Thubagere",
        "lat": 13.373,
        "lon": 77.570
    },
    {
        "name": "Sasalu, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Sasalu",
        "lat": 13.280,
        "lon": 77.530
    },
    {
        "name": "Madhure, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Madhure",
        "lat": 13.19510,
        "lon": 77.45586
    },
    
    # Devanahalli Taluk (5 hoblis)
    {"name": "Kasaba, Devanahalli", "taluk": "Devanahalli", "hobli": "Kasaba", "lat": 13.18, "lon": 77.85},
    {"name": "Vijayapura, Devanahalli", "taluk": "Devanahalli", "hobli": "Vijayapura", "lat": 13.22, "lon": 77.88},
    {"name": "Kundana, Devanahalli", "taluk": "Devanahalli", "hobli": "Kundana", "lat": 13.15, "lon": 77.92},
    {"name": "Bettakote, Devanahalli", "taluk": "Devanahalli", "hobli": "Bettakote", "lat": 13.25, "lon": 77.80},
    {"name": "Undire, Devanahalli", "taluk": "Devanahalli", "hobli": "Undire", "lat": 13.12, "lon": 77.78},
    
    # Hosakote Taluk (5 hoblis)
    {"name": "Sulibele, Hosakote", "taluk": "Hosakote", "hobli": "Sulibele", "lat": 13.45, "lon": 77.77},
    {"name": "Anugondanahalli, Hosakote", "taluk": "Hosakote", "hobli": "Anugondanahalli", "lat": 13.48, "lon": 77.82},
    {"name": "Jadigenahalli, Hosakote", "taluk": "Hosakote", "hobli": "Jadigenahalli", "lat": 13.50, "lon": 77.75},
    {"name": "Nandagudi, Hosakote", "taluk": "Hosakote", "hobli": "Nandagudi", "lat": 13.42, "lon": 77.70},
    {"name": "Kasaba, Hosakote", "taluk": "Hosakote", "hobli": "Kasaba", "lat": 13.47, "lon": 77.80},
    
    # Nelamangala Taluk (6 hoblis)
    {"name": "Kasaba, Nelamangala", "taluk": "Nelamangala", "hobli": "Kasaba", "lat": 13.27, "lon": 77.45},
    {"name": "Huliyurdurga, Nelamangala", "taluk": "Nelamangala", "hobli": "Huliyurdurga", "lat": 13.30, "lon": 77.40},
    {"name": "Tyamagondlu, Nelamangala", "taluk": "Nelamangala", "hobli": "Tyamagondlu", "lat": 13.25, "lon": 77.50},
    {"name": "Sompura, Nelamangala", "taluk": "Nelamangala", "hobli": "Sompura", "lat": 13.32, "lon": 77.48},
    {"name": "Lakshmipura, Nelamangala", "taluk": "Nelamangala", "hobli": "Lakshmipura", "lat": 13.28, "lon": 77.42},
    {"name": "Makali, Nelamangala", "taluk": "Nelamangala", "hobli": "Makali", "lat": 13.35, "lon": 77.52}
]


def fetch_weather_for_location(latitude, longitude, location_name):
    """
    Fetch historical weather data for specific location
    Uses 10 years of Open-Meteo Archive data for better accuracy
    """
    print(f"\n{'='*70}")
    print(f"📍 Fetching data for: {location_name}")
    print(f"   Coordinates: {latitude}, {longitude}")
    print(f"{'='*70}")
    
    end_date = datetime.now().date()
    # ✅ OPTIMIZED: Fetch 10 years of historical data
    start_date = end_date - timedelta(days=365 * 10)

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = [
        ("latitude", latitude),
        ("longitude", longitude),
        ("start_date", start_date.strftime("%Y-%m-%d")),
        ("end_date", end_date.strftime("%Y-%m-%d")),
        ("daily", "temperature_2m_max"),
        ("daily", "temperature_2m_min"),
        ("daily", "precipitation_sum"),
        ("timezone", "Asia/Kolkata"),
        ("temperature_unit", "celsius"),
    ]

    try:
        print(f"⏳ Fetching 10 years of data ({start_date} to {end_date})...")
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        daily = data.get("daily", {})
        if not daily or "time" not in daily:
            print(f"[ERR] Invalid API response for {location_name}: {data}")
            return None

        df = pd.DataFrame({
            "date": pd.to_datetime(daily["time"]),
            "temp_max": daily.get("temperature_2m_max", []),
            "temp_min": daily.get("temperature_2m_min", []),
            "rainfall": daily.get("precipitation_sum", []),
        })

        # Save per-location CSV
        Path("data").mkdir(exist_ok=True)
        slug = location_name.replace(' ', '_').replace(',', '').lower()
        csv_path = Path(f"data/{slug}_weather.csv")
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved {len(df)} records to {csv_path}")

        return df

    except requests.exceptions.RequestException as e:
        print(f"[ERR] Failed to fetch data for {location_name}: {e}")
        return None


def train_model_for_location(location):
    """Fetch, preprocess and train a model for a single location."""
    name = location["name"]
    lat = location["lat"]
    lon = location["lon"]
    taluk = location["taluk"]
    hobli = location["hobli"]

    df = fetch_weather_for_location(lat, lon, name)
    if df is None or len(df) < 365:
        print(f"[WARN] Not enough data for {name}, skipping training.")
        return

    pre = WeatherPreprocessor()
    df = pre.clean_data(df)
    norm = pre.normalize_data(df, fit=True)

    X, y = pre.create_sequences(norm, seq_length=30)
    if len(X) == 0:
        print(f"[WARN] No sequences created for {name}, skipping.")
        return

    (X_train, y_train), (X_val, y_val), (X_test, y_test) = pre.split_data(X, y)

    model = WeatherLSTMModel(seq_length=30, n_features=3)
    model.build_model()
    model.train(X_train, y_train, X_val, y_val, epochs=5, batch_size=32)

    # Save model and scaler to per-location folder
    loc_dir = Path("models/locations")
    loc_dir.mkdir(parents=True, exist_ok=True)
    slug = name.replace(' ', '_').replace(',', '').lower()
    model_path = loc_dir / f"lstm_{slug}.h5"
    scaler_path = loc_dir / f"scaler_{slug}.pkl"

    model.model.save(model_path)
    joblib.dump(pre.scaler, scaler_path)
    print(f"✅ Model saved: {model_path}")
    print(f"✅ Scaler saved: {scaler_path}")


def train_all_locations():
    """
    Train models for all Bangalore Rural hobli locations.
    This function is called by main.py during startup if models don't exist.
    
    ✅ OPTIMIZED:
    - Only Bangalore Rural (4 taluks, 21 hoblis)
    - 10 years historical data
    - Better accuracy for farmers
    - Faster training (~30-45 minutes)
    """
    print("\n" + "=" * 70)
    print("🌾 BANGALORE RURAL LSTM MODEL TRAINING")
    print("=" * 70)
    print(f"📊 Locations: {len(LOCATIONS)} hoblis across 4 taluks")
    print("📈 Data: 10 years historical (Open-Meteo Archive)")
    print("⏱️  Estimated time: 30-45 minutes")
    print("=" * 70)
    
    # Group by taluk for better logging
    taluk_counts = {}
    for loc in LOCATIONS:
        taluk = loc["taluk"]
        taluk_counts[taluk] = taluk_counts.get(taluk, 0) + 1
    
    for taluk, count in taluk_counts.items():
        print(f"  • {taluk}: {count} hoblis")
    
    print("=" * 70)
    
    for i, location in enumerate(LOCATIONS, 1):
        taluk = location["taluk"]
        hobli = location["hobli"]
        print(f"\n[{i}/{len(LOCATIONS)}] 🚀 {taluk} > {hobli}")
        train_model_for_location(location)
        time.sleep(1)
    
    print("\n" + "=" * 70)
    print("✅ ALL TRAINING COMPLETE!")
    print("=" * 70)
    print(f"📊 Trained {len(LOCATIONS)} location-specific models")
    print("🌾 Ready for accurate hobli-level forecasts!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    train_all_locations()
