"""
Script to initialize and train LSTM model - SIMPLIFIED VERSION
Run this once to set up the model
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.preprocessor import WeatherPreprocessor
from models.lstm_model import WeatherLSTMModel
import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_weather_simple():
    """
    Fetch weather data using a simpler approach
    """
    print("Fetching weather data from Open-Meteo API...")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365*3)
    
    # Use simpler daily parameter format
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": "13.2256",
        "longitude": "77.5750",
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m,relative_humidity_2m",
        "temperature_unit": "celsius",
        "timezone": "Asia/Kolkata"
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return None
        
        data = response.json()
        
        if "daily" not in data:
            print(f"No daily data in response: {data}")
            return None
        
        daily = data["daily"]
        
        df = pd.DataFrame({
            "date": pd.to_datetime(daily["time"]),
            "temp_max": daily["temperature_2m_max"],
            "temp_min": daily["temperature_2m_min"],
            "rainfall": daily["precipitation_sum"],
            "wind_speed": daily["windspeed_10m"],
            "humidity": daily["relative_humidity_2m"]
        })
        
        print(f"✓ Successfully fetched {len(df)} records")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def main():
    print("="*70)
    print("FARMER ASSISTANT - WEATHER PREDICTION LSTM TRAINING")
    print("="*70)
    print()
    
    try:
        # Step 1: Fetch historical data
        print("STEP 1: Fetching Historical Weather Data")
        print("-" * 70)
        
        historical_df = fetch_weather_simple()
        
        if historical_df is None or len(historical_df) == 0:
            print("✗ Failed to fetch weather data")
            print("\nTroubleshooting:")
            print("1. Check your internet connection")
            print("2. Check if Open-Meteo API is accessible")
            print("3. Try manually: curl 'https://archive-api.open-meteo.com/v1/archive?latitude=13.2256&longitude=77.5750&start_date=2022-11-28&end_date=2025-11-27&daily=temperature_2m_max'")
            return
        
        print()
        
        # Step 2: Preprocess data
        print("STEP 2: Preprocessing Data")
        print("-" * 70)
        
        preprocessor = WeatherPreprocessor()
        df_clean = preprocessor.clean_data(historical_df)
        data_normalized = preprocessor.normalize_data(df_clean, fit=True)
        X, y = preprocessor.create_sequences(data_normalized, seq_length=30)
        (X_train, y_train), (X_val, y_val), (X_test, y_test) = preprocessor.split_data(X, y)
        print()
        
        # Step 3: Build model
        print("STEP 3: Building LSTM Model")
        print("-" * 70)
        
        model = WeatherLSTMModel(seq_length=30, n_features=5)
        model.build_model()
        print()
        
        # Step 4: Train model
        print("STEP 4: Training Model")
        print("-" * 70)
        print("This may take 10-15 minutes depending on your hardware...")
        print()
        
        history = model.train(X_train, y_train, X_val, y_val, epochs=50, batch_size=32)
        print()
        
        # Step 5: Evaluate model
        print("STEP 5: Evaluating Model")
        print("-" * 70)
        
        metrics = model.evaluate(X_test, y_test)
        print()
        
        # Step 6: Save model
        print("STEP 6: Saving Model")
        print("-" * 70)
        
        model.save_model()
        print()
        
        # Summary
        print("="*70)
        print("TRAINING COMPLETE!")
        print("="*70)
        print(f"\nModel saved successfully!")
        print(f"✓ Model: models/lstm_weather_model.h5")
        print(f"✓ Scaler: models/weather_scaler.pkl")
        print(f"✓ History: models/training_history.pkl")
        print(f"✓ Data: data/bangalore_rural_weather.csv")
        print(f"\nYou can now run the FastAPI server:")
        print(f"  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print()
        
    except Exception as e:
        print(f"\n✗ Error during training: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
