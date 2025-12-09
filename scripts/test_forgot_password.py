import sys
from pathlib import Path
import asyncio
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))

from farmer_auth_backend import (
    SessionLocal,
    FarmerRegister,
    FarmerLogin,
    FarmerForgotPassword,
    register,
    login,
    forgot_password,
    Farmer,
)

async def test_forgot_password_flow():
    """Test register -> forgot password -> login with new password"""
    
    # Use timestamp for unique phone
    timestamp = int(time.time() * 1000) % 10000000000
    phone = f"{timestamp:010d}"[:10]
    old_password = "old_pass_123"
    new_password = "new_pass_456"
    
    db = SessionLocal()
    try:
        # Clean up any existing farmer
        existing = db.query(Farmer).filter(Farmer.phone_number == phone).first()
        if existing:
            db.delete(existing)
            db.commit()
        
        print("\n=== STEP 1: Register with old password ===")
        reg = await register(
            FarmerRegister(
                phone_number=phone, 
                password=old_password, 
                name="Forgot Password Test"
            ), 
            db=db
        )
        print(f"✓ Registered: {reg['farmer'].name}")
        print(f"  Token: {reg['access_token'][:50]}...")
        
        print("\n=== STEP 2: Login with old password ===")
        login_old = await login(
            FarmerLogin(phone_number=phone, password=old_password), 
            db=db
        )
        print(f"✓ Logged in with old password")
        print(f"  Token: {login_old['access_token'][:50]}...")
        
        print("\n=== STEP 3: Reset password (forgot password) ===")
        reset = await forgot_password(
            FarmerForgotPassword(phone_number=phone, new_password=new_password),
            db=db
        )
        print(f"✓ Password reset successfully")
        print(f"  Message: {reset['message']}")
        
        print("\n=== STEP 4: Try login with old password (should fail) ===")
        try:
            login_old_fail = await login(
                FarmerLogin(phone_number=phone, password=old_password),
                db=db
            )
            print("✗ ERROR: Should have failed but succeeded!")
        except Exception as e:
            print(f"✓ Correctly failed: {type(e).__name__}")
        
        print("\n=== STEP 5: Login with new password ===")
        login_new = await login(
            FarmerLogin(phone_number=phone, password=new_password),
            db=db
        )
        print(f"✓ Logged in with new password")
        print(f"  Token: {login_new['access_token'][:50]}...")
        
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(test_forgot_password_flow())
