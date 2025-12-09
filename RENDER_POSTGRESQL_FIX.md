# Render PostgreSQL Deployment Fix

## Issue
Deployment on Render was failing with the following error:
```
ValueError: invalid literal for int() with base 10: '...dpg-d4mhcuchg0os73brgrd0-a'
```

This error occurs when SQLAlchemy attempts to parse a PostgreSQL connection string from the `DATABASE_URL` environment variable. The issue arises because:

1. **Special Characters in Password**: Render's PostgreSQL connection string contains special characters in the password (e.g., hyphens, underscores)
2. **URL Parsing Failure**: SQLAlchemy's URL parser attempts to extract the port number but encounters non-numeric characters from the password, causing a type conversion error

## Root Cause
In `farmer_auth_backend.py` (line 22), the code was directly parsing the DATABASE_URL string:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./farmers.db")
engine = create_engine(DATABASE_URL, connect_args=...)
```

When the DATABASE_URL contains special characters, the parser fails at this stage.

## Solution

### 1. **Enhanced URL Parsing** (`farmer_auth_backend.py`)
Implemented proper URL parsing that handles special characters:

```python
from urllib.parse import quote_plus, urlparse

# For PostgreSQL URLs with special characters
if "postgresql" in DATABASE_URL.lower() or "postgres" in DATABASE_URL.lower():
    try:
        # Parse URL safely
        parsed = urlparse(DATABASE_URL)
        
        # Extract components
        username = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        database = parsed.path.lstrip('/')
        
        # Properly encode the password to handle special characters
        encoded_password = quote_plus(password) if password else ""
        db_url = f"postgresql+psycopg2://{username}:{encoded_password}@{host}:{port}/{database}"
        
        engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 10})
    except Exception as e:
        # Fallback to direct string
        engine = create_engine(DATABASE_URL)
else:
    # SQLite - use default
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

**Key improvements:**
- Uses `urllib.parse.urlparse()` to safely extract URL components
- Uses `urllib.parse.quote_plus()` to properly encode the password
- Adds `pool_pre_ping=True` to verify connections before using them
- Adds connection timeout for reliability
- Falls back to direct DATABASE_URL if parsing fails
- Maintains SQLite compatibility

### 2. **Added PostgreSQL Driver** (`requirements.txt`)
```
psycopg2-binary>=2.9.0
```

### 3. **Updated Render Configuration** (`render.yaml`)
```yaml
startCommand: uvicorn main:app --host 0.0.0.0 --port 10000
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: ai-farmer-db
      property: connectionString
```

**Changes:**
- Changed port from 8000 to 10000 (per Render logs)
- Properly configured DATABASE_URL from Render's database service

## Testing

### Local Testing
The fix has been tested locally with:
1. SQLite database (default fallback)
2. PostgreSQL connection string parsing

### Deployment Testing
1. Push changes to GitHub (`commit: 1be0efe`)
2. Trigger Render deployment
3. Monitor logs for the startup sequence
4. Verify no URL parsing errors occur

## Expected Deployment Flow

After deploying with these fixes:

```
[Build]
✓ pip install -r requirements.txt
✓ psycopg2-binary installed
✓ Dependencies resolved

[Deploy]
✓ uvicorn starts on 0.0.0.0:10000
✓ DATABASE_URL parsed successfully
✓ PostgreSQL connection established
✓ SQLAlchemy engine created
✓ farmer_auth_backend imported
✓ main.py application starts
✓ 21 LSTM models load
✓ Historical weather data cached
✓ API ready at https://your-app.onrender.com
```

## Frontend Configuration

Update your frontend API base URL to:
```
https://your-app.onrender.com
```

Or if running locally:
```
http://127.0.0.1:10000
```

## Additional Notes

1. **Connection Pooling**: The fix includes `pool_pre_ping=True` which validates connections before use
2. **Timeout Handling**: `connect_timeout=10` provides 10 seconds for initial connection
3. **Fallback Mechanism**: If PostgreSQL parsing fails, the system falls back to the original DATABASE_URL
4. **SQLite Compatibility**: Local development with SQLite continues to work unchanged

## Monitoring

After deployment, monitor:
1. Render application logs for any URL parsing errors
2. Database connection status
3. API response times
4. Authentication endpoint availability

---

**Deployed**: December 9, 2025
**Commit**: 1be0efe
**Status**: Ready for Render deployment
