"""
Simplified Training Script - Train Location-Specific LSTM Models
Bangalore Rural - All 21 Hoblis
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TF info logs

print("Importing libraries...")
from models.preprocessor import WeatherPreprocessor
from models.lstm_model import WeatherLSTMModel
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import joblib

print("[OK] Libraries imported")

# 21 Hoblis in Bangalore Rural
LOCATIONS = [
    # Doddaballapura Taluk (5 hoblis)
    {"name": "Kasaba, Doddaballapura", "slug": "kasaba_doddaballapura", "lat": 13.29273, "lon": 77.53891},
    {"name": "Doddabelavangala, Doddaballapura", "slug": "doddabelavangala_doddaballapura", "lat": 13.28855, "lon": 77.42205},
    {"name": "Thubagere, Doddaballapura", "slug": "thubagere_doddaballapura", "lat": 13.373, "lon": 77.570},
    {"name": "Sasalu, Doddaballapura", "slug": "sasalu_doddaballapura", "lat": 13.280, "lon": 77.530},
    {"name": "Madhure, Doddaballapura", "slug": "madhure_doddaballapura", "lat": 13.19510, "lon": 77.45586},
    
    # Devanahalli Taluk (5 hoblis)
    {"name": "Kasaba, Devanahalli", "slug": "kasaba_devanahalli", "lat": 13.18, "lon": 77.85},
    {"name": "Vijayapura, Devanahalli", "slug": "vijayapura_devanahalli", "lat": 13.22, "lon": 77.88},
    {"name": "Kundana, Devanahalli", "slug": "kundana_devanahalli", "lat": 13.15, "lon": 77.92},
    {"name": "Bettakote, Devanahalli", "slug": "bettakote_devanahalli", "lat": 13.25, "lon": 77.80},
    {"name": "Undire, Devanahalli", "slug": "undire_devanahalli", "lat": 13.12, "lon": 77.78},
    
    # Hosakote Taluk (5 hoblis)
    {"name": "Sulibele, Hosakote", "slug": "sulibele_hosakote", "lat": 13.45, "lon": 77.77},
    {"name": "Anugondanahalli, Hosakote", "slug": "anugondanahalli_hosakote", "lat": 13.48, "lon": 77.82},
    {"name": "Jadigenahalli, Hosakote", "slug": "jadigenahalli_hosakote", "lat": 13.50, "lon": 77.75},
    {"name": "Nandagudi, Hosakote", "slug": "nandagudi_hosakote", "lat": 13.42, "lon": 77.70},
    {"name": "Kasaba, Hosakote", "slug": "kasaba_hosakote", "lat": 13.47, "lon": 77.80},
    
    # Nelamangala Taluk (6 hoblis)
    {"name": "Kasaba, Nelamangala", "slug": "kasaba_nelamangala", "lat": 13.27, "lon": 77.45},
    {"name": "Huliyurdurga, Nelamangala", "slug": "huliyurdurga_nelamangala", "lat": 13.30, "lon": 77.40},
    {"name": "Tyamagondlu, Nelamangala", "slug": "tyamagondlu_nelamangala", "lat": 13.25, "lon": 77.50},
    {"name": "Sompura, Nelamangala", "slug": "sompura_nelamangala", "lat": 13.32, "lon": 77.48},
    {"name": "Lakshmipura, Nelamangala", "slug": "lakshmipura_nelamangala", "lat": 13.28, "lon": 77.42},
    {"name": "Makali, Nelamangala", "slug": "makali_nelamangala", "lat": 13.35, "lon": 77.52}
]

def fetch_weather_data(lat, lon, location_name):
    """Fetch 10 years of historical weather data"""
    # Validate coordinates
    if not lat or not lon or lat == 0 or lon == 0:
        raise ValueError(f"Invalid coordinates for {location_name}: lat={lat}, lon={lon}")
    
    from datetime import date
    end_date = date(2025, 11, 30)  # Use a date within API range
    start_date = end_date - timedelta(days=365*10)
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "celsius"
    }
    
    try:
        print(f"  [Fetching] {location_name}...", end="", flush=True)
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        daily_data = data.get("daily", {})
        df = pd.DataFrame({
            "date": pd.to_datetime(daily_data["time"]),
            "temp_max": daily_data["temperature_2m_max"],
            "temp_min": daily_data["temperature_2m_min"],
            "rainfall": daily_data["precipitation_sum"],
        })
        print(f" [OK] {len(df)} records")
        return df
    except Exception as e:
        # Safe error printing for Windows
        error_msg = str(e)[:60].encode('cp1252', errors='ignore').decode('cp1252')
        print(f" [ERROR] {error_msg}")
        return None

def train_location_model(location):
    """Train LSTM model for a single location"""
    slug = location["slug"]
    name = location["name"]
    
    print(f"\n{'='*60}")
    print(f"Training: {name}")
    print(f"{'='*60}")
    
    # Fetch data
    df = fetch_weather_data(location["lat"], location["lon"], name)
    if df is None or len(df) < 365:
        print(f"[FAIL] Insufficient data for {name}")
        return False
    
    try:
        # Preprocess
        print(f"  [Preprocessing]...", end="", flush=True)
        preprocessor = WeatherPreprocessor(n_features=3)
        df_clean = preprocessor.clean_data(df)
        df_norm = preprocessor.normalize_data(df_clean, fit=True)
        X, y = preprocessor.create_sequences(df_norm.values)
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = preprocessor.split_data(X, y)
        print(" [OK]")
        
        # Train model
        print(f"  [Training] Building & Training LSTM...", end="", flush=True)
        model = WeatherLSTMModel(n_features=3)
        model.build_model()
        model.train(X_train, y_train, X_val, y_val, epochs=3, batch_size=32)
        print(" [OK]")
        
        # Evaluate
        eval_results = model.evaluate(X_test, y_test)
        print(f"  [Results] Test Loss: {eval_results['mse']:.4f}, MAE: {eval_results['mae']:.4f}")
        
        # Save
        print(f"  [Saving]...", end="", flush=True)
        model_dir = Path("models/locations")
        model_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = model_dir / f"lstm_{slug}.h5"
        scaler_path = model_dir / f"scaler_{slug}.pkl"
        
        model.model.save(str(model_path))
        joblib.dump(preprocessor.scaler, str(scaler_path))
        print(" [OK]")
        
        # Save data
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        df.to_csv(data_dir / f"{slug}_weather.csv", index=False)
        
        print(f"[OK] {name} trained successfully!")
        return True
        
    except Exception as e:
        # Safe error printing for Windows
        error_msg = str(e).encode('cp1252', errors='ignore').decode('cp1252')
        print(f"\n[FAIL] Error training {name}: {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print(f"\n{'='*60}")
    print(f"Training All {len(LOCATIONS)} Hobli Models")
    print(f"{'='*60}\n")
    
    success_count = 0
    failed_count = 0
    
    for i, location in enumerate(LOCATIONS, 1):
        print(f"\n[{i}/{len(LOCATIONS)}] Training {location['name']}")
        if train_location_model(location):
            success_count += 1
        else:
            failed_count += 1
        
        # Rate limiting
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"Training Complete!")
    print(f"Success: {success_count}/{len(LOCATIONS)}")
    print(f"Failed: {failed_count}/{len(LOCATIONS)}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
