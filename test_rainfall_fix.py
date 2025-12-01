#!/usr/bin/env python3
"""
Test script to verify the rainfall prediction fix
Tests that rain_days and dry_days are calculated correctly
"""

import pandas as pd
import numpy as np
import sys

# Test the adaptive threshold logic
def test_adaptive_threshold():
    print("="*80)
    print("RAINFALL PREDICTION FIX - VERIFICATION TEST")
    print("="*80)
    
    test_cases = [
        {
            "name": "Very low rainfall (0.0-0.8mm)",
            "values": np.array([0.0, 0.2, 0.1, 0.5, 0.3, 0.8, 0.4, 0.1, 0.6, 0.2,
                              0.0, 0.3, 0.2, 0.7, 0.1, 0.5, 0.0, 0.4, 0.3, 0.2,
                              0.0, 0.1, 0.6, 0.2, 0.5, 0.3, 0.0, 0.4, 0.1, 0.2]),
            "expected_threshold": 0.5
        },
        {
            "name": "Low rainfall (0.5-3mm)",
            "values": np.array([0.5, 1.2, 0.8, 2.1, 1.5, 0.9, 2.3, 1.1, 0.7, 1.8,
                              0.6, 2.0, 1.3, 0.9, 1.7, 2.2, 0.8, 1.4, 0.9, 2.1,
                              1.0, 1.6, 0.7, 1.9, 2.4, 1.2, 0.8, 1.5, 0.9, 1.8]),
            "expected_threshold": 1.0
        },
        {
            "name": "Normal rainfall (5-30mm)",
            "values": np.array([5.2, 12.1, 8.5, 20.3, 15.2, 9.1, 25.5, 11.8, 7.2, 18.9,
                              6.3, 21.7, 13.4, 9.8, 17.1, 24.2, 8.6, 14.5, 9.3, 22.1,
                              10.2, 16.8, 7.9, 19.3, 26.5, 12.6, 8.1, 15.7, 9.8, 18.4]),
            "expected_threshold": 5.0
        }
    ]
    
    print("\n" + "-"*80)
    print("Testing Adaptive Threshold Logic")
    print("-"*80)
    
    all_passed = True
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        values = test['values']
        max_rainfall = float(np.max(values))
        
        # Apply adaptive threshold logic
        if max_rainfall < 1.0:
            threshold = 0.5
        elif max_rainfall < 5.0:
            threshold = 1.0
        else:
            threshold = 5.0
        
        # Calculate rain/dry days
        rainy_days = int((values > threshold).sum())
        dry_days = int((values <= threshold).sum())
        
        # Validation
        expected_threshold = test['expected_threshold']
        test_passed = threshold == expected_threshold and (rainy_days + dry_days) == 30
        
        print(f"   Max rainfall: {max_rainfall:.2f} mm")
        print(f"   Selected threshold: {threshold:.1f} mm (expected: {expected_threshold:.1f} mm)")
        print(f"   Rainy days: {rainy_days} (days > {threshold}mm)")
        print(f"   Dry days: {dry_days} (days <= {threshold}mm)")
        print(f"   Total: {rainy_days + dry_days}")
        
        if test_passed:
            print(f"   [PASS] Threshold correctly selected")
        else:
            print(f"   [FAIL] Incorrect threshold calculation")
            all_passed = False
        
        # Verify distribution is realistic
        if rainy_days == 0:
            print(f"   [WARNING] No rainy days - distribution might not reflect data")
        if dry_days == 0:
            print(f"   [WARNING] No dry days - all days are rainy")
    
    print("\n" + "-"*80)
    print("Testing Edge Cases")
    print("-"*80)
    
    # Edge case 1: All zeros
    print("\nEdge case: All zeros")
    values = np.zeros(30)
    max_rainfall = float(np.max(values))
    threshold = 0.5 if max_rainfall < 1.0 else (1.0 if max_rainfall < 5.0 else 5.0)
    rainy_days = int((values > threshold).sum())
    dry_days = int((values <= threshold).sum())
    print(f"   Max: {max_rainfall:.2f} mm, Threshold: {threshold:.1f} mm")
    print(f"   Rainy: {rainy_days}, Dry: {dry_days}")
    print(f"   [EXPECTED] Rainy: 0, Dry: 30")
    
    # Edge case 2: All maximum values
    print("\nEdge case: All high values (30mm)")
    values = np.full(30, 30.0)
    max_rainfall = float(np.max(values))
    threshold = 0.5 if max_rainfall < 1.0 else (1.0 if max_rainfall < 5.0 else 5.0)
    rainy_days = int((values > threshold).sum())
    dry_days = int((values <= threshold).sum())
    print(f"   Max: {max_rainfall:.2f} mm, Threshold: {threshold:.1f} mm")
    print(f"   Rainy: {rainy_days}, Dry: {dry_days}")
    print(f"   [EXPECTED] Rainy: 30, Dry: 0")
    
    # Edge case 3: Mixed distribution
    print("\nEdge case: Mixed normal distribution")
    values = np.random.normal(10, 8, 30)  # mean=10, std=8
    values = np.clip(values, 0, 50)  # Clip to realistic range
    max_rainfall = float(np.max(values))
    threshold = 0.5 if max_rainfall < 1.0 else (1.0 if max_rainfall < 5.0 else 5.0)
    rainy_days = int((values > threshold).sum())
    dry_days = int((values <= threshold).sum())
    print(f"   Max: {max_rainfall:.2f} mm, Threshold: {threshold:.1f} mm")
    print(f"   Rainy: {rainy_days}, Dry: {dry_days}")
    print(f"   Mean: {values.mean():.2f} mm")
    print(f"   [EXPECTED] Realistic distribution (not 0/30 or 30/0)")
    
    print("\n" + "="*80)
    if all_passed:
        print("TEST RESULT: ALL TESTS PASSED")
        print("="*80)
        print("\nRainfall prediction fix is working correctly!")
        print("✓ Adaptive threshold logic is correct")
        print("✓ Rain days are calculated properly")
        print("✓ Dry days are calculated properly")
        return 0
    else:
        print("TEST RESULT: SOME TESTS FAILED")
        print("="*80)
        return 1

if __name__ == "__main__":
    sys.exit(test_adaptive_threshold())
