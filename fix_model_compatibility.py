"""
Fix TensorFlow model compatibility issue with batch_shape in InputLayer
The models were saved with an older TensorFlow version and use 'batch_shape' parameter
which is not recognized in newer TensorFlow versions. We need to convert them.
"""

import os
import json
import tensorflow as tf
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_DIR = Path("trained_models")

def fix_model_config_file(config_path):
    """Fix the config.json file to use 'input_shape' instead of 'batch_shape'"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Recursively search for batch_shape and replace with proper input_shape
        def fix_config(obj):
            if isinstance(obj, dict):
                # If this is an InputLayer config with batch_shape
                if obj.get('class_name') == 'InputLayer' and 'batch_shape' in obj.get('config', {}):
                    batch_shape = obj['config']['batch_shape']
                    # Convert batch_shape to input_shape (remove batch dimension)
                    if isinstance(batch_shape, list) and len(batch_shape) > 1:
                        obj['config']['input_shape'] = batch_shape[1:]
                    del obj['config']['batch_shape']
                    logger.info(f"  Fixed InputLayer in config: batch_shape {batch_shape} → input_shape {obj['config'].get('input_shape')}")
                
                # Recursively fix nested dicts
                for key, value in obj.items():
                    fix_config(value)
            elif isinstance(obj, list):
                for item in obj:
                    fix_config(item)
        
        fix_config(config)
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        logger.info(f"✓ Fixed config file: {config_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Error fixing config {config_path}: {e}")
        return False

def load_and_resave_model(model_h5_path):
    """Load model with custom object scope and resave to fix compatibility"""
    try:
        model_name = Path(model_h5_path).stem
        logger.info(f"\nProcessing model: {model_name}")
        
        # Try to load the model
        try:
            # First try direct load
            model = tf.keras.models.load_model(model_h5_path, compile=False)
            logger.info(f"  ✓ Direct load successful")
        except Exception as e:
            logger.warning(f"  Direct load failed: {e}")
            logger.info(f"  Attempting safe load (skipping layer creation)...")
            
            # Try loading with custom_objects to handle any custom layers
            model = tf.keras.models.load_model(
                model_h5_path,
                compile=False,
                custom_objects={'LSTM': tf.keras.layers.LSTM}
            )
            logger.info(f"  ✓ Safe load successful")
        
        # Recompile the model
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        # Resave the model (this will use the new TF format)
        model.save(model_h5_path, overwrite=True)
        logger.info(f"  ✓ Model resaved successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ Error processing {model_h5_path}: {e}")
        return False

def main():
    """Fix all models in trained_models directory"""
    if not MODEL_DIR.exists():
        logger.error(f"Model directory not found: {MODEL_DIR}")
        return
    
    # Find all .h5 model files
    model_files = sorted(MODEL_DIR.glob("**/model_*.h5"))
    config_files = sorted(MODEL_DIR.glob("**/config_*.json"))
    
    logger.info(f"Found {len(model_files)} model files and {len(config_files)} config files")
    
    # First, try to fix config files if they exist
    if config_files:
        logger.info("\n=== FIXING CONFIG FILES ===")
        for config_path in config_files:
            fix_model_config_file(config_path)
    
    # Then, try to load and resave models
    if model_files:
        logger.info("\n=== LOADING AND RESAVING MODELS ===")
        success_count = 0
        for model_path in model_files:
            if load_and_resave_model(model_path):
                success_count += 1
        
        logger.info(f"\n✓ Successfully processed {success_count}/{len(model_files)} models")
        return success_count > 0
    
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
