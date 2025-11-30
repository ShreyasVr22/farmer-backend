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
            
            self.model = WeatherLSTMModel()
            self.model.load_model(str(self.model_path))
            
            self.preprocessor = WeatherPreprocessor()
            if self.scaler_path.exists():
                self.preprocessor.load_scaler(str(self.scaler_path))
            
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
            feature_columns = [col for col in ["temp_max", "temp_min", "rainfall", "wind_speed", "humidity"] 
                             if col in historical_data_df.columns]
            
            if len(feature_columns) < 3:
                logger.warning(f"Insufficient features for {self.location_slug}: {feature_columns}")
                feature_columns = ["temp_max", "temp_min", "rainfall"]
            
            # Get last 30 days
            last_30_days = historical_data_df[feature_columns].tail(30).values
            
            # Normalize
            last_30_days_normalized = self.preprocessor.scaler.transform(last_30_days)
            
            # Predict
            predictions_normalized = self.model.predict_next_30_days(last_30_days_normalized)
            
            # Denormalize
            predictions = self.preprocessor.denormalize_predictions(predictions_normalized)
            
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
        
        # Find all .h5 files
        model_files = list(self.model_dir.glob("lstm_*.h5"))
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
        
        # Check for drought (>15 consecutive days without rain)
        dry_streak = 0
        max_dry_streak = 0
        for rain in predictions_df['rainfall'].values:
            if rain < 5:
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
        
        return {
            "avg_max_temp": float(predictions_df['temp_max'].mean()),
            "avg_min_temp": float(predictions_df['temp_min'].mean()),
            "max_temperature": float(predictions_df['temp_max'].max()),
            "min_temperature": float(predictions_df['temp_min'].min()),
            "total_rainfall": float(predictions_df['rainfall'].sum()),
            "avg_daily_rainfall": float(predictions_df['rainfall'].mean()),
            "rainy_days": int((predictions_df['rainfall'] > 5).sum()),
            "dry_days": int((predictions_df['rainfall'] <= 5).sum())
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
