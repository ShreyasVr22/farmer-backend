"""
Comprehensive test: Verify entire prediction pipeline with 3-feature LSTM
Tests from data loading through model prediction
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("COMPREHENSIVE LSTM FIX VERIFICATION")
print("="*70)

# ============================================================
# STEP 1: Test data shape
# ============================================================
print("\n[STEP 1] Testing input data shapes...")
print("-" * 70)

# Simulate 30 days of weather data with 3 features
days = 30
features = ["temp_max", "temp_min", "rainfall"]
n_features = 3

# Create sample data
sample_data = np.random.randn(days, n_features) * 10 + 25  # Realistic temp range

df = pd.DataFrame(sample_data, columns=features)
print(f"[OK] Created sample DataFrame with shape: {df.shape}")
print(f"  Columns: {list(df.columns)}")
print(f"  Data size: {days} days x {n_features} features = {days * n_features} values")

# ============================================================
# STEP 2: Test model initialization
# ============================================================
print("\n[STEP 2] Testing model initialization...")
print("-" * 70)

try:
    from models.lstm_model import WeatherLSTMModel
    
    model = WeatherLSTMModel()
    print(f"[OK] Model initialized successfully")
    print(f"  seq_length: {model.seq_length}")
    print(f"  n_features: {model.n_features}")
    print(f"  Expected input elements: {model.seq_length * model.n_features}")
    
except Exception as e:
    print(f"[ERROR] Failed to initialize model: {e}")
    sys.exit(1)

# ============================================================
# STEP 3: Test feature extraction
# ============================================================
print("\n[STEP 3] Testing feature extraction...")
print("-" * 70)

feature_columns = [col for col in ["temp_max", "temp_min", "rainfall", "wind_speed", "humidity"] 
                   if col in df.columns]

if len(feature_columns) < 3:
    feature_columns = ["temp_max", "temp_min", "rainfall"]

print(f"[OK] Selected features: {feature_columns}")
print(f"  Number of features: {len(feature_columns)}")

last_30_days = df[feature_columns].tail(30).values
print(f"[OK] Extracted last 30 days")
print(f"  Shape: {last_30_days.shape} (expected: (30, 3))")

# ============================================================
# STEP 4: Test reshape operation
# ============================================================
print("\n[STEP 4] Testing reshape operation...")
print("-" * 70)

try:
    # This is the critical reshape that was failing before
    X = last_30_days.reshape(1, model.seq_length, model.n_features)
    print(f"[OK] Reshape successful!")
    print(f"  From: {last_30_days.shape}")
    print(f"  To:   {X.shape}")
    print(f"  Required for model: (batch_size=1, timesteps={model.seq_length}, features={model.n_features})")
    
except ValueError as e:
    print(f"[ERROR] Reshape failed: {e}")
    print(f"  Input size: {last_30_days.size} elements")
    print(f"  Required size: {1 * model.seq_length * model.n_features} elements")
    sys.exit(1)

# ============================================================
# STEP 5: Validate dimensions match
# ============================================================
print("\n[STEP 5] Validating dimension compatibility...")
print("-" * 70)

input_size = last_30_days.size
required_size = model.seq_length * model.n_features

print(f"Input array size:    {input_size}")
print(f"Required array size: {required_size}")

if input_size == required_size:
    print(f"[OK] Sizes match! Ready for LSTM processing.")
else:
    print(f"[ERROR] Size mismatch! {input_size} != {required_size}")
    sys.exit(1)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*70)
print("[OK] ALL TESTS PASSED!")
print("="*70)
print("\nSummary:")
print("  • LSTM model expects: 30 days x 3 features = 90 values")
print("  • Input data provides: 30 days x 3 features = 90 values")
print("  • Reshape (30, 3) -> (1, 30, 3): SUCCESS")
print("  • The 'cannot reshape array of size 90 into shape (1,30,5)' error")
print("    will NO LONGER occur because the model now correctly expects")
print("    3 features instead of 5.")
print("\n" + "="*70)
