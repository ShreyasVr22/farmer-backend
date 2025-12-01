"""
Multi-Location Weather Predictor
Manages per-location LSTM models for weather forecasting
"""

import logging
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from models.lstm_model import WeatherLSTMModel
from models.preprocessor import WeatherPreprocessor

logger = logging.getLogger(__name__)

# Bangalore Rural Hobli-Level Locations (21 hoblis across 4 taluks)
LOCATIONS = [
    # Doddaballapura Taluk (5 hoblis)
    {
        "name": "Kasaba, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Kasaba",
        "lat": 13.29273,
        "lon": 77.53891
    },
    {
        "name": "Doddabelavangala, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Doddabelavangala",
        "lat": 13.28855,
        "lon": 77.42205
    },
    {
        "name": "Thubagere, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Thubagere",
        "lat": 13.373,
        "lon": 77.570
    },
    {
        "name": "Sasalu, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Sasalu",
        "lat": 13.280,
        "lon": 77.530
    },
    {
        "name": "Madhure, Doddaballapura",
        "taluk": "Doddaballapura",
        "hobli": "Madhure",
        "lat": 13.19510,
        "lon": 77.45586
    },
    
    # Devanahalli Taluk (5 hoblis)
    {"name": "Kasaba, Devanahalli", "taluk": "Devanahalli", "hobli": "Kasaba", "lat": 13.18, "lon": 77.85},
    {"name": "Vijayapura, Devanahalli", "taluk": "Devanahalli", "hobli": "Vijayapura", "lat": 13.22, "lon": 77.88},
    {"name": "Kundana, Devanahalli", "taluk": "Devanahalli", "hobli": "Kundana", "lat": 13.15, "lon": 77.92},
    {"name": "Bettakote, Devanahalli", "taluk": "Devanahalli", "hobli": "Bettakote", "lat": 13.25, "lon": 77.80},
    {"name": "Undire, Devanahalli", "taluk": "Devanahalli", "hobli": "Undire", "lat": 13.12, "lon": 77.78},
    
    # Hosakote Taluk (5 hoblis)
    {"name": "Sulibele, Hosakote", "taluk": "Hosakote", "hobli": "Sulibele", "lat": 13.45, "lon": 77.77},
    {"name": "Anugondanahalli, Hosakote", "taluk": "Hosakote", "hobli": "Anugondanahalli", "lat": 13.48, "lon": 77.82},
    {"name": "Jadigenahalli, Hosakote", "taluk": "Hosakote", "hobli": "Jadigenahalli", "lat": 13.50, "lon": 77.75},
    {"name": "Nandagudi, Hosakote", "taluk": "Hosakote", "hobli": "Nandagudi", "lat": 13.42, "lon": 77.70},
    {"name": "Kasaba, Hosakote", "taluk": "Hosakote", "hobli": "Kasaba", "lat": 13.47, "lon": 77.80},
    
    # Nelamangala Taluk (6 hoblis)
    {"name": "Kasaba, Nelamangala", "taluk": "Nelamangala", "hobli": "Kasaba", "lat": 13.27, "lon": 77.45},
    {"name": "Huliyurdurga, Nelamangala", "taluk": "Nelamangala", "hobli": "Huliyurdurga", "lat": 13.30, "lon": 77.40},
    {"name": "Tyamagondlu, Nelamangala", "taluk": "Nelamangala", "hobli": "Tyamagondlu", "lat": 13.25, "lon": 77.50},
    {"name": "Sompura, Nelamangala", "taluk": "Nelamangala", "hobli": "Sompura", "lat": 13.32, "lon": 77.48},
    {"name": "Lakshmipura, Nelamangala", "taluk": "Nelamangala", "hobli": "Lakshmipura", "lat": 13.28, "lon": 77.42},
    {"name": "Makali, Nelamangala", "taluk": "Nelamangala", "hobli": "Makali", "lat": 13.35, "lon": 77.52}
]

# Location slug mapping for model loading
# Maps display names to model file slugs
LOCATION_SLUG_MAPPING = {
    # Doddaballapura Taluk
    "kasaba, doddaballapura": "kasaba_doddaballapura",
    "doddabelavangala, doddaballapura": "doddabelavangala_doddaballapura",
    "thubagere, doddaballapura": "thubagere_doddaballapura",
    "sasalu, doddaballapura": "sasalu_doddaballapura",
    "madhure, doddaballapura": "madhure_doddaballapura",
    
    # Devanahalli Taluk
    "kasaba, devanahalli": "kasaba_devanahalli",
    "vijayapura, devanahalli": "vijayapura_devanahalli",
    "kundana, devanahalli": "kundana_devanahalli",
    "bettakote, devanahalli": "bettakote_devanahalli",
    "undire, devanahalli": "undire_devanahalli",
    
    # Hosakote Taluk
    "sulibele, hosakote": "sulibele_hosakote",
    "anugondanahalli, hosakote": "anugondanahalli_hosakote",
    "jadigenahalli, hosakote": "jadigenahalli_hosakote",
    "nandagudi, hosakote": "nandagudi_hosakote",
    "kasaba, hosakote": "kasaba_hosakote",
    
    # Nelamangala Taluk
    "kasaba, nelamangala": "kasaba_nelamangala",
    "huliyurdurga, nelamangala": "huliyurdurga_nelamangala",
    "tyamagondlu, nelamangala": "tyamagondlu_nelamangala",
    "sompura, nelamangala": "sompura_nelamangala",
    "lakshmipura, nelamangala": "lakshmipura_nelamangala",
    "makali, nelamangala": "makali_nelamangala",
}

class LocationModel:
    """Wrapper for location-specific model and scaler"""
    
    def __init__(self, location_slug: str, model_path: Path, scaler_path: Path):
        self.location_slug = location_slug
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = None
        self.preprocessor = None
        self.is_loaded = False
        
    def load(self):
        """Load model and scaler from disk"""
        try:
            if not self.model_path.exists():
                logger.warning(f"Model not found for {self.location_slug}: {self.model_path}")
                return False
            
            # Load with safe deserialization to handle version compatibility
            import tensorflow as tf
            self.model = WeatherLSTMModel()
            
            # Strategy 1: Try standard load
            try:
                self.model.load_model(str(self.model_path))
                logger.info(f"  ✓ Standard load successful for {self.location_slug}")
            except Exception as load_error:
                logger.debug(f"  Standard load error: {load_error}")
                # Strategy 2: Try safe load without compilation
                try:
                    logger.info(f"  Attempting safe load (no compile) for {self.location_slug}...")
                    self.model.model = tf.keras.models.load_model(
                        str(self.model_path),
                        compile=False
                    )
                    self.model.model.compile(
                        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                        loss='mse',
                        metrics=['mae']
                    )
                    logger.info(f"  ✓ Safe load successful for {self.location_slug}")
                except Exception as safe_error:
                    logger.debug(f"  Safe load error: {safe_error}")
                    # Strategy 3: Try with custom_objects for Keras compatibility
                    try:
                        logger.info(f"  Attempting custom object load for {self.location_slug}...")
                        custom_objects = {
                            'LSTM': tf.keras.layers.LSTM,
                            'Dense': tf.keras.layers.Dense,
                            'Dropout': tf.keras.layers.Dropout,
                            'InputLayer': tf.keras.layers.InputLayer
                        }
                        self.model.model = tf.keras.models.load_model(
                            str(self.model_path),
                            compile=False,
                            custom_objects=custom_objects
                        )
                        self.model.model.compile(
                            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                            loss='mse',
                            metrics=['mae']
                        )
                        logger.info(f"  ✓ Custom object load successful for {self.location_slug}")
                    except Exception as custom_error:
                        raise Exception(f"Could not load model after 3 strategies: {str(custom_error)}")
            
            self.preprocessor = WeatherPreprocessor()
            
            # Load the scaler if it exists
            if self.scaler_path.exists():
                self.preprocessor.load_scaler(str(self.scaler_path))
                logger.info(f"✓ Scaler loaded for {self.location_slug}")
            else:
                logger.warning(f"Scaler not found for {self.location_slug}: {self.scaler_path}")
            
            self.is_loaded = True
            logger.info(f"✓ Loaded model for {self.location_slug}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to load model for {self.location_slug}: {e}")
            return False
    
    def predict_next_30_days(self, historical_data_df: pd.DataFrame) -> pd.DataFrame:
        """Generate 30-day forecast"""
        if not self.is_loaded:
            raise ValueError(f"Model not loaded for {self.location_slug}")
        
        try:
            # Select only available feature columns (3 core: temp_max, temp_min, rainfall)
            # Models are trained with exactly 3 features
            feature_columns = [col for col in ["temp_max", "temp_min", "rainfall"] 
                             if col in historical_data_df.columns]
            
            if len(feature_columns) != 3:
                # Ensure we have exactly 3 features for model input
                logger.warning(f"Expected 3 features for {self.location_slug}, found: {feature_columns}")
                feature_columns = ["temp_max", "temp_min", "rainfall"]
            
            # Get last 30 days of data
            last_30_days = historical_data_df[feature_columns].tail(30).values
            logger.debug(f"Input shape before normalization: {last_30_days.shape} (expected: (30, 3))")
            
            # Normalize using the location's fitted scaler
            last_30_days_normalized = self.preprocessor.scaler.transform(last_30_days)
            logger.debug(f"Input shape after normalization: {last_30_days_normalized.shape}")
            
            # Predict
            predictions_normalized = self.model.predict_next_30_days(last_30_days_normalized)
            logger.debug(f"Prediction shape (normalized): {predictions_normalized.shape} (expected: (30, 3))")
            
            # Denormalize
            predictions = self.preprocessor.denormalize_predictions(predictions_normalized)
            logger.debug(f"Prediction shape (denormalized): {predictions.shape}")
            
            # Create DataFrame
            start_date = pd.to_datetime(historical_data_df['date'].max()) + timedelta(days=1)
            dates = [start_date + timedelta(days=i) for i in range(30)]
            
            result_df = pd.DataFrame({
                'date': dates,
                'temp_max': predictions[:, 0],
                'temp_min': predictions[:, 1],
                'rainfall': predictions[:, 2]
            })
            
            return result_df
            
        except Exception as e:
            logger.error(f"Prediction error for {self.location_slug}: {e}")
            raise


class MultiLocationPredictor:
    """
    Manages multiple location-specific LSTM models for weather forecasting
    """
    
    def __init__(self):
        self.models = {}
        self.model_dir = Path("models/locations")
        self.feature_columns = ["temp_max", "temp_min", "rainfall"]
        
        # Load all available models
        self._load_all_models()
    
    def _load_all_models(self):
        """Load all available location models from disk"""
        logger.info("Loading location-specific models...")
        
        if not self.model_dir.exists():
            logger.warning(f"Models directory not found: {self.model_dir}")
            return
        
        # Find all .h5 files (excluding .backup files)
        model_files = [f for f in self.model_dir.glob("lstm_*.h5") if not str(f).endswith('.backup')]
        logger.info(f"Found {len(model_files)} model files")
        
        for model_file in model_files:
            # Extract location slug from filename (lstm_<slug>.h5)
            location_slug = model_file.stem.replace("lstm_", "")
            
            # Find corresponding scaler
            scaler_path = self.model_dir / f"scaler_{location_slug}.pkl"
            
            try:
                location_model = LocationModel(location_slug, model_file, scaler_path)
                if location_model.load():
                    self.models[location_slug] = location_model
            except Exception as e:
                logger.warning(f"Could not load model for {location_slug}: {e}")
        
        logger.info(f"✓ Successfully loaded {len(self.models)} models")
    
    def _get_location_slug(self, location_name: str) -> str:
        """Convert location name to model slug"""
        # Normalize location name
        slug = location_name.lower().replace(" ", "_").replace("-", "_")
        
        # Try exact match
        if slug in self.models:
            return slug
        
        # Try partial match
        for model_slug in self.models.keys():
            if slug in model_slug or model_slug in slug:
                return model_slug
        
        # Fallback to first available model
        if self.models:
            logger.warning(f"Location '{location_name}' not found, using first available model")
            return list(self.models.keys())[0]
        
        raise ValueError(f"No models available and location '{location_name}' not found")
    
    def predict_next_month(self, historical_df: pd.DataFrame, location: str) -> pd.DataFrame:
        """
        Generate 30-day forecast for a location
        
        Args:
            historical_df: DataFrame with historical weather data
            location: Location name for model selection
        
        Returns:
            DataFrame with 30-day predictions
        """
        try:
            # Get location slug
            location_slug = self._get_location_slug(location)
            
            if location_slug not in self.models:
                raise ValueError(f"Model not found for location: {location}")
            
            location_model = self.models[location_slug]
            
            # Generate predictions
            predictions = location_model.predict_next_30_days(historical_df)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Forecast error for {location}: {e}")
            raise
    
    def get_alert_suggestions(self, predictions_df: pd.DataFrame) -> dict:
        """
        Generate weather alerts based on predictions
        
        Args:
            predictions_df: DataFrame with predictions
        
        Returns:
            Dict with alert types and counts
        """
        alerts = {
            "high_temperature": 0,
            "heavy_rainfall": 0,
            "drought_risk": 0,
            "frost_risk": 0,
            "details": []
        }
        
        if predictions_df is None or predictions_df.empty:
            return alerts
        
        # Check for high temperature (>40°C)
        high_temp_days = predictions_df[predictions_df['temp_max'] > 40]
        alerts["high_temperature"] = len(high_temp_days)
        
        # Check for heavy rainfall (>50mm)
        heavy_rain_days = predictions_df[predictions_df['rainfall'] > 50]
        alerts["heavy_rainfall"] = len(heavy_rain_days)
        
        # Determine appropriate "no rain" threshold for drought detection
        # Use adaptive threshold based on data range
        rainfall_values = predictions_df['rainfall'].values
        rainfall_max = float(np.max(rainfall_values))
        
        if rainfall_max < 1.0:
            no_rain_threshold = 0.5
        elif rainfall_max < 5.0:
            no_rain_threshold = 1.0
        else:
            no_rain_threshold = 5.0
        
        # Check for drought (>15 consecutive days without rain)
        dry_streak = 0
        max_dry_streak = 0
        for rain in rainfall_values:
            if rain < no_rain_threshold:
                dry_streak += 1
                max_dry_streak = max(max_dry_streak, dry_streak)
            else:
                dry_streak = 0
        
        if max_dry_streak > 15:
            alerts["drought_risk"] = 1
        
        # Check for frost (<10°C)
        frost_days = predictions_df[predictions_df['temp_min'] < 10]
        alerts["frost_risk"] = len(frost_days)
        
        return alerts
    
    def get_summary_stats(self, predictions_df: pd.DataFrame) -> dict:
        """
        Calculate summary statistics for predictions
        
        Args:
            predictions_df: DataFrame with predictions
        
        Returns:
            Dict with various statistics
        """
        if predictions_df is None or predictions_df.empty:
            return {}
        
        # Calculate stats with NaN handling
        avg_max = float(predictions_df['temp_max'].mean())
        avg_min = float(predictions_df['temp_min'].mean())
        max_temp = float(predictions_df['temp_max'].max())
        min_temp = float(predictions_df['temp_min'].min())
        total_rain = float(predictions_df['rainfall'].sum())
        avg_rain = float(predictions_df['rainfall'].mean())
        
        # Replace NaN/inf with 0 as fallback
        avg_max = 0 if (np.isnan(avg_max) or np.isinf(avg_max)) else avg_max
        avg_min = 0 if (np.isnan(avg_min) or np.isinf(avg_min)) else avg_min
        max_temp = 0 if (np.isnan(max_temp) or np.isinf(max_temp)) else max_temp
        min_temp = 0 if (np.isnan(min_temp) or np.isinf(min_temp)) else min_temp
        total_rain = 0 if (np.isnan(total_rain) or np.isinf(total_rain)) else total_rain
        avg_rain = 0 if (np.isnan(avg_rain) or np.isinf(avg_rain)) else avg_rain
        
        # Determine rainy vs dry days using adaptive threshold
        # If all values are very low (< 1mm), use 0.5mm threshold instead of 5mm
        rainfall_values = predictions_df['rainfall'].values
        rainfall_max = float(np.max(rainfall_values))
        
        if rainfall_max < 1.0:
            # Use 0.5mm threshold for very low rainfall predictions
            rain_threshold = 0.5
        elif rainfall_max < 5.0:
            # Use 1mm threshold for low rainfall predictions
            rain_threshold = 1.0
        else:
            # Use standard 5mm threshold for normal rainfall predictions
            rain_threshold = 5.0
        
        rainy_days = int((rainfall_values > rain_threshold).sum())
        dry_days = int((rainfall_values <= rain_threshold).sum())
        
        return {
            "avg_max_temp": avg_max,
            "avg_min_temp": avg_min,
            "max_temperature": max_temp,
            "min_temperature": min_temp,
            "total_rainfall": total_rain,
            "avg_daily_rainfall": avg_rain,
            "rainy_days": rainy_days,
            "dry_days": dry_days
        }
    
    def format_for_response(self, predictions_df: pd.DataFrame, include_alerts: bool = True) -> dict:
        """
        Format predictions for API response
        
        Args:
            predictions_df: DataFrame with predictions
            include_alerts: Whether to include alert suggestions
        
        Returns:
            Dict formatted for API response
        """
        response = {
            "status": "success",
            "data": {
                "predictions": [],
                "summary": self.get_summary_stats(predictions_df),
                "alerts": self.get_alert_suggestions(predictions_df) if include_alerts else {}
            }
        }
        
        # Convert predictions to list of dicts
        for _, row in predictions_df.iterrows():
            response["data"]["predictions"].append({
                "date": row['date'].strftime("%Y-%m-%d") if hasattr(row['date'], 'strftime') else str(row['date']),
                "temp_max": float(row['temp_max']),
                "temp_min": float(row['temp_min']),
                "rainfall": float(row['rainfall'])
            })
        
        return response
