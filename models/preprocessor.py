"""
Data preprocessing and normalization for LSTM
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path
import joblib

class WeatherPreprocessor:
    """
    Handle data preprocessing for weather time series
    """
    
    def __init__(self, n_features=3):
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        # Default to 3 core features (API provides these)
        self.all_features = ["temp_max", "temp_min", "rainfall", "wind_speed", "humidity"]
        self.n_features = n_features
        self.feature_columns = self.all_features[:n_features]
        self.scaler_path = Path("models/weather_scaler.pkl")
    
    def clean_data(self, df):
        """
        Clean weather data - handle missing values
        """
        print("Cleaning data...")
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['date']).reset_index(drop=True)
        
        # Use only available feature columns
        available_features = [col for col in self.feature_columns if col in df.columns]
        if not available_features:
            available_features = self.feature_columns[:len([col for col in df.columns if col in self.all_features])]
        
        self.feature_columns = available_features
        
        # Handle missing values using forward fill then backward fill
        df[self.feature_columns] = df[self.feature_columns].ffill().bfill()
        
        # Remove rows with NaN (if any)
        df = df.dropna()
        
        print(f"[OK] Data cleaned. Shape: {df.shape}, Features: {self.feature_columns}")
        return df
    
    def normalize_data(self, df, fit=True):
        """
        Normalize data to 0-1 range using MinMaxScaler
        Returns a DataFrame with only feature columns (no date)
        """
        print("Normalizing data...")
        
        data = df[self.feature_columns].values
        
        if fit:
            normalized_data = self.scaler.fit_transform(data)
            # Save scaler for later use in predictions
            Path("models").mkdir(exist_ok=True)
            joblib.dump(self.scaler, self.scaler_path)
            print(f"[OK] Scaler fitted and saved to {self.scaler_path}")
        else:
            # Load existing scaler
            self.scaler = joblib.load(self.scaler_path)
            normalized_data = self.scaler.transform(data)
            print("[OK] Using existing scaler")
        
        # Return as DataFrame with same index and columns (feature columns only, no date)
        result_df = pd.DataFrame(normalized_data, columns=self.feature_columns, index=df.index)
        return result_df
    
    def create_sequences(self, data, seq_length=30):
        """
        Create sequences for LSTM training
        Input: 30 days of data -> Output: predict next 30 days
        
        Args:
            data: Normalized data (n_samples, n_features)
            seq_length: Length of sequence (default 30 days)
        
        Returns:
            X, y arrays for training
        """
        print(f"Creating sequences with length {seq_length}...")
        
        X, y = [], []
        
        # Each sequence is seq_length days + next seq_length days as target
        for i in range(len(data) - (seq_length * 2)):
            X.append(data[i:(i + seq_length)])
            y.append(data[(i + seq_length):(i + seq_length * 2)])
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"[OK] Created {len(X)} sequences")
        print(f"  X shape: {X.shape}  (samples, timesteps, features)")
        print(f"  y shape: {y.shape}  (samples, timesteps, features)")
        
        return X, y
    
    def split_data(self, X, y, train_size=0.8):
        """
        Split data into train/val/test sets
        Train: 80%, Validation: 10%, Test: 10%
        """
        print("Splitting data...")
        
        train_idx = int(len(X) * train_size)
        val_idx = int(len(X) * (train_size + 0.1))
        
        X_train = X[:train_idx]
        y_train = y[:train_idx]
        
        X_val = X[train_idx:val_idx]
        y_val = y[train_idx:val_idx]
        
        X_test = X[val_idx:]
        y_test = y[val_idx:]
        
        print(f"[OK] Train set: {len(X_train)} sequences")
        print(f"[OK] Val set: {len(X_val)} sequences")
        print(f"[OK] Test set: {len(X_test)} sequences")
        
        return (X_train, y_train), (X_val, y_val), (X_test, y_test)
    
    def load_scaler(self, scaler_path=None):
        """
        Load saved scaler for inference
        
        Args:
            scaler_path: Path to the scaler file. If None, uses self.scaler_path
        """
        path = Path(scaler_path) if scaler_path else self.scaler_path
        if path.exists():
            self.scaler = joblib.load(str(path))
            return self.scaler
        else:
            raise FileNotFoundError(f"Scaler not found at {path}")
    
    def denormalize_predictions(self, predictions):
        """
        Convert normalized predictions back to original scale
        """
        return self.scaler.inverse_transform(predictions)
