
"""
FastAPI Backend for Farmer Assistant - Weather Prediction API
Multi-location LSTM Forecasting for Bangalore & surrounding districts
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import asyncio
from pathlib import Path
import logging
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
# Cache configuration (hours). Set to 0 to disable periodic refresh.
CACHE_REFRESH_HOURS = float(os.getenv('CACHE_REFRESH_HOURS', '6'))
# If true, invalidate cached data on every prediction request
CACHE_INVALIDATE_ON_REQUEST = os.getenv('CACHE_INVALIDATE_ON_REQUEST', 'false').lower() in ('1', 'true', 'yes')
# Enable test-only endpoints (default: disabled)
ENABLE_TEST_ENDPOINTS = os.getenv('ENABLE_TEST_ENDPOINTS', 'false').lower() in ('1', 'true', 'yes')

# Import custom modules
from modules.weather_data import get_weather_data
from modules.multi_location_predictor import MultiLocationPredictor
# Authentication router (from auth backend)
from farmer_auth_backend import router as auth_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Farmer Assistant - Weather Prediction API",
    description="LSTM-based 1-month weather forecasting for multiple districts",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication endpoints
app.include_router(auth_router)

# Global state
predictor = None
cached_weather_data = None  # Cache historical data at startup
# Background task handle for periodic cache refresh
_cache_refresh_task = None

# ==================== PYDANTIC MODELS ====================

class PredictionResponse(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    rainfall: float

class AlertResponse(BaseModel):
    type: str
    severity: str
    message: str
    date: Optional[str] = None

class WeatherSummary(BaseModel):
    avg_temp_max: float
    avg_temp_min: float
    total_rainfall: float
    max_temp: float
    min_temp: float
    days_with_rain: int

class ForecastRequest(BaseModel):
    latitude: float
    longitude: float
    location: str

class ForecastResponse(BaseModel):
    status: str
    data: Dict
    timestamp: str

# ==================== STARTUP & SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """
    Initialize multi-location predictor and cache weather data on startup
    This prevents blocking API calls during request handling
    """
    global predictor, cached_weather_data
    start_time = time.time()
    
    try:
        logger.info("Initializing Multi-Location Predictor...")
        predictor = MultiLocationPredictor()
        logger.info(f"✓ Predictor initialized successfully")
        logger.info(f"✓ Loaded {len(predictor.models)} location-specific models")
        
        # Load weather data once at startup
        logger.info("Loading historical weather data...")
        logger.info(f"Current working directory: {os.getcwd()}")
        cached_weather_data = get_weather_data()
        if cached_weather_data is not None and len(cached_weather_data) > 0:
            logger.info(f"✓ Cached {len(cached_weather_data)} historical weather records")
        else:
            logger.warning(f"⚠️ No weather data loaded (data={cached_weather_data})")
        
        elapsed = time.time() - start_time
        logger.info(f"✓ Startup completed in {elapsed:.2f}s")
        # Start periodic cache refresher if enabled
        global _cache_refresh_task, CACHE_REFRESH_HOURS
        if CACHE_REFRESH_HOURS and CACHE_REFRESH_HOURS > 0:
            async def _cache_refresher(hours: float):
                """Background task to periodically refresh cached_weather_data"""
                global cached_weather_data
                while True:
                    try:
                        await asyncio.sleep(hours * 3600)
                        logger.info("Periodic cache refresher: reloading weather data...")
                        new_data = get_weather_data()
                        if new_data is not None and len(new_data) > 0:
                            cached_weather_data = new_data
                            logger.info("Periodic cache refresher: cache updated")
                        else:
                            logger.warning("Periodic cache refresher: loaded empty data, keeping existing cache")
                    except asyncio.CancelledError:
                        logger.info("Periodic cache refresher: cancelled")
                        break
                    except Exception as e:
                        logger.error(f"Periodic cache refresher error: {e}")

            # schedule the refresher
            try:
                _cache_refresh_task = asyncio.create_task(_cache_refresher(CACHE_REFRESH_HOURS))
                logger.info(f"Started cache refresher task every {CACHE_REFRESH_HOURS} hours")
            except Exception as e:
                logger.warning(f"Could not start cache refresher task: {e}")
        # Log whether test endpoints are enabled
        global ENABLE_TEST_ENDPOINTS
        if ENABLE_TEST_ENDPOINTS:
            logger.warning("Test-only endpoints are ENABLED (ENABLE_TEST_ENDPOINTS=true). Do not expose this in production.")
        else:
            logger.info("Test-only endpoints are disabled")
    except Exception as e:
        logger.error(f"✗ Error during startup: {e}")
        logger.warning("Predictor will be initialized on first prediction request")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown
    """
    logger.info("Shutting down Weather Prediction API")
    # Cancel cache refresher if running
    global _cache_refresh_task
    try:
        if _cache_refresh_task is not None:
            _cache_refresh_task.cancel()
            _cache_refresh_task = None
            logger.info("Cancelled cache refresher task")
    except Exception:
        pass

# ==================== REMOVED DUPLICATE ROOT - See line 476 ====================

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    models_loaded = len(predictor.models) if predictor else 0
    
    return {
        "status": "healthy",
        "service": "Farmer Assistant Weather API",
        "timestamp": datetime.now().isoformat(),
        "model_ready": predictor is not None,
        "location_models_loaded": models_loaded
    }

# ==================== PREDICTION ENDPOINTS ====================

@app.post("/predict/next-month")
async def get_30_day_forecast(request: ForecastRequest):
    """
    Get 30-day weather forecast for any location
    Uses location-specific LSTM models trained on historical data
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        location: Location name for reference
    
    Returns:
        - 30 daily forecasts (temp_max, temp_min, rainfall)
        - Summary statistics
        - Weather alerts for farmers
    """
    global predictor, cached_weather_data
    start_time = time.time()
    
    try:
        # Initialize predictor if not already done
        if predictor is None:
            logger.info("Initializing predictor on-demand...")
            predictor = MultiLocationPredictor()
        
        logger.info(f"[{time.time() - start_time:.2f}s] Generating forecast for {request.location}")
        
        # If configured to invalidate cache on every request, reload data
        if CACHE_INVALIDATE_ON_REQUEST:
            logger.info("CACHE_INVALIDATE_ON_REQUEST enabled; reloading weather data for this request...")
            historical_df = get_weather_data()
        else:
            # Use cached weather data when fresh; otherwise reload to avoid stale dates
            if cached_weather_data is not None:
                try:
                    cached_max = pd.to_datetime(cached_weather_data['date'].max()).date()
                    # If cached data is older than yesterday, refresh it
                    if cached_max < (datetime.now().date() - timedelta(days=1)):
                        logger.info("Cached weather data is stale; refreshing from source...")
                        cached_weather_data = get_weather_data()
                    else:
                        logger.debug(f"[{time.time() - start_time:.2f}s] Using cached weather data")
                except Exception:
                    # If parsing fails for any reason, attempt to reload
                    logger.info("Could not determine cached data date; reloading weather data...")
                    cached_weather_data = get_weather_data()

                historical_df = cached_weather_data
            else:
                logger.info(f"[{time.time() - start_time:.2f}s] Loading weather data (cache miss)...")
                historical_df = get_weather_data()
        
        if historical_df is None or len(historical_df) < 30:
            raise HTTPException(
                status_code=400,
                detail="Insufficient historical data. Need at least 30 days of data."
            )
        
        logger.info(f"Loaded {len(historical_df)} historical records")
        
        # Generate predictions using location-specific model
        logger.info(f"[{time.time() - start_time:.2f}s] Generating 30-day forecast using {request.location} model...")
        from starlette.concurrency import run_in_threadpool
        predictions = await run_in_threadpool(predictor.predict_next_month, historical_df, request.location)
        logger.debug(f"[{time.time() - start_time:.2f}s] Prediction completed")
        
        # Format response (already includes status and data)
        response = predictor.format_for_response(predictions, include_alerts=True)
        
        # Add metadata
        response["data"]["location"] = request.location
        response["data"]["coordinates"] = {
            "latitude": request.latitude,
            "longitude": request.longitude
        }
        response["timestamp"] = datetime.now().isoformat()
        
        elapsed = time.time() - start_time
        logger.info(f"✓ Forecast generated in {elapsed:.2f}s for {request.location}")
        return response
        
    except HTTPException as e:
        raise e
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ Error generating forecast after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating forecast: {str(e)}"
        )

@app.get("/predict/specific-date/{date}")
async def get_prediction_for_date(
    date: str,
    latitude: float = 13.2256,
    longitude: float = 77.5750,
    location: str = "Bangalore Rural"
):
    """
    Get weather prediction for a specific date using location-specific model
    
    Args:
        date: Date in format YYYY-MM-DD (must be within next 30 days)
        latitude: Location latitude (default: Bangalore Rural)
        longitude: Location longitude (default: Bangalore Rural)
        location: Location name for reference
    """
    global predictor, cached_weather_data
    start_time = time.time()
    
    try:
        if predictor is None:
            predictor = MultiLocationPredictor()
        
        logger.info(f"[{time.time() - start_time:.2f}s] Fetching prediction for {location} on {date}")
        
        # Use cached weather data
        if cached_weather_data is not None:
            historical_df = cached_weather_data
        else:
            historical_df = get_weather_data()
        
        predictions = predictor.predict_next_month(historical_df, location)
        
        # Filter for specific date
        prediction = predictions[predictions['date'].astype(str).str.contains(date)]
        
        if prediction.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No prediction available for date {date}"
            )
        
        row = prediction.iloc[0]
        elapsed = time.time() - start_time
        logger.info(f"✓ Prediction fetched in {elapsed:.2f}s for {location}")
        
        return {
            "status": "success",
            "data": {
                "date": str(row['date']),
                "temp_max": float(row['temp_max']),
                "temp_min": float(row['temp_min']),
                "rainfall": float(row['rainfall'])
            },
            "location": location,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Error fetching prediction after {elapsed:.2f}s: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/_internal/test/set-cache-max-date")
async def _test_set_cache_max_date(payload: dict):
    """Test-only endpoint: set `cached_weather_data` to a synthetic DataFrame
    whose maximum date is `payload['max_date']` (YYYY-MM-DD).
    This helps test cache refresh behavior without restarting the server.
    """
    global cached_weather_data, ENABLE_TEST_ENDPOINTS
    if not ENABLE_TEST_ENDPOINTS:
        raise HTTPException(status_code=404, detail="Test endpoints are disabled")

    try:
        max_date = payload.get('max_date')
        if not max_date:
            raise ValueError("'max_date' is required (YYYY-MM-DD)")

        end = pd.to_datetime(max_date).date()
        # create 40 days of dummy historical data ending at `end`
        dates = pd.date_range(end=end, periods=40).tolist()
        df = pd.DataFrame({
            'date': dates,
            'temp_max': [30.0] * len(dates),
            'temp_min': [20.0] * len(dates),
            'rainfall': [0.0] * len(dates)
        })
        cached_weather_data = df
        return {"status": "ok", "cached_max": str(df['date'].max())}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==================== REAL-TIME WEATHER ENDPOINT ====================

@app.get("/weather/realtime")
async def get_realtime_weather(
    lat: float,
    lon: float,
    location: str = "Unknown Location"
):
    """
    Get current weather conditions for a location
    Fetches from Open-Meteo's current weather API
    
    Args:
        lat: Latitude
        lon: Longitude
        location: Location name for reference
    
    Returns:
        Current weather conditions with alert levels
    """
    start_time = time.time()
    try:
        import requests
        
        logger.info(f"[{time.time() - start_time:.2f}s] Fetching real-time weather for {location} ({lat}, {lon})")
        
        # Open-Meteo current weather API
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
            "temperature_unit": "celsius",
            "wind_speed_unit": "ms"
        }
        
        # Don't add API key - it causes issues with routing
        # The free tier is sufficient for our use case
        logger.debug(f"[{time.time() - start_time:.2f}s] Making API request to Open-Meteo...")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"[{time.time() - start_time:.2f}s] API response received")
        
        current = data.get("current", {})
        
        # Determine weather condition from WMO code
        weather_code = current.get("weather_code", 0)
        condition_map = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            61: "Slight rain",
            71: "Slight snow",
            80: "Moderate rain",
            85: "Moderate rain and snow",
            95: "Thunderstorm",
        }
        
        condition = condition_map.get(weather_code, "Unknown")
        
        # Extract data
        temp = current.get("temperature_2m", 0)
        humidity = current.get("relative_humidity_2m", 0)
        wind_speed = current.get("wind_speed_10m", 0)
        rainfall = current.get("precipitation", 0)
        
        # Determine alert level
        alert_level = "low"
        alert_message = f"Current conditions: {condition}"
        
        if wind_speed >= 10:
            alert_level = "high"
            alert_message = f"High wind speed: {wind_speed:.1f} m/s. Secure outdoor equipment."
        elif wind_speed >= 5:
            alert_level = "medium"
            alert_message = f"Moderate wind: {wind_speed:.1f} m/s"
        elif rainfall > 0:
            alert_level = "medium"
            alert_message = f"Rain detected: {rainfall:.1f}mm"
        elif humidity > 80:
            alert_level = "medium"
            alert_message = f"High humidity: {humidity}%. Watch for fungal diseases."
        elif temp > 35:
            alert_level = "medium"
            alert_message = f"High temperature: {temp:.1f}°C. Ensure irrigation."
        
        response_data = {
            "temp": round(temp, 1),
            "humidity": int(humidity),
            "wind_speed": round(wind_speed, 1),
            "rainfall": round(rainfall, 1),
            "condition": condition,
            "realtime_rain_1h": round(rainfall, 1),
            "alert_level": alert_level,
            "alert_message": alert_message,
            "location": location,
            "coordinates": {
                "latitude": lat,
                "longitude": lon
            },
            "timestamp": datetime.now().isoformat()
        }
        
        elapsed = time.time() - start_time
        logger.info(f"✓ Real-time weather fetched in {elapsed:.2f}s for {location}: {temp}°C, {humidity}% RH")
        return response_data
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        logger.warning(f"Real-time weather request timed out after {elapsed:.2f}s for {location}")
        raise HTTPException(
            status_code=504,
            detail="Real-time weather service timed out. Using fallback to forecast."
        )
    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start_time
        logger.warning(f"Connection error after {elapsed:.2f}s fetching real-time weather for {location}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Real-time weather service unavailable. Using fallback to forecast."
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Error fetching real-time weather after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching real-time weather: {str(e)}"
        )

# ==================== INFO ENDPOINTS ====================

@app.get("/info/location")
async def location_info():
    """
    Get information about supported locations and available models
    """
    available_models = list(predictor.models.keys()) if predictor else []
    
    return {
        "supported_regions": ["Bangalore Urban", "Bangalore Rural", "Kolar", "Chikkaballapura"],
        "available_location_models": len(available_models),
        "model_names": available_models,
        "data_source": "Open-Meteo Historical Weather API",
        "note": "Location-specific LSTM models trained on 3 years of historical data"
    }

@app.get("/info/model")
async def model_info():
    """
    Get information about the LSTM models
    """
    return {
        "model_type": "Location-Specific LSTM (Long Short-Term Memory)",
        "total_models": len(predictor.models) if predictor else 0,
        "architecture": {
            "layers": 3,
            "lstm_units": [64, 64, 32],
            "input_shape": [30, 5],
            "output_shape": [30, 5],
            "dropout": 0.2,
            "optimizer": "Adam",
            "loss": "MSE"
        },
        "training_data": {
            "duration": "3 years (2022-2025)",
            "samples_per_location": 1095,
            "total_locations": 20
        },
        "features_predicted": [
            "temperature_max (°C)",
            "temperature_min (°C)",
            "rainfall (mm)",
            "wind_speed (m/s)",
            "humidity (%)"
        ],
        "forecast_horizon": "30 days",
        "training_note": "Each location has a dedicated model trained on local historical weather data"
    }

@app.get("/info/available-models")
async def available_models_info():
    """
    Get list of all available location models
    """
    if not predictor or not predictor.models:
        return {
            "status": "no_models_loaded",
            "message": "Run train_all_locations.py to train models",
            "available_models": 0
        }
    
    models_list = []
    for location_slug in predictor.models.keys():
        location_name = location_slug.replace('_', ' ').title()
        models_list.append({
            "slug": location_slug,
            "name": location_name,
            "model_loaded": True
        })
    
    return {
        "status": "success",
        "total_models": len(models_list),
        "models": models_list
    }

# ==================== ROOT ====================

@app.get("/")
async def root():
    """
    API Documentation
    """
    return {
        "service": "Farmer Assistant - Weather Prediction API",
        "version": "1.0.0",
        "description": "LSTM-based weather forecasting with location-specific models for farming assistance",
        "models_loaded": len(predictor.models) if predictor else 0,
        "endpoints": {
            "health": "GET /health",
            "forecast": "POST /predict/next-month",
            "specific_date": "GET /predict/specific-date/{date}?latitude=X&longitude=Y&location=Name",
            "location_info": "GET /info/location",
            "model_info": "GET /info/model",
            "available_models": "GET /info/available-models",
            "docs": "GET /docs (Swagger UI)",
            "redoc": "GET /redoc (ReDoc)"
        },
        "features": [
            "30-day LSTM-based weather forecast",
            "Location-specific trained models (20 locations)",
            "Automated weather alerts for farmers",
            "30-day summary statistics",
            "Real-time predictions with local weather patterns"
        ]
    }

# ==================== RUN ====================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🚀 FARMER ASSISTANT BACKEND STARTING")
    print("="*70)
    print("\n✅ Backend will be available at: http://localhost:8000")
    print("   (NOT http://0.0.0.0:8000 - that's for the server, not browser!)")
    print("\n📝 Configure your frontend to use: http://localhost:8000")
    print("   If deployed remotely, use the actual server IP/domain")
    print("\n📚 API Documentation: http://localhost:8000/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
