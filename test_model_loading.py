#!/usr/bin/env python
"""
Test script to verify model loading and basic training works
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from pathlib import Path
import sys

print("\n" + "="*60)
print("MODEL LOADING & TRAINING TEST")
print("="*60 + "\n")

# Test 1: Check TensorFlow version
print("[TEST 1] Checking TensorFlow version...", end=" ", flush=True)
try:
    import tensorflow as tf
    print(f"[OK] {tf.__version__}")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Test 2: Check required imports
print("[TEST 2] Checking required imports...", end=" ", flush=True)
try:
    from models.preprocessor import WeatherPreprocessor
    from models.lstm_model import WeatherLSTMModel
    import requests
    import pandas as pd
    from datetime import datetime, timedelta
    import joblib
    print("[OK]")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Test 3: Test WeatherPreprocessor
print("[TEST 3] Testing WeatherPreprocessor...", end=" ", flush=True)
try:
    preprocessor = WeatherPreprocessor()
    print("[OK]")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Test 4: Test WeatherLSTMModel initialization
print("[TEST 4] Testing WeatherLSTMModel initialization...", end=" ", flush=True)
try:
    model = WeatherLSTMModel(n_features=3)
    print("[OK]")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Test 5: Test building model
print("[TEST 5] Building LSTM model...", end=" ", flush=True)
try:
    model.build_model()
    print("[OK]")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Test 6: Fetch test data
print("[TEST 6] Fetching test weather data...", end=" ", flush=True)
try:
    from datetime import date
    end_date = date(2025, 11, 30)  # Use a date within API range
    start_date = end_date - timedelta(days=365*10)
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 13.29273,
        "longitude": 77.53891,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "celsius"
    }
    
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
    print(f"[OK] {len(df)} records")
except Exception as e:
    error_msg = str(e)[:60].encode('cp1252', errors='ignore').decode('cp1252')
    print(f"[ERROR] {error_msg}")
    sys.exit(1)

# Test 7: Test preprocessing
print("[TEST 7] Testing data preprocessing...", end=" ", flush=True)
try:
    preprocessor = WeatherPreprocessor(n_features=3)
    df_clean = preprocessor.clean_data(df)
    df_norm = preprocessor.normalize_data(df_clean, fit=True)
    X, y = preprocessor.create_sequences(df_norm.values)
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = preprocessor.split_data(X, y)
    print(f"[OK] X_train shape: {X_train.shape}")
except Exception as e:
    error_msg = str(e).encode('cp1252', errors='ignore').decode('cp1252')
    print(f"[ERROR] {error_msg}")
    sys.exit(1)

# Test 8: Test model training (1 epoch)
print("[TEST 8] Training model (1 epoch)...", end=" ", flush=True)
try:
    model = WeatherLSTMModel(n_features=3)
    model.build_model()
    model.train(X_train, y_train, X_val, y_val, epochs=1, batch_size=32)
    print("[OK]")
except Exception as e:
    error_msg = str(e).encode('cp1252', errors='ignore').decode('cp1252')
    print(f"[ERROR] {error_msg}")
    sys.exit(1)

# Test 9: Test model saving
print("[TEST 9] Testing model save/load...", end=" ", flush=True)
try:
    Path("models").mkdir(exist_ok=True)
    test_model_path = Path("models/test_lstm_temp.h5")
    model.model.save(str(test_model_path))
    
    # Test loading with custom objects
    loaded_model = WeatherLSTMModel()
    loaded_model.load_model(str(test_model_path))
    
    # Cleanup
    if test_model_path.exists():
        test_model_path.unlink()
    backup_path = test_model_path.parent / f"{test_model_path.name}.backup"
    if backup_path.exists():
        backup_path.unlink()
    
    print("[OK]")
except Exception as e:
    error_msg = str(e).encode('cp1252', errors='ignore').decode('cp1252')
    print(f"[ERROR] {error_msg}")
    sys.exit(1)

print("\n" + "="*60)
print("ALL TESTS PASSED - READY TO TRAIN!")
print("="*60)
print("\nRun: python train_all_locations_simple.py\n")
