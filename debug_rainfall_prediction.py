#!/usr/bin/env python3
"""
Debug script to check 30-day rainfall prediction values
Helps diagnose why rain_days shows 0 and dry_days shows 30
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

print("="*80)
print("RAINFALL PREDICTION DEBUG SCRIPT")
print("="*80)

# Check if models and scalers exist
model_dir = Path("models/locations")
if not model_dir.exists():
    print(f"\n[ERROR] Model directory not found: {model_dir}")
    exit(1)

print(f"\n[OK] Found model directory: {model_dir}")

# List all models
models = list(model_dir.glob("lstm_*.h5"))
scalers = list(model_dir.glob("scaler_*.pkl"))

print(f"\nModels found: {len(models)}")
print(f"Scalers found: {len(scalers)}")

# Load sample weather data
print("\n" + "-"*80)
print("Loading historical weather data...")

weather_files = list(Path("data").glob("*_weather.csv"))
if not weather_files:
    print("[ERROR] No weather CSV files found in data/")
    exit(1)

print(f"[OK] Found {len(weather_files)} weather data files")

# Load first file as sample
sample_file = weather_files[0]
print(f"\nLoading sample data from: {sample_file.name}")

try:
    df = pd.read_csv(sample_file)
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {df.columns.tolist()}")
    print(f"\n   Sample rainfall values (first 10):")
    print(f"   {df['rainfall'].head(10).tolist()}")
    print(f"\n   Rainfall statistics:")
    print(f"   Mean: {df['rainfall'].mean():.4f} mm")
    print(f"   Min: {df['rainfall'].min():.4f} mm")
    print(f"   Max: {df['rainfall'].max():.4f} mm")
    print(f"   Std: {df['rainfall'].std():.4f} mm")
    
    # Check distribution
    print(f"\n   Rainfall distribution:")
    print(f"   Days with rainfall > 5mm: {(df['rainfall'] > 5).sum()}")
    print(f"   Days with rainfall <= 5mm: {(df['rainfall'] <= 5).sum()}")
    print(f"   Days with rainfall > 20mm: {(df['rainfall'] > 20).sum()}")
    print(f"   Days with rainfall > 50mm: {(df['rainfall'] > 50).sum()}")
    
except Exception as e:
    print(f"[ERROR] Error loading data: {e}")
    exit(1)

# Now test prediction
print("\n" + "-"*80)
print("Testing prediction with actual model...")

try:
    from modules.multi_location_predictor import MultiLocationPredictor
    
    print("\nInitializing MultiLocationPredictor...")
    predictor = MultiLocationPredictor()
    
    print(f"[OK] Loaded {len(predictor.models)} location models")
    
    # Get first location
    first_location = list(predictor.models.keys())[0]
    print(f"\nTesting with location: {first_location}")
    
    # Load historical data for this location
    location_slug = first_location.replace(' ', '_').lower()
    location_data_files = list(Path("data").glob(f"*{location_slug.split('_')[0]}*weather.csv"))
    
    if location_data_files:
        hist_df = pd.read_csv(location_data_files[0])
        print(f"   Loaded {len(hist_df)} days of historical data")
        
        # Get predictions
        print(f"\n   Generating 30-day forecast...")
        predictions = predictor.models[first_location].predict_next_30_days(hist_df)
        
        print(f"   [OK] Predictions generated")
        print(f"\n   Rainfall predictions (first 10 days):")
        print(f"   {predictions['rainfall'].head(10).tolist()}")
        
        print(f"\n   Rainfall prediction statistics:")
        print(f"   Mean: {predictions['rainfall'].mean():.4f} mm")
        print(f"   Min: {predictions['rainfall'].min():.4f} mm")
        print(f"   Max: {predictions['rainfall'].max():.4f} mm")
        print(f"   Std: {predictions['rainfall'].std():.4f} mm")
        
        # Check distribution with current threshold
        print(f"\n   Distribution with current threshold (5mm):")
        rainy = (predictions['rainfall'] > 5).sum()
        dry = (predictions['rainfall'] <= 5).sum()
        print(f"   Rainy days (>5mm): {rainy}")
        print(f"   Dry days (<=5mm): {dry}")
        print(f"   Total: {rainy + dry}")
        
        # Check if all values are the same (potential bug)
        if predictions['rainfall'].nunique() == 1:
            print(f"\n   [WARNING] All rainfall values are identical!")
            print(f"   Value: {predictions['rainfall'].iloc[0]}")
        
        # Suggest better thresholds
        print(f"\n   Distribution with different thresholds:")
        for threshold in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]:
            count = (predictions['rainfall'] > threshold).sum()
            print(f"   Days with rainfall > {threshold}mm: {count}")
        
except Exception as e:
    print(f"[ERROR] Error during prediction: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*80)
print("DEBUG COMPLETE")
print("="*80)

print("""
POSSIBLE ISSUES:

1. All rainfall predictions are 0 or very small
   → CAUSE: Model predicting very small values
   → FIX: Check model training or denormalization

2. All values are identical
   → CAUSE: Model not training properly
   → FIX: Retrain the model

3. Threshold value (5mm) is too high
   → CAUSE: Actual rainfall predictions are lower
   → FIX: Lower the threshold (e.g., 0.5mm or 1.0mm)

4. Denormalization issue
   → CAUSE: Scaler not properly transforming values
   → FIX: Check scaler fit/transform logic

RECOMMENDATION:
Run with verbose logging to see actual prediction values
""")
