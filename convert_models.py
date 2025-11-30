"""
Convert old TensorFlow models to be compatible with TensorFlow 2.14+
Fixes batch_shape -> input_shape issue in InputLayer
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF warnings

from pathlib import Path
import tensorflow as tf
from tensorflow import keras
import json
import shutil

def convert_model(model_path):
    """Try to load and resave model with updated format"""
    try:
        # Create backup
        backup_path = str(model_path) + ".backup"
        if not Path(backup_path).exists():
            shutil.copy(model_path, backup_path)
            print(f"  [Backup] Created {Path(backup_path).name}")
        
        # Try loading with custom_objects for InputLayer compatibility
        try:
            custom_objs = {'InputLayer': tf.keras.layers.InputLayer}
            model = keras.models.load_model(str(model_path), custom_objects=custom_objs)
            print(f"[OK] Loaded {model_path.name}, resaving...")
            model.save(str(model_path))
            print(f"[FIXED] {model_path.name} updated successfully")
            return True
        except Exception as e:
            # If that fails, try standard load
            print(f"[WARN] Custom objects load failed for {model_path.name}, trying standard load...")
            try:
                model = keras.models.load_model(str(model_path))
                print(f"[OK] Loaded {model_path.name}, resaving...")
                model.save(str(model_path))
                print(f"[FIXED] {model_path.name} updated successfully")
                return True
            except Exception as e2:
                print(f"[ERROR] {model_path.name}: {str(e2)[:80]}")
                return False
            
    except Exception as e:
        print(f"[ERROR] {model_path.name}: {e}")
        return False

if __name__ == "__main__":
    model_dir = Path("models/locations")
    model_files = list(model_dir.glob("lstm_*.h5"))
    
    print(f"\nFound {len(model_files)} models to fix")
    print("Attempting to load and resave models for compatibility...\n")
    
    fixed = 0
    failed = 0
    
    for model_file in sorted(model_files):
        if convert_model(model_file):
            fixed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {fixed} fixed, {failed} need retraining")
    print(f"{'='*60}\n")

