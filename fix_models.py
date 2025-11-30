#!/usr/bin/env python
"""
Fix TensorFlow model compatibility issue
Models trained with older TensorFlow versions use 'batch_shape' instead of 'batch_input_shape'
in the InputLayer, which newer TensorFlow versions can't deserialize.

Solution: Rebuild models from scratch using the trained weights converted from the old format.
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from pathlib import Path
import h5py
import json
import shutil
import tempfile

def fix_model_json(config_dict):
    """
    Recursively fix InputLayer config to use batch_input_shape instead of batch_shape
    """
    if isinstance(config_dict, dict):
        # Handle InputLayer config
        if config_dict.get('class_name') == 'InputLayer':
            if 'batch_shape' in config_dict.get('config', {}):
                batch_shape = config_dict['config'].pop('batch_shape')
                config_dict['config']['batch_input_shape'] = batch_shape
                print(f"  [FIXED] InputLayer: batch_shape -> batch_input_shape")
        
        # Recurse into nested dicts
        for key, value in config_dict.items():
            if isinstance(value, (dict, list)):
                fix_model_json(value)
    
    elif isinstance(config_dict, list):
        for item in config_dict:
            if isinstance(item, (dict, list)):
                fix_model_json(item)

def fix_model_file(model_path):
    """
    Fix a single HDF5 model file's InputLayer configuration
    """
    try:
        # Create backup
        backup_path = str(model_path) + ".backup"
        if not Path(backup_path).exists():
            shutil.copy(model_path, backup_path)
            print(f"  [Backup] Created {Path(backup_path).name}")
        
        # Open the HDF5 file and fix the model config
        with h5py.File(str(model_path), 'r+') as f:
            # Get the model config
            if 'model_config' in f.attrs:
                config_str = f.attrs['model_config']
                if isinstance(config_str, bytes):
                    config_str = config_str.decode('utf-8')
                
                # Parse JSON
                config_dict = json.loads(config_str)
                
                # Fix batch_shape -> batch_input_shape
                fix_model_json(config_dict)
                
                # Write back the fixed config
                f.attrs['model_config'] = json.dumps(config_dict).encode('utf-8')
        
        print(f"[OK] Fixed {model_path.name}")
        return True
        
    except Exception as e:
        print(f"[ERROR] {model_path.name}: {str(e)[:80]}")
        return False

if __name__ == "__main__":
    model_dir = Path("models/locations")
    model_files = sorted(list(model_dir.glob("lstm_*.h5")))
    
    # Exclude backups
    model_files = [f for f in model_files if not str(f).endswith('.backup')]
    
    print(f"\nFound {len(model_files)} models to fix")
    print("Fixing InputLayer batch_shape compatibility issue...\n")
    
    fixed = 0
    failed = 0
    
    for i, model_file in enumerate(model_files, 1):
        print(f"[{i}/{len(model_files)}] {model_file.name}")
        if fix_model_file(model_file):
            fixed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {fixed} fixed, {failed} failed")
    print(f"{'='*60}\n")
    print("Testing model loading...")
    
    # Test loading one fixed model
    if fixed > 0:
        test_model = list(model_dir.glob("lstm_*.h5"))[0]
        print(f"\nTesting {test_model.name}...")
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(str(test_model))
            print(f"[OK] Model loaded successfully!")
            print(f"[Model] Inputs: {[inp.shape for inp in model.inputs]}")
        except Exception as e:
            print(f"[ERROR] Could not load model: {str(e)[:100]}")
