import sys
from pathlib import Path

# Ensure project root is importable when running tests
sys.path.append(str(Path(__file__).resolve().parent.parent))

import sys
from pathlib import Path
import asyncio
import time

# Ensure project root is importable when running tests
sys.path.append(str(Path(__file__).resolve().parent.parent))

from farmer_auth_backend import (
    SessionLocal,
    FarmerRegister,
    FarmerLogin,
    register,
    login,
    Farmer,
)


def test_register_and_login():
    # Use timestamp to generate unique phone number for each test run
    timestamp = int(time.time() * 1000) % 10000000000  # Last 10 digits for phone
    phone = f"{timestamp:010d}"[:10]  # Ensure exactly 10 digits

    async def run_sequence():
        db = SessionLocal()
        try:
            # Clean up any existing farmer with this phone (shouldn't happen, but safe)
            existing = db.query(Farmer).filter(Farmer.phone_number == phone).first()
            if existing:
                db.delete(existing)
                db.commit()

            # Register
            reg = await register(FarmerRegister(phone_number=phone, password='pytest-pass', name='PyTest Farmer'), db=db)
            assert isinstance(reg, dict) or hasattr(reg, 'access_token')
            assert 'access_token' in reg
            assert reg['token_type'] == 'bearer'
            
            # Login
            ln = await login(FarmerLogin(phone_number=phone, password='pytest-pass'), db=db)
            assert isinstance(ln, dict) or hasattr(ln, 'access_token')
            assert 'access_token' in ln
            assert ln['token_type'] == 'bearer'
        finally:
            db.close()

    asyncio.run(run_sequence())
