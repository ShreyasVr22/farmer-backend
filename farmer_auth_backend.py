"""
Farmer Authentication Backend
Simple Phone Number + Password login
No complex security requirements - Farmer-friendly!
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer, DateTime, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import URL
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
from typing import Optional
from urllib.parse import quote_plus, urlparse

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./farmers.db")

print(f"[DB] Attempting to initialize database...")

# Build database engine with better error handling
engine = None

# Check if we're using PostgreSQL
if "postgresql" in DATABASE_URL.lower() or "postgres" in DATABASE_URL.lower():
    print("[DB] PostgreSQL URL detected, attempting connection...")
    try:
        # Try direct connection first
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        print("[DB] ✓ PostgreSQL connected")
    except ValueError as e:
        if "Port could not be cast to integer" in str(e) or "invalid literal for int()" in str(e):
            print(f"[DB] ⚠ PostgreSQL URL parsing failed: {str(e)[:100]}")
            print("[DB] Render may have provided an invalid DATABASE_URL")
            print("[DB] Falling back to SQLite for development/testing")
            engine = create_engine("sqlite:///./farmers.db", connect_args={"check_same_thread": False})
        else:
            raise
    except Exception as e:
        print(f"[DB] PostgreSQL connection error: {e}")
        print("[DB] Falling back to SQLite")
        engine = create_engine("sqlite:///./farmers.db", connect_args={"check_same_thread": False})
else:
    # Use SQLite
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    print("[DB] ✓ SQLite database ready")

if engine is None:
    raise RuntimeError("Failed to create database engine")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "farmer-assistant-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7  # 1 week


# ✅ DATABASE MODEL
class Farmer(Base):
    """
    Farmer user model - SIMPLE for Indian farmers
    No complex requirements!
    """
    __tablename__ = "farmers"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=True)  # Optional
    preferred_taluk = Column(String, nullable=True)
    preferred_hobli = Column(String, nullable=True)
    language = Column(String, default="en")  # en or kn
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    class Config:
        from_attributes = True


# Create tables
Base.metadata.create_all(bind=engine)


# ✅ PYDANTIC MODELS (API request/response)
class FarmerRegister(BaseModel):
    """Farmer registration request"""
    phone_number: str = Field(..., description="10-digit phone number")
    password: str = Field(..., description="Password (any characters, any length)")
    name: Optional[str] = Field(None, description="Farmer's name (optional)")
    language: Optional[str] = Field("en", description="Language preference: en or kn")


class FarmerLogin(BaseModel):
    """Farmer login request"""
    phone_number: str = Field(..., description="10-digit phone number")
    password: str = Field(..., description="Password")


class FarmerProfile(BaseModel):
    """Farmer profile response"""
    id: int
    phone_number: str
    name: Optional[str]
    preferred_taluk: Optional[str]
    preferred_hobli: Optional[str]
    language: str
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str
    farmer: FarmerProfile


class FarmerForgotPassword(BaseModel):
    """Forgot password request"""
    phone_number: str
    new_password: str


# ✅ DATABASE FUNCTIONS
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_phone_number(phone: str) -> bool:
    """Validate Indian phone number (10 digits)"""
    return len(phone) == 10 and phone.isdigit()


def hash_password(password: str) -> str:
    """
    Simple password hashing - NO special requirements for farmers!
    In production, use bcrypt: pip install bcrypt
    For now: just a simple transformation
    """
    # For production, use:
    # import bcrypt
    # return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # For MVP (simple):
    return f"hashed_{password}_farmer"  # Obviously not secure, but simple


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    # For production: return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    return hash_password(plain_password) == hashed_password


def create_access_token(phone_number: str, expires_hours: int = 24) -> str:
    """Create JWT token"""
    expire = datetime.utcnow() + timedelta(hours=expires_hours)
    to_encode = {
        "phone_number": phone_number,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return phone number"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("phone_number")
        if phone_number is None:
            return None
        return phone_number
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ✅ FASTAPI ENDPOINTS
from fastapi import APIRouter
router = APIRouter()


@router.post("/auth/register", response_model=TokenResponse)
async def register(farmer_data: FarmerRegister, db: Session = Depends(get_db)):
    """
    Register a new farmer
    
    Requirements:
    - Phone number: 10 digits (Indian mobile)
    - Password: Any characters, any length
    - Name: Optional
    - Language: en or kn
    """
    
    # Validate phone number
    if not validate_phone_number(farmer_data.phone_number):
        raise HTTPException(status_code=400, detail="Phone number must be 10 digits")
    
    # Check if phone number already exists
    existing_farmer = db.query(Farmer).filter(
        Farmer.phone_number == farmer_data.phone_number
    ).first()
    
    if existing_farmer:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Create new farmer
    new_farmer = Farmer(
        phone_number=farmer_data.phone_number,
        password=hash_password(farmer_data.password),
        name=farmer_data.name,
        language=farmer_data.language
    )
    
    db.add(new_farmer)
    db.commit()
    db.refresh(new_farmer)
    
    # Create token
    access_token = create_access_token(new_farmer.phone_number, expires_hours=24*7)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "farmer": FarmerProfile.from_orm(new_farmer)
    }


@router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: FarmerLogin, db: Session = Depends(get_db)):
    """
    Login farmer with phone + password
    
    Returns JWT token valid for 7 days
    """
    
    # Find farmer
    farmer = db.query(Farmer).filter(
        Farmer.phone_number == credentials.phone_number
    ).first()
    
    if not farmer:
        raise HTTPException(status_code=401, detail="Invalid phone number or password")
    
    # Verify password
    if not verify_password(credentials.password, farmer.password):
        raise HTTPException(status_code=401, detail="Invalid phone number or password")
    
    # Update last login
    farmer.last_login = datetime.utcnow()
    db.commit()
    
    # Create token
    access_token = create_access_token(farmer.phone_number, expires_hours=24*7)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "farmer": FarmerProfile.from_orm(farmer)
    }


@router.post("/auth/logout")
async def logout(token: str):
    """
    Logout - just delete token from frontend
    (Backend doesn't need to do anything)
    """
    return {"message": "Logged out successfully"}


@router.get("/profile")
async def get_profile(token: str, db: Session = Depends(get_db)):
    """
    Get farmer profile (requires authentication)
    
    Usage: GET /profile?token=YOUR_JWT_TOKEN
    """
    
    phone_number = verify_token(token)
    if not phone_number:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    farmer = db.query(Farmer).filter(
        Farmer.phone_number == phone_number
    ).first()
    
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    return FarmerProfile.from_orm(farmer)


@router.put("/profile/update")
async def update_profile(
    token: str,
    name: Optional[str] = None,
    preferred_taluk: Optional[str] = None,
    preferred_hobli: Optional[str] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update farmer profile
    
    Usage: PUT /profile/update?token=TOKEN&name=John&preferred_taluk=Devanahalli
    """
    
    phone_number = verify_token(token)
    if not phone_number:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    farmer = db.query(Farmer).filter(
        Farmer.phone_number == phone_number
    ).first()
    
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    # Update only provided fields
    if name is not None:
        farmer.name = name
    if preferred_taluk is not None:
        farmer.preferred_taluk = preferred_taluk
    if preferred_hobli is not None:
        farmer.preferred_hobli = preferred_hobli
    if language is not None:
        farmer.language = language
    
    db.commit()
    db.refresh(farmer)
    
    return {
        "message": "Profile updated successfully",
        "farmer": FarmerProfile.from_orm(farmer)
    }


@router.post("/auth/verify-token")
async def verify_token_endpoint(token: str):
    """
    Verify if token is valid
    
    Usage: POST /auth/verify-token?token=YOUR_JWT_TOKEN
    """
    
    phone_number = verify_token(token)
    if not phone_number:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "valid": True,
        "phone_number": phone_number,
        "message": "Token is valid"
    }


@router.post("/auth/forgot-password")
async def forgot_password(forgot_data: FarmerForgotPassword, db: Session = Depends(get_db)):
    """
    Reset password for a farmer using phone number
    
    Requirements:
    - Phone number: 10 digits (Indian mobile)
    - New password: Any characters, any length
    """
    
    # Validate phone number
    if not validate_phone_number(forgot_data.phone_number):
        raise HTTPException(status_code=400, detail="Phone number must be 10 digits")
    
    # Find farmer
    farmer = db.query(Farmer).filter(
        Farmer.phone_number == forgot_data.phone_number
    ).first()
    
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    # Update password
    farmer.password = hash_password(forgot_data.new_password)
    db.commit()
    db.refresh(farmer)
    
    return {
        "message": "Password reset successfully",
        "farmer": FarmerProfile.from_orm(farmer)
    }


# ✅ TEST ENDPOINTS
@router.get("/test/register-farmer")
async def test_register():
    """Test registration with dummy data"""
    return {
        "message": "Use POST /auth/register with this data:",
        "example": {
            "phone_number": "9876543210",
            "password": "any_password_123",
            "name": "Ramesh Kumar",
            "language": "kn"
        }
    }


@router.get("/test/login-farmer")
async def test_login():
    """Test login with dummy data"""
    return {
        "message": "Use POST /auth/login with this data:",
        "example": {
            "phone_number": "9876543210",
            "password": "any_password_123"
        }
    }


@router.post("/auth/forgot-password")
async def forgot_password(payload: FarmerForgotPassword, db: Session = Depends(get_db)):
    """
    Reset farmer password using phone number.

    Expects JSON: { "phone_number": "9876543210", "new_password": "newpass123" }
    """

    # Validate phone number format
    if not validate_phone_number(payload.phone_number):
        raise HTTPException(status_code=400, detail="Phone number must be 10 digits")

    farmer = db.query(Farmer).filter(Farmer.phone_number == payload.phone_number).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    # Update password (simple hash used in this project)
    farmer.password = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


# Create FastAPI app for standalone execution and include router
app = FastAPI()
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("[AUTH] Farmer Authentication Backend Starting")
    print("="*70)
    print("\nAvailable endpoints:")
    print("  POST /auth/register  - Register new farmer")
    print("  POST /auth/login     - Login farmer")
    print("  GET /profile         - Get farmer profile")
    print("  PUT /profile/update  - Update profile")
    print("="*70 + "\n")
    
    uvicorn.run(
        "farmer_auth_backend:app",
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
