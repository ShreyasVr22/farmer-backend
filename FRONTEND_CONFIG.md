# Frontend Configuration

## For Development (Local Backend)

Replace the backend URL in your React code with:

```javascript
const API_BASE_URL = "http://localhost:8000";
```

### Common files to update in React:
- `src/config/api.js` or `src/api.js`
- Environment variables `.env` file
- Any service files that make API calls

### Example API calls:

```javascript
// Weather Forecast
const response = await fetch(`${API_BASE_URL}/predict/next-month`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    latitude: 13.2256,
    longitude: 77.5750,
    location: "huliyurdurga_nelamangala"
  })
});

// Real-time Weather
const realtime = await fetch(`${API_BASE_URL}/weather/realtime?lat=13.2256&lon=77.5750&location=huliyurdurga_nelamangala`);

// Health Check
const health = await fetch(`${API_BASE_URL}/health`);
```

## Backend Status

✓ Server running on: http://localhost:8000
✓ All 21 models loaded
✓ Ready for requests

## Current Error

Your React app is calling: `https://ai-farmer-assistant-backend.onrender.com` (old Render deployment)
Should call: `http://localhost:8000` (local backend)

This causes 404 errors since the routes don't match.
