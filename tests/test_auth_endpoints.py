import sys
from pathlib import Path

# Ensure project root is importable when running tests
sys.path.append(str(Path(__file__).resolve().parent.parent))

import sys
from pathlib import Path
import asyncio

# Ensure project root is importable when running tests
sys.path.append(str(Path(__file__).resolve().parent.parent))

from farmer_auth_backend import (
    SessionLocal,
    FarmerRegister,
    FarmerLogin,
    register,
    login,
)


def test_register_and_login():
    phone = "9997776665"

    async def run_sequence():
        db = SessionLocal()
        try:
            # Register
            reg = await register(FarmerRegister(phone_number=phone, password='pytest-pass', name='PyTest Farmer'), db=db)
            assert isinstance(reg, dict) or hasattr(reg, 'access_token')
            # Login
            ln = await login(FarmerLogin(phone_number=phone, password='pytest-pass'), db=db)
            assert isinstance(ln, dict) or hasattr(ln, 'access_token')
        finally:
            db.close()

    asyncio.run(run_sequence())
