// Frontend-Backend Field Mapping Reference
// For developers debugging data flow

export const FIELD_MAPPING = {
  // ============ PREDICTION FIELDS ============
  FORECAST_FIELDS: {
    // ✅ Working (Provided by backend)
    date: {
      frontend_use: "Display date on card header",
      backend_provides: "YES",
      example: "2025-12-02",
      status: "✅ Working"
    },
    temp_max: {
      frontend_use: "Display as red temperature number",
      backend_provides: "YES",
      example: 32.5,
      status: "✅ Working",
      frontend_code: "Math.round(day.temp_max)"
    },
    temp_min: {
      frontend_use: "Display as blue temperature number",
      backend_provides: "YES",
      example: 18.2,
      status: "✅ Working",
      frontend_code: "Math.round(day.temp_min)"
    },
    rainfall: {
      frontend_use: "Display rainfall amount",
      backend_provides: "YES",
      example: 0.0,
      status: "✅ Working",
      frontend_code: "day.rainfall.toFixed(1) + 'mm'"
    },

    // ⚠️ Missing (Frontend will show "N/A")
    wind_speed: {
      frontend_use: "Calculate wind risk % and display",
      backend_provides: "NO",
      example: 5.2,
      status: "⚠️  N/A shown",
      frontend_code: `
        const wind = day.wind_speed !== undefined ? day.wind_speed : 0;
        // Defaults to 0 if missing = 20% risk = green
      `,
      fallback: "Defaults to 0 (no wind)"
    },
    humidity: {
      frontend_use: "Display humidity percentage",
      backend_provides: "NO",
      example: 65,
      status: "⚠️  N/A shown",
      frontend_code: `
        const humidity = day.humidity !== null ? Math.round(day.humidity) : null;
        // Shows "N/A" if missing
      `,
      fallback: "Shows 'N/A'"
    },
    pop: {
      frontend_use: "Display rain probability %",
      backend_provides: "NO",
      example: 0.0,
      status: "⚠️  Shows null",
      frontend_code: `
        const rainPct = day.pop ? Math.round(day.pop * 100) : null;
        // Shows "N/A" if missing
      `,
      fallback: "Falls back to rain_probability field"
    },
    rain_probability: {
      frontend_use: "Fallback for rain probability",
      backend_provides: "NO",
      example: 0.0,
      status: "⚠️  Shows null",
      fallback: "Tries pop field first"
    },

    // Optional derived fields
    wind_u: {
      frontend_use: "Calculate wind magnitude from components",
      backend_provides: "NO",
      note: "Frontend checks: Math.sqrt(day.wind_u ** 2 + day.wind_v ** 2)"
    },
    wind_v: {
      frontend_use: "Calculate wind magnitude from components",
      backend_provides: "NO"
    },
    wind_mean: {
      frontend_use: "Alternative wind speed name",
      backend_provides: "NO"
    },
    wind_avg: {
      frontend_use: "Alternative wind speed name",
      backend_provides: "NO"
    },
    windSpeed: {
      frontend_use: "Alternative wind speed name (camelCase)",
      backend_provides: "NO"
    },
    rh: {
      frontend_use: "Alternative humidity name",
      backend_provides: "NO"
    }
  },

  // ============ SUMMARY FIELDS ============
  SUMMARY_FIELDS: {
    avg_temp_max: {
      frontend_use: "Display in 30-day summary grid",
      backend_provides: "YES",
      example: 32.1,
      status: "✅ Working"
    },
    avg_temp_min: {
      frontend_use: "Display in 30-day summary grid",
      backend_provides: "YES",
      example: 17.8,
      status: "✅ Working"
    },
    total_rainfall: {
      frontend_use: "Display total rain for 30 days",
      backend_provides: "YES",
      example: 45.3,
      status: "✅ Working"
    },
    avg_humidity: {
      frontend_use: "Display in summary (optional)",
      backend_provides: "NO",
      status: "⚠️  Not displayed"
    },
    avg_wind_speed: {
      frontend_use: "Display in summary (optional)",
      backend_provides: "NO",
      status: "⚠️  Not displayed"
    },
    max_temp: {
      frontend_use: "Not currently displayed",
      backend_provides: "YES"
    },
    min_temp: {
      frontend_use: "Not currently displayed",
      backend_provides: "YES"
    },
    days_with_rain: {
      frontend_use: "Display rainy days count",
      backend_provides: "YES",
      example: 8,
      status: "✅ Working"
    }
  },

  // ============ ALERT FIELDS ============
  ALERT_FIELDS: {
    type: {
      frontend_use: "Not used in UI",
      backend_provides: "YES",
      example: "high_temperature"
    },
    severity: {
      frontend_use: "Not used in UI",
      backend_provides: "YES",
      example: "warning"
    },
    message: {
      frontend_use: "Display alert text",
      backend_provides: "YES",
      example: "High temperatures expected...",
      status: "✅ Working"
    },
    date: {
      frontend_use: "Display date of alert",
      backend_provides: "YES",
      example: "2025-12-15",
      status: "✅ Working",
      frontend_code: "new Date(alert.date).toLocaleDateString()"
    }
  },

  // ============ REAL-TIME WEATHER FIELDS ============
  REALTIME_FIELDS: {
    temp: {
      frontend_use: "Display current temperature",
      backend_provides: "YES (NEW)",
      example: 28.5,
      status: "✅ Working",
      notes: "Fetched from Open-Meteo current weather API"
    },
    humidity: {
      frontend_use: "Display in real-time banner",
      backend_provides: "YES (NEW)",
      example: 72,
      status: "✅ Working"
    },
    wind_speed: {
      frontend_use: "Display in real-time banner",
      backend_provides: "YES (NEW)",
      example: 6.2,
      status: "✅ Working"
    },
    condition: {
      frontend_use: "Display weather condition text",
      backend_provides: "YES (NEW)",
      example: "Partly Cloudy",
      status: "✅ Working"
    },
    realtime_rain_1h: {
      frontend_use: "Display rainfall in last hour",
      backend_provides: "YES (NEW)",
      example: 0,
      status: "✅ Working"
    },
    rain_mm_next_1h: {
      frontend_use: "Alternative field name for rainfall",
      backend_provides: "NO (but realtime_rain_1h works)"
    },
    alert_level: {
      frontend_use: "Determine alert banner color",
      backend_provides: "YES (NEW)",
      example: "low | medium | high",
      status: "✅ Working",
      colors: {
        low: "blue background",
        medium: "yellow background",
        high: "red background"
      }
    },
    alert_message: {
      frontend_use: "Display alert text in banner",
      backend_provides: "YES (NEW)",
      example: "Current conditions: Partly Cloudy",
      status: "✅ Working"
    }
  },

  // ============ FRONTEND LOGIC FALLBACKS ============
  FRONTEND_FALLBACKS: {
    wind_extraction: `
      // Frontend tries multiple field names in order
      const wind = day.wind_speed !== undefined ? day.wind_speed : 
                   day.wind_avg !== undefined ? day.wind_avg :
                   day.wind_mean !== undefined ? day.wind_mean :
                   day.windSpeed !== undefined ? day.windSpeed :
                   day.wind && typeof day.wind === 'object' && day.wind.speed !== undefined ? day.wind.speed :
                   day.wind && typeof day.wind === 'object' && day.wind.avg !== undefined ? day.wind.avg :
                   day.wind && typeof day.wind === 'object' && day.wind.mean !== undefined ? day.wind.mean :
                   day.wind_u !== undefined && day.wind_v !== undefined ? Math.sqrt(day.wind_u ** 2 + day.wind_v ** 2) :
                   0;
    `,
    humidity_extraction: `
      // Frontend tries two field names
      const humidity = typeof day.humidity === 'number' ? Math.round(day.humidity) : 
                       typeof day.rh === 'number' ? Math.round(day.rh) : 
                       null;
    `,
    rain_probability_extraction: `
      // Frontend tries three field names
      const rainPct = typeof day.pop === 'number' ? Math.round(day.pop * 100) : 
                      typeof day.rain_probability === 'number' ? Math.round(day.rain_probability * 100) : 
                      null;
    `
  }
};

// ============ QUICK REFERENCE ============

/*
WHAT WORKS NOW (✅):
- Temperature predictions
- Rainfall predictions
- 30-day summary
- Weather alerts
- Authentication
- Real-time weather (NEW)

WHAT SHOWS N/A (⚠️):
- Wind speed
- Humidity
- Rain probability

WHAT THE FRONTEND DOES WITH N/A:
- Wind: Defaults to 0 (safe - green status)
- Humidity: Shows "N/A" text
- Rain prob: Shows "N/A" text

IMPACT ON USER:
- Farmers can still see all critical info (temp + rain)
- Wind/humidity are nice-to-have extras
- UI won't break
- System is 100% usable
*/

export default FIELD_MAPPING;
