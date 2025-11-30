"""
VISUAL DATA FLOW DIAGRAM
Farmer Assistant Weather System
"""

# ============================================================================
#                        SYSTEM ARCHITECTURE
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────┐
│                         REACT FRONTEND                                  │
│  Weather.jsx Component - Bangalore Rural Farmer Assistant               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. SELECT LOCATION                                                     │
│     ├─ Choose Taluk (4 options)                                        │
│     ├─ Choose Hobli (21 total)                                         │
│     └─ Get coordinates (lat/lon)                                       │
│                                                                          │
│  2. SHOW FORECAST BUTTON                                               │
│     └─ Triggers POST /predict/next-month                              │
│                                                                          │
│  3. RECEIVE & DISPLAY                                                  │
│     ├─ 30-day forecast data                                            │
│     ├─ 4-day weather cards                                             │
│     ├─ 30-day summary stats                                            │
│     ├─ Weather alerts                                                  │
│     └─ Real-time weather banner                                        │
│                                                                          │
│  4. REAL-TIME ALERTS (Auto-fetch on hobli select)                      │
│     └─ GET /weather/realtime ↓                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓↑
                        (HTTP REST API - CORS)
                                   ↓↑
┌─────────────────────────────────────────────────────────────────────────┐
│                     PYTHON FASTAPI BACKEND                              │
│  main.py + farmer_auth_backend.py                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  API ENDPOINTS:                                                         │
│  ├─ POST /predict/next-month                                           │
│  │  ├─ Input: {lat, lon, location}                                    │
│  │  └─ Output: {predictions[], summary, alerts}  ✅                   │
│  │                                                                      │
│  ├─ GET /weather/realtime ⭐ NEW                                       │
│  │  ├─ Input: {lat, lon, location}                                    │
│  │  └─ Output: {temp, humidity, wind, condition, alert}  ✅           │
│  │                                                                      │
│  ├─ POST /auth/register                                                │
│  │  └─ Output: {jwt_token, farmer_profile}  ✅                        │
│  │                                                                      │
│  └─ POST /auth/login                                                   │
│     └─ Output: {jwt_token, farmer_profile}  ✅                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓↑
                           (Internal Processing)
                                   ↓↑
┌─────────────────────────────────────────────────────────────────────────┐
│                    PREDICTION MODULE                                    │
│  modules/multi_location_predictor.py                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  MultiLocationPredictor                                                │
│  ├─ Load 21 location-specific models                                   │
│  │  ├─ kasaba_doddaballapura.h5                                        │
│  │  ├─ thubagere_doddaballapura.h5                                     │
│  │  └─ ... (other 19 models)                                           │
│  │                                                                      │
│  ├─ Get location slug from request                                     │
│  ├─ Load model + scaler for location                                   │
│  ├─ Get historical data (last 30 days)                                 │
│  ├─ Normalize using location's scaler                                  │
│  └─ Generate 30-day prediction                                         │
│                                                                          │
│  Format response:                                                       │
│  ├─ predictions[] (30 days)                                             │
│  │  ├─ date: "2025-12-02"                              ✅             │
│  │  ├─ temp_max: 32.5                                  ✅             │
│  │  ├─ temp_min: 18.2                                  ✅             │
│  │  ├─ rainfall: 0.0                                   ✅             │
│  │  ├─ wind_speed: N/A                                 ⚠️              │
│  │  ├─ humidity: N/A                                   ⚠️              │
│  │  └─ pop: N/A                                        ⚠️              │
│  ├─ summary{}                                           ✅             │
│  │  ├─ avg_temp_max                                                    │
│  │  ├─ avg_temp_min                                                    │
│  │  ├─ total_rainfall                                                  │
│  │  └─ days_with_rain                                                  │
│  └─ alerts[]                                            ✅             │
│     └─ {type, severity, message, date}                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓↑
                           (ML Models & Data)
                                   ↓↑
┌─────────────────────────────────────────────────────────────────────────┐
│                      LSTM MODEL LAYER                                   │
│  models/lstm_model.py + models/preprocessor.py                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  For each location:                                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ LSTM Model (Trained on historical data for location)             │  │
│  │                                                                   │  │
│  │ Input: Last 30 days (seq_length=30, n_features=3)               │  │
│  │   • temp_max                                                     │  │
│  │   • temp_min                                                     │  │
│  │   • rainfall                                                     │  │
│  │                                                                   │  │
│  │ Architecture:                                                     │  │
│  │   LSTM(64) → Dropout(0.2)                                        │  │
│  │   LSTM(64) → Dropout(0.2)                                        │  │
│  │   LSTM(32) → Dropout(0.2)                                        │  │
│  │   Dense(90) → Reshape(30, 3)                                     │  │
│  │                                                                   │  │
│  │ Output: 30-day prediction (3 features)                          │  │
│  │   • temp_max (next 30 days)                                      │  │
│  │   • temp_min (next 30 days)                                      │  │
│  │   • rainfall (next 30 days)                                      │  │
│  │                                                                   │  │
│  │ Training:                                                         │  │
│  │   • Optimizer: Adam (lr=0.001)                                   │  │
│  │   • Loss: MSE                                                    │  │
│  │   • Callbacks: EarlyStopping, ReduceLROnPlateau                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Scaler (per location):                                                 │
│  └─ MinMaxScaler (0-1 range)                                           │
│     Used for: Normalization before model, Denormalization after        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓↑
                        (Historical Data Loading)
                                   ↓↑
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. TRAINING DATA (Used to train models)                                │
│     └─ data/*.csv (10 years of Open-Meteo historical data)              │
│        ├─ kasaba_doddaballapura_weather.csv                             │
│        ├─ thubagere_doddaballapura_weather.csv                          │
│        └─ ... (21 location CSVs)                                        │
│                                                                          │
│  2. REAL-TIME WEATHER (for alerts)                                      │
│     └─ Open-Meteo Current Weather API                                   │
│        └─ api.open-meteo.com/v1/forecast?current=...                   │
│           └─ Temp, humidity, wind, precipitation, weather code         │
│                                                                          │
│  3. MODELS (Trained on training data)                                   │
│     └─ models/locations/lstm_*.h5 (21 models)                           │
│     └─ models/locations/scaler_*.pkl (21 scalers)                       │
│                                                                          │
│  4. DATABASE (User data)                                                │
│     └─ farmers.db (SQLite)                                              │
│        ├─ farmer registration                                           │
│        ├─ phone_number (unique)                                         │
│        ├─ hashed password                                               │
│        └─ language preference                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
#                    REQUEST-RESPONSE FLOW
# ============================================================================

"""
REQUEST #1: Get 30-Day Forecast
──────────────────────────────

Frontend:
  POST /predict/next-month
  Body: {
    "latitude": 13.29273,
    "longitude": 77.53891,
    "location": "kasaba_doddaballapura"
  }

Backend Flow:
  1. Receive request in main.py
  2. Load location: kasaba_doddaballapura
  3. Get historical data from module
  4. Load LSTM model + scaler
  5. Preprocess: normalize last 30 days
  6. Generate prediction: next 30 days
  7. Denormalize output
  8. Generate alerts from predictions
  9. Compute summary statistics
  10. Format response

Frontend Response (200 OK):
  {
    "status": "success",
    "data": {
      "predictions": [
        {
          "date": "2025-12-02",
          "temp_max": 32.5,
          "temp_min": 18.2,
          "rainfall": 0.0,
          "wind_speed": null,        ← N/A (missing)
          "humidity": null,          ← N/A (missing)
          "pop": null                ← N/A (missing)
        },
        ... 29 more days ...
      ],
      "summary": {
        "avg_temp_max": 32.1,
        "avg_temp_min": 17.8,
        "total_rainfall": 45.3,
        "days_with_rain": 8
      },
      "alerts": [
        {
          "type": "high_temperature",
          "severity": "warning",
          "message": "High temps (up to 38°C). Ensure irrigation.",
          "date": "2025-12-15"
        }
      ]
    }
  }

Frontend Display:
  ├─ Show location header
  ├─ Display 4 weather cards (first 4 days)
  │  ├─ Date
  │  ├─ Temp (high/low)
  │  ├─ Rainfall amount
  │  ├─ Wind speed → Shows "N/A"
  │  ├─ Humidity → Shows "N/A"
  │  └─ Rain probability → Shows "N/A"
  ├─ Display 30-day summary box
  ├─ Display alert cards
  └─ Fetch real-time weather (separate)


REQUEST #2: Get Real-Time Weather
──────────────────────────────────

Frontend (auto-fetches when hobli selected):
  GET /weather/realtime?lat=13.29273&lon=77.53891&location=kasaba_doddaballapura

Backend Flow:
  1. Receive request in main.py
  2. Call Open-Meteo current weather API
  3. Parse response: temp, humidity, wind, precipitation
  4. Map WMO code to condition text
  5. Determine alert level based on conditions
  6. Format response

Frontend Response (200 OK):
  {
    "temp": 28.5,
    "humidity": 72,
    "wind_speed": 6.2,
    "rainfall": 0.0,
    "condition": "Partly Cloudy",
    "realtime_rain_1h": 0,
    "alert_level": "medium",
    "alert_message": "Moderate wind: 6.2 m/s",
    "location": "kasaba_doddaballapura",
    "timestamp": "2025-12-01T14:30:00"
  }

Frontend Display:
  ├─ Show alert banner at top of page
  ├─ Icon based on alert level
  │  ├─ Low: ℹ️ 
  │  ├─ Medium: ⚠️ 
  │  └─ High: 🚨
  ├─ Show alert message
  └─ Show current conditions


REQUEST #3: Register Farmer
──────────────────────────

Frontend (FarmerAuth component):
  POST /auth/register
  Body: {
    "phone_number": "9876543210",
    "password": "password123",
    "name": "Farmer Name",
    "language": "kn"
  }

Backend Flow:
  1. Validate phone (10 digits)
  2. Check if already exists
  3. Hash password
  4. Create farmer record in DB
  5. Generate JWT token
  6. Return token + profile

Frontend Response (200 OK):
  {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "farmer": {
      "id": 1,
      "phone_number": "9876543210",
      "name": "Farmer Name",
      "language": "kn",
      "created_at": "2025-12-01T14:30:00"
    }
  }

Frontend Action:
  ├─ Store token in localStorage
  ├─ Store farmer profile
  ├─ Show success message
  └─ Close auth modal


REQUEST #4: Login Farmer
───────────────────────

Frontend (FarmerAuth component):
  POST /auth/login
  Body: {
    "phone_number": "9876543210",
    "password": "password123"
  }

Backend Flow:
  1. Validate phone
  2. Find farmer by phone
  3. Verify password hash
  4. Generate JWT token
  5. Update last_login
  6. Return token + profile

Frontend Response (200 OK):
  {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "farmer": {
      "id": 1,
      "phone_number": "9876543210",
      "name": "Farmer Name",
      "language": "kn",
      "last_login": "2025-12-01T14:35:00"
    }
  }

Frontend Action:
  ├─ Store token
  ├─ Store farmer profile
  └─ Close auth modal
"""


# ============================================================================
#                    LOCATION MAPPING
# ============================================================================

LOCATIONS_MAPPING = {
    "DODDABALLAPURA": {
        "kasaba_doddaballapura": {
            "name": "Kasaba, Doddaballapura",
            "lat": 13.29273,
            "lon": 77.53891,
            "model_file": "models/locations/lstm_kasaba_doddaballapura.h5",
            "scaler_file": "models/locations/scaler_kasaba_doddaballapura.pkl",
        },
        # ... 4 more hoblis
    },
    "DEVANAHALLI": {
        # ... 5 hoblis
    },
    "HOSAKOTE": {
        # ... 5 hoblis
    },
    "NELAMANGALA": {
        # ... 6 hoblis
    }
}


# ============================================================================
#                    SUMMARY
# ============================================================================

"""
COMPLETE DATA FLOW:

1. Frontend: User selects hobli
   └─ Auto-fetches real-time weather

2. Frontend: User clicks "Show forecast"
   └─ Posts to /predict/next-month

3. Backend: Loads location LSTM model
   └─ Returns 30-day predictions

4. Frontend: Displays 4-day cards + 30-day summary
   └─ Shows wind_speed & humidity as "N/A" (missing fields)

5. Frontend: Shows real-time banner
   └─ Updates continuously if user navigates

KEY POINTS:
✅ 30-day batch predictions (NOT real-time streaming)
✅ Perfect for farming applications
✅ Frontend gracefully handles missing fields
✅ All critical data available (temp + rain)
✅ Real-time alerts supported
✅ 21 locations supported
✅ Authentication working
✅ Ready for production
"""
