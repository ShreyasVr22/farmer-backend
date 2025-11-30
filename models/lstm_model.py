
"""
LSTM model definition, training, and saving
"""

import numpy as np
import tensorflow as tf
# TensorFlow 2.14 has keras as tensorflow.keras
from tensorflow import keras
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Reshape
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from pathlib import Path
import joblib
from datetime import datetime

class WeatherLSTMModel:
    """
    LSTM model for weather forecasting
    Predicts: temp_max, temp_min, rainfall, wind_speed, humidity
    """
    
    def __init__(self, seq_length=30, n_features=5):
        self.seq_length = seq_length
        self.n_features = n_features
        self.model = None
        self.history = None
        self.model_path = Path("models/lstm_weather_model.h5")
        self.weights_path = Path("models/lstm_weather_weights.weights.h5")
    
    def build_model(self):
        """
        Build LSTM architecture for time series forecasting
        """
        print("Building LSTM model...")
        
        self.model = Sequential([
            # First LSTM layer
            keras.layers.LSTM(
                units=64,
                activation='relu',
                return_sequences=True,
                input_shape=(self.seq_length, self.n_features)
            ),
            keras.layers.Dropout(0.2),
            
            # Second LSTM layer
            keras.layers.LSTM(
                units=64,
                activation='relu',
                return_sequences=True
            ),
            keras.layers.Dropout(0.2),
            
            # Third LSTM layer
            keras.layers.LSTM(
                units=32,
                activation='relu',
                return_sequences=False
            ),
            keras.layers.Dropout(0.2),
            
            # Dense layers for output
            Dense(units=self.seq_length * self.n_features),
            Reshape((self.seq_length, self.n_features))
        ])
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        print("[OK] Model built successfully")
        try:
            self.model.summary()
        except:
            pass  # Suppress summary if encoding issues
        
        return self.model
    
    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
        """
        Train LSTM model
        """
        print(f"\nTraining model for {epochs} epochs...")
        
        # Create models directory if it doesn't exist
        Path("models").mkdir(exist_ok=True)
        
        # Callbacks
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        )
        
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=0.00001,
            verbose=1
        )
        
        # Train
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
        
        print("[OK] Training completed")
        return self.history
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model on test set
        """
        print("\nEvaluating model...")
        
        loss, mae = self.model.evaluate(X_test, y_test, verbose=0)
        
        print(f"[OK] Test Loss (MSE): {loss:.6f}")
        print(f"[OK] Test MAE: {mae:.6f}")
        
        return {"mse": loss, "mae": mae}
    
    def save_model(self):
        """
        Save trained model
        """
        Path("models").mkdir(exist_ok=True)
        
        # Save in Keras format
        self.model.save(self.model_path)
        print(f"✓ Model saved to {self.model_path}")
        
        # Also save training history
        history_path = Path("models/training_history.pkl")
        joblib.dump(self.history.history, history_path)
        print(f"✓ Training history saved to {history_path}")
    
    def load_model(self, model_path=None):
        """
        Load saved model with compatibility fixes for InputLayer deserialization
        Handles batch_shape -> input_shape conversion for TensorFlow version compatibility
        """
        path = Path(model_path) if model_path else self.model_path
        if path.exists():
            try:
                # Try standard loading first
                self.model = load_model(str(path))
                print(f"[OK] Model loaded from {path}")
                return self.model
            except Exception as e:
                # If standard load fails, try with custom_objects to handle InputLayer issues
                print(f"  [Note] Standard load encountered issue, attempting with custom_objects...")
                try:
                    custom_objs = {'InputLayer': tf.keras.layers.InputLayer}
                    self.model = load_model(str(path), custom_objects=custom_objs)
                    print(f"[OK] Model loaded with custom objects from {path}")
                    return self.model
                except Exception as e2:
                    error_msg = str(e2)[:100].encode('cp1252', errors='ignore').decode('cp1252')
                    print(f"[ERROR] Failed to load model: {error_msg}")
                    raise FileNotFoundError(f"Could not load model at {path}. Error: {str(e2)}")
        else:
            raise FileNotFoundError(f"Model not found at {path}")
    
    def predict(self, X):
        """
        Make predictions
        """
        if self.model is None:
            self.load_model()
        
        predictions = self.model.predict(X, verbose=0)
        return predictions
    
    def predict_next_30_days(self, last_30_days_normalized):
        """
        Predict next 30 days given last 30 days of data
        
        Args:
            last_30_days_normalized: Shape (30, 5) - normalized data
        
        Returns:
            predictions: Shape (30, 5) - predicted values (still normalized)
        """
        # Reshape for model input: (1, 30, 5)
        X = last_30_days_normalized.reshape(1, self.seq_length, self.n_features)
        
        # Predict
        predictions = self.predict(X)
        
        # Return squeezed predictions (30, 5)
        return predictions.squeeze()