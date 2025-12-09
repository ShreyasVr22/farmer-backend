import sys
from pathlib import Path
import asyncio
import time

# ensure project root on path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from farmer_auth_backend import (
    SessionLocal,
    FarmerRegister,
    FarmerLogin,
    FarmerForgotPassword,
    register,
    login,
    forgot_password,
)

async def run_flow():
    db = SessionLocal()
    try:
        # unique phone
        phone = f"9{int(time.time()*1000)%1000000000:09d}"[:10]
        print('Using phone:', phone)

        # Register
        reg = await register(FarmerRegister(phone_number=phone, password='orig-pass', name='Forgot Test'), db=db)
        print('register:', 'access_token' in reg)

        # Attempt login with original password
        ln = await login(FarmerLogin(phone_number=phone, password='orig-pass'), db=db)
        print('login with orig-pass:', 'access_token' in ln)

        # Reset password
        resp = await forgot_password(FarmerForgotPassword(phone_number=phone, new_password='new-pass-123'), db=db)
        print('forgot resp:', resp)

        # Login with new password
        ln2 = await login(FarmerLogin(phone_number=phone, password='new-pass-123'), db=db)
        print('login with new-pass:', 'access_token' in ln2)

    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(run_flow())
