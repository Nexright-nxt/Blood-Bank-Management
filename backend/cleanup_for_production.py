"""
Clean up demo data for production deployment
Keeps: users, organizations, system_settings, form_configurations
Removes: all demo/test data
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
import uuid
import bcrypt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "bbms")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def cleanup_for_production():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("="*60)
    print("CLEANING UP DEMO DATA FOR PRODUCTION")
    print("="*60)
    
    # Collections to completely clear (demo data)
    collections_to_clear = [
        "donors",
        "donations", 
        "screenings",
        "blood_units",
        "lab_tests",
        "components",
        "qc_validation",
        "blood_requests",
        "issuances",
        "shipments",
        "logistics",
        "returns",
        "discards",
        "quarantine",
        "pre_lab_qc",
        "chain_custody",
        "donor_requests",
        "audit_logs",
        "notifications",
        "action_verifications",
        "sensitive_action_logs",
        "user_sessions",
    ]
    
    print("\n1. Clearing demo data collections...")
    for coll in collections_to_clear:
        count = await db[coll].count_documents({})
        if count > 0:
            await db[coll].delete_many({})
            print(f"   Cleared {coll}: {count} documents removed")
    
    # Keep but clean up certain collections
    print("\n2. Cleaning up configuration collections...")
    
    # Remove test vehicles and couriers (keep structure)
    await db.vehicles.delete_many({})
    print("   Cleared vehicles")
    await db.couriers.delete_many({})
    print("   Cleared couriers")
    
    # Keep storage locations but verify they're clean
    storage_count = await db.storage_locations.count_documents({})
    print(f"   Storage locations: {storage_count} (kept)")
    
    # Keep organizations
    org_count = await db.organizations.count_documents({})
    print(f"   Organizations: {org_count} (kept)")
    
    # Keep users
    user_count = await db.users.count_documents({})
    print(f"   Users: {user_count} (kept)")
    
    # Keep form configurations
    form_count = await db.form_configurations.count_documents({})
    print(f"   Form configurations: {form_count} (kept)")
    
    # Keep system settings
    settings_count = await db.system_settings.count_documents({})
    print(f"   System settings: {settings_count} (kept)")
    
    # Clean up MFA data for fresh start
    await db.user_mfa.delete_many({})
    print("   Cleared MFA data")
    
    print("\n3. Verifying essential data exists...")
    
    # Ensure system admin exists
    system_admin = await db.users.find_one({"user_type": "system_admin"})
    if not system_admin:
        print("   Creating system admin...")
        admin = {
            "id": str(uuid.uuid4()),
            "email": "admin@bloodlink.local",
            "password_hash": hash_password("Admin@123456"),
            "full_name": "System Administrator",
            "role": "admin",
            "user_type": "system_admin",
            "org_id": None,
            "is_active": True,
            "phone": "",
            "department": "IT Administration",
            "permissions": ["*"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin)
        print(f"   Created system admin: admin@bloodlink.local")
    else:
        print(f"   System admin exists: {system_admin['email']}")
    
    # Ensure at least one organization exists
    org = await db.organizations.find_one({})
    if not org:
        print("   Creating default organization...")
        org_doc = {
            "id": str(uuid.uuid4()),
            "name": "Blood Link Central",
            "org_code": "BLC001",
            "type": "blood_bank",
            "address": "123 Healthcare Avenue",
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
            "phone": "+91 22 1234 5678",
            "email": "contact@bloodlink.local",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.organizations.insert_one(org_doc)
        print(f"   Created organization: {org_doc['name']}")
    else:
        print(f"   Organization exists: {org.get('name', 'N/A')}")
    
    # Final count
    print("\n" + "="*60)
    print("CLEANUP COMPLETE - FINAL STATE")
    print("="*60)
    
    collections = await db.list_collection_names()
    total_docs = 0
    for coll in sorted(collections):
        count = await db[coll].count_documents({})
        if count > 0:
            print(f"   {coll:<30} {count:>6}")
            total_docs += count
    
    print(f"\n   Total documents: {total_docs}")
    print("="*60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_for_production())
