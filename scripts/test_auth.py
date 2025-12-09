import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from farmer_auth_backend import (
    SessionLocal,
    FarmerRegister,
    FarmerLogin,
    register,
    login,
)

import asyncio


async def run_async():
    db = SessionLocal()
    try:
        print('\n=== DIRECT REGISTER (function call) ===')
        reg_resp = await register(FarmerRegister(phone_number='9998887776', password='testpass', name='Test Farmer'), db=db)
        print('register response:')
        print(reg_resp)

        print('\n=== DIRECT LOGIN (function call) ===')
        login_resp = await login(FarmerLogin(phone_number='9998887776', password='testpass'), db=db)
        print('login response:')
        print(login_resp)
    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(run_async())
