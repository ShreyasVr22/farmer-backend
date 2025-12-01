"""
Test script to verify LSTM input shape fix
Tests that 30 days × 3 features = 90 values reshape correctly to (1, 30, 3)
"""

import numpy as np
import sys
from pathlib import Path

# Test the reshape operation
print("Testing LSTM input shape fix...")
print("="*60)

# Simulate the input data: 30 days of 3 features each
last_30_days = np.random.randn(30, 3)
print(f"✓ Input data shape: {last_30_days.shape}")
print(f"  Total elements: {last_30_days.size} (should be 90)")

# This should work now with n_features=3
try:
    X = last_30_days.reshape(1, 30, 3)
    print(f"✓ Reshaped successfully to: {X.shape}")
    print(f"  Model input shape: (batch_size=1, timesteps=30, features=3)")
except ValueError as e:
    print(f"✗ Reshape failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("Testing with actual LSTM model...")
print("="*60)

try:
    from models.lstm_model import WeatherLSTMModel
    
    # Initialize model with default n_features=3
    model = WeatherLSTMModel()
    print(f"✓ Model initialized with seq_length={model.seq_length}, n_features={model.n_features}")
    
    # Check expected input shape
    expected_input_size = model.seq_length * model.n_features
    actual_input_size = last_30_days.size
    
    print(f"\n  Expected total elements: {expected_input_size}")
    print(f"  Actual input elements: {actual_input_size}")
    
    if expected_input_size == actual_input_size:
        print(f"✓ Input size matches!")
    else:
        print(f"✗ Input size mismatch! Expected {expected_input_size}, got {actual_input_size}")
        sys.exit(1)
    
    # Try the reshape that happens in predict_next_30_days
    X = last_30_days.reshape(1, model.seq_length, model.n_features)
    print(f"✓ Reshape successful: {last_30_days.shape} -> {X.shape}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✓ All tests passed! The LSTM input shape fix is correct.")
print("="*60)
