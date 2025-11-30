🚀 RENDER DEPLOYMENT - ENVIRONMENT VARIABLES GUIDE

For your Farmer Assistant backend deployment on Render


═══════════════════════════════════════════════════════════════════════════════
                        ENVIRONMENT VARIABLES TO ADD
═══════════════════════════════════════════════════════════════════════════════

Your backend uses these environment variables. Add them in Render's dashboard:


1️⃣ DATABASE CONFIGURATION
──────────────────────────────────────────────────────────────────────────────

Variable Name: DATABASE_URL
Type: String (Secret)
Description: Database connection string for user authentication

Options:
  
  A) PostgreSQL (Recommended for production):
     DATABASE_URL = postgresql://username:password@host:5432/database_name
     
     Get from: Render PostgreSQL service or external provider
     
  B) SQLite (For MVP):
     DATABASE_URL = sqlite:///./farmers.db
     
     Default - no setup needed


2️⃣ AUTHENTICATION/JWT
──────────────────────────────────────────────────────────────────────────────

Variable Name: SECRET_KEY
Type: String (Secret) ⚠️ CRITICAL - KEEP PRIVATE
Description: JWT token signing secret

Default: "farmer-assistant-secret-key-change-in-production"

🔐 IMPORTANT: Generate a strong random secret for production:

Linux/Mac:
  python -c "import secrets; print(secrets.token_urlsafe(32))"

Windows PowerShell:
  [Convert]::ToBase64String([byte[]]$(1..32 | ForEach-Object {Get-Random -Max 256}))

Example secure value:
  "xK7pQmN9_dF2jH4vB8zR3wT5yL1sC6oP0"


3️⃣ PYTHON VERSION (Optional - already set)
──────────────────────────────────────────────────────────────────────────────

Variable Name: PYTHON_VERSION
Value: 3.11.7
(Already in render.yaml)


4️⃣ RENDER DEPLOYMENT SETUP (render.yaml)
──────────────────────────────────────────────────────────────────────────────

Your render.yaml already includes:
  • Service: ai-back (web service)
  • Environment: Python
  • Plan: Free tier
  • Python Version: 3.11.7
  • Start Command: gunicorn with uvicorn


═══════════════════════════════════════════════════════════════════════════════
                        STEP-BY-STEP RENDER SETUP
═══════════════════════════════════════════════════════════════════════════════

1. Go to https://render.com and login/signup

2. Create New → Web Service

3. Connect your GitHub repository:
   - Select your repo (whether-backend)
   - Branch: main

4. Configure Service:
   Name: ai-back (or your choice)
   Environment: Python 3.11
   Plan: Free
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 main:app

5. Add Environment Variables (CRITICAL STEP):
   
   Click "Advanced" → "Add from .env"
   OR manually add:
   
   ┌─────────────────────────────────────────────────────────┐
   │ KEY: DATABASE_URL                                       │
   │ VALUE: sqlite:///./farmers.db (for MVP)               │
   │ or postgresql://... (for production)                   │
   │ TYPE: Secret                                           │
   └─────────────────────────────────────────────────────────┘
   
   ┌─────────────────────────────────────────────────────────┐
   │ KEY: SECRET_KEY                                         │
   │ VALUE: xK7pQmN9_dF2jH4vB8zR3wT5yL1sC6oP0               │
   │ TYPE: Secret                                           │
   └─────────────────────────────────────────────────────────┘

6. Deploy!


═══════════════════════════════════════════════════════════════════════════════
                        YOUR ENVIRONMENT VARIABLES
═══════════════════════════════════════════════════════════════════════════════

Suggested values for MVP deployment:

DATABASE_URL = sqlite:///./farmers.db
SECRET_KEY = farmer-assistant-secret-key-change-in-production

⚠️ For production, use:

DATABASE_URL = postgresql://user:password@host/dbname
SECRET_KEY = [generate strong random string]


═══════════════════════════════════════════════════════════════════════════════
                    WHERE TO FIND THESE IN YOUR CODE
═══════════════════════════════════════════════════════════════════════════════

farmer_auth_backend.py (lines 17-23):
  
  load_dotenv()
  
  DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./farmers.db")
  SECRET_KEY = os.getenv("SECRET_KEY", "farmer-assistant-secret-key-change-in-production")

The os.getenv() function reads from Render environment variables.


═══════════════════════════════════════════════════════════════════════════════
                        ADDITIONAL RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════════

✅ DO:
  • Use PostgreSQL in production (not SQLite)
  • Generate a strong SECRET_KEY (32+ characters)
  • Mark DATABASE_URL and SECRET_KEY as "Secret" in Render
  • Keep backups of your SECRET_KEY
  • Monitor logs in Render dashboard

❌ DON'T:
  • Commit .env file to Git
  • Use default/weak SECRET_KEY in production
  • Share SECRET_KEY publicly
  • Use free SQLite on production (data loss risk)


═══════════════════════════════════════════════════════════════════════════════
                        FOR REAL-TIME WEATHER API
═══════════════════════════════════════════════════════════════════════════════

Good news! The /weather/realtime endpoint uses Open-Meteo API which:
  ✅ Doesn't require API key
  ✅ Free tier available
  ✅ No authentication needed
  ✅ Already implemented in your code

So you DON'T need to add any API keys for real-time weather!


═══════════════════════════════════════════════════════════════════════════════
                        QUICK REFERENCE
═══════════════════════════════════════════════════════════════════════════════

Render Environment Variable Names:

┌────────────────────┬──────────────────┬───────────────┬────────────────────┐
│ Variable Name      │ Purpose          │ Required      │ Example            │
├────────────────────┼──────────────────┼───────────────┼────────────────────┤
│ DATABASE_URL       │ User DB          │ Yes           │ sqlite:///farmers.db
│ SECRET_KEY         │ JWT Signing      │ Yes           │ [random string]    │
│ PYTHON_VERSION     │ Runtime          │ No (default)  │ 3.11.7             │
└────────────────────┴──────────────────┴───────────────┴────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                        EXAMPLE: Complete Setup
═══════════════════════════════════════════════════════════════════════════════

In Render Dashboard → Environment section:

1. Add Variable:
   KEY: DATABASE_URL
   VALUE: sqlite:///./farmers.db
   TYPE: Secret ✓

2. Add Variable:
   KEY: SECRET_KEY
   VALUE: xK7pQmN9_dF2jH4vB8zR3wT5yL1sC6oP0
   TYPE: Secret ✓

3. Click "Save Changes"

4. Render automatically deploys!


═══════════════════════════════════════════════════════════════════════════════

Ready to deploy? Follow the steps above and your backend will be live!

Generated: December 1, 2025
For: Farmer Assistant Weather Prediction System
