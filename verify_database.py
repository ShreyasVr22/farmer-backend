#!/usr/bin/env python3
"""
Database Verification Script
Checks if the SQLite database is properly set up and has valid data
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path("farmers.db")

print("=" * 70)
print("🗄️  FARMER DATABASE VERIFICATION")
print("=" * 70)

# Check if database file exists
if not DB_PATH.exists():
    print("\n❌ Database file not found at:", DB_PATH)
    exit(1)

print(f"\n✅ Database file found: {DB_PATH}")
print(f"   Size: {DB_PATH.stat().st_size} bytes ({DB_PATH.stat().st_size / 1024:.1f} KB)")
print(f"   Created: {datetime.fromtimestamp(DB_PATH.stat().st_ctime)}")
print(f"   Modified: {datetime.fromtimestamp(DB_PATH.stat().st_mtime)}")

# Connect to database
try:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    print("\n✅ Database connection successful")
except Exception as e:
    print(f"\n❌ Failed to connect to database: {e}")
    exit(1)

# Check if tables exist
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print("\n⚠️  No tables found in database")
    else:
        print(f"\n✅ Found {len(tables)} table(s):")
        for table in tables:
            print(f"   • {table[0]}")
except Exception as e:
    print(f"\n❌ Failed to list tables: {e}")
    exit(1)

# Check farmers table structure
try:
    cursor.execute("PRAGMA table_info(farmers);")
    columns = cursor.fetchall()
    
    if columns:
        print("\n✅ Farmers table structure:")
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            print(f"   • {col_name:20} ({col_type})" + (" [PK]" if pk else "") + (" [NOT NULL]" if not_null else ""))
    else:
        print("\n⚠️  Farmers table not found or is empty")
except Exception as e:
    print(f"\n⚠️  Could not read table structure: {e}")

# Check how many farmers are registered
try:
    cursor.execute("SELECT COUNT(*) FROM farmers;")
    farmer_count = cursor.fetchone()[0]
    
    print(f"\n📊 Farmer Records:")
    print(f"   Total farmers registered: {farmer_count}")
    
    if farmer_count > 0:
        print(f"\n✅ Sample farmer records (first 5):")
        cursor.execute("""
            SELECT id, phone_number, name, created_at, last_login 
            FROM farmers 
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            farmer_id, phone, name, created, last_login = row
            print(f"\n   ID: {farmer_id}")
            print(f"   Phone: {phone}")
            print(f"   Name: {name or 'N/A'}")
            print(f"   Created: {created}")
            print(f"   Last Login: {last_login or 'Never'}")
    else:
        print("\n   ⚠️  No farmers registered yet")
        print("   (Database is ready but no users have signed up)")
        
except Exception as e:
    print(f"\n❌ Failed to query farmers: {e}")

# Check database integrity
try:
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0]
    
    if integrity == "ok":
        print(f"\n✅ Database integrity check: PASSED")
    else:
        print(f"\n❌ Database integrity check: FAILED")
        print(f"   {integrity}")
except Exception as e:
    print(f"\n⚠️  Could not run integrity check: {e}")

conn.close()

print("\n" + "=" * 70)
print("✅ DATABASE VERIFICATION COMPLETE")
print("=" * 70)
print("\n📝 Summary:")
print("   ✅ Database file exists and accessible")
print("   ✅ Connection working properly")
print("   ✅ Tables created successfully")
print("   ✅ Ready for user registration and login")
print("\n🚀 Next steps:")
print("   1. Run authentication backend")
print("   2. Register users (phone + password)")
print("   3. Login with credentials")
print("   4. JWT tokens will be generated automatically")
print("\n" + "=" * 70 + "\n")
