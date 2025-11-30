"""
Prediction logic and utilities
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import joblib
from models.preprocessor import WeatherPreprocessor
from models.lstm_model import WeatherLSTMModel

class WeatherPredictor:
    """
    Handle weather predictions for the Farmer Assistant app
    """
    
    def __init__(self):
        self.preprocessor = WeatherPreprocessor()
        self.model = WeatherLSTMModel()
        self.feature_columns = ["temp_max", "temp_min", "rainfall", "wind_speed", "humidity"]
        
        # Load saved model and scaler
        self.model.load_model()
        self.preprocessor.load_scaler()
    
    def predict_next_month(self, historical_data_df):
        """
        Predict weather for next 30 days
        
        Args:
            historical_data_df: DataFrame with columns [date, temp_max, temp_min, rainfall, wind_speed, humidity]
        
        Returns:
            Dict with predicted values for next 30 days
        """
        
        # Get last 30 days and normalize
        last_30_days = historical_data_df[self.feature_columns].tail(30).values
        last_30_days_normalized = self.preprocessor.scaler.transform(last_30_days)
        
        # Predict next 30 days (still normalized)
        predictions_normalized = self.model.predict_next_30_days(last_30_days_normalized)
        
        # Denormalize predictions
        predictions = self.preprocessor.denormalize_predictions(predictions_normalized)
        
        # Create result dataframe
        start_date = historical_data_df['date'].max() + timedelta(days=1)
        dates = [start_date + timedelta(days=i) for i in range(30)]
        
        result_df = pd.DataFrame({
            'date': dates,
            'temp_max': predictions[:, 0],
            'temp_min': predictions[:, 1],
            'rainfall': predictions[:, 2],
            'wind_speed': predictions[:, 3],
            'humidity': predictions[:, 4]
        })
        
        return result_df
    
    def get_alert_suggestions(self, predictions_df):
        """
        Generate weather alerts based on predictions
        Useful for farmers to make decisions
        """
        alerts = []
        
        # High temperature alert
        if predictions_df['temp_max'].max() > 40:
            alerts.append({
                "type": "high_temperature",
                "severity": "warning",
                "message": f"High temperatures expected (up to {predictions_df['temp_max'].max():.1f}°C). Ensure adequate irrigation.",
                "date": predictions_df[predictions_df['temp_max'] == predictions_df['temp_max'].max()]['date'].values[0]
            })
        
        # Heavy rainfall alert
        if predictions_df['rainfall'].max() > 50:
            alerts.append({
                "type": "heavy_rainfall",
                "severity": "warning",
                "message": f"Heavy rainfall expected (up to {predictions_df['rainfall'].max():.1f}mm). Ensure proper drainage.",
                "date": predictions_df[predictions_df['rainfall'] == predictions_df['rainfall'].max()]['date'].values[0]
            })
        
        # No rainfall alert
        no_rain_days = len(predictions_df[predictions_df['rainfall'] < 1])
        if no_rain_days > 15:
            alerts.append({
                "type": "drought_risk",
                "severity": "info",
                "message": f"Low rainfall expected ({no_rain_days} dry days). Plan irrigation accordingly.",
                "date": None
            })
        
        # Cold night alert
        if predictions_df['temp_min'].min() < 10:
            alerts.append({
                "type": "frost_risk",
                "severity": "warning",
                "message": f"Low temperatures expected (down to {predictions_df['temp_min'].min():.1f}°C). Frost risk possible.",
                "date": predictions_df[predictions_df['temp_min'] == predictions_df['temp_min'].min()]['date'].values[0]
            })
        
        return alerts
    
    def get_summary_stats(self, predictions_df):
        """
        Get summary statistics for the predicted month
        """
        return {
            "avg_temp_max": round(predictions_df['temp_max'].mean(), 2),
            "avg_temp_min": round(predictions_df['temp_min'].mean(), 2),
            "total_rainfall": round(predictions_df['rainfall'].sum(), 2),
            "avg_humidity": round(predictions_df['humidity'].mean(), 2),
            "avg_wind_speed": round(predictions_df['wind_speed'].mean(), 2),
            "max_temp": round(predictions_df['temp_max'].max(), 2),
            "min_temp": round(predictions_df['temp_min'].min(), 2),
            "days_with_rain": int(len(predictions_df[predictions_df['rainfall'] > 0]))
        }
    
    def format_for_response(self, predictions_df, include_alerts=True):
        """
        Format predictions for API response
        """
        # Convert dates to string
        predictions_df_copy = predictions_df.copy()
        predictions_df_copy['date'] = predictions_df_copy['date'].astype(str)
        
        response = {
            "status": "success",
            "data": {
                "predictions": predictions_df_copy.to_dict('records'),
                "summary": self.get_summary_stats(predictions_df)
            }
        }
        
        if include_alerts:
            response["data"]["alerts"] = self.get_alert_suggestions(predictions_df)
        
        return response
