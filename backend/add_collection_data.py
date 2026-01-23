"""
Add eligible donors for Collection demo
Creates donors with completed screening (eligibility_status: eligible) ready for blood collection
"""
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
import uuid
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
db_name = os.environ.get("DB_NAME", "bbms")

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
FIRST_NAMES = ["Arjun", "Neha", "Rohit", "Sneha", "Karan", "Divya", "Nikhil", "Pooja", "Sameer", "Ritu"]
LAST_NAMES = ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Verma", "Reddy", "Nair", "Das", "Mehta"]

async def add_eligible_donors_for_collection():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Fetching existing data...")
    
    # Get org_id from existing data
    org = await db.organizations.find_one({"org_code": "TEST001"}, {"_id": 0})
    if not org:
        print("ERROR: Test organization not found!")
        return
    
    org_id = org["id"]
    print(f"Organization ID: {org_id}")
    
    # Get existing users
    registration = await db.users.find_one({"email": "registration@testorg.com"}, {"_id": 0})
    admin = await db.users.find_one({"email": "admin@testorg.com"}, {"_id": 0})
    
    screener = registration if registration else admin
    
    # Get current counts
    donor_count = await db.donors.count_documents({"org_id": org_id})
    
    print(f"Current donor count: {donor_count}")
    
    new_donors = []
    new_screenings = []
    
    # ========================================
    # Create ELIGIBLE donors ready for collection
    # ========================================
    print("\n=== Creating Eligible Donors for COLLECTION ===")
    
    for i in range(6):
        donor_num = donor_count + i + 1
        
        donor_id = str(uuid.uuid4())
        screening_id = str(uuid.uuid4())
        
        blood_group = BLOOD_GROUPS[i % len(BLOOD_GROUPS)]
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Screening done today or yesterday
        screening_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))
        
        # Age between 18-55 for eligibility
        birth_year = random.randint(1970, 2005)
        
        # Create donor
        donor = {
            "id": donor_id,
            "org_id": org_id,
            "donor_code": f"DNR-2026-{donor_num:06d}",
            "donor_id": f"DNR-2026-{donor_num:06d}",  # Some code uses donor_id field
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "email": f"{first_name.lower()}.{last_name.lower()}{donor_num}@email.com",
            "phone": f"+91 98765{random.randint(10000, 99999)}",
            "blood_group": blood_group,
            "date_of_birth": f"{birth_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "gender": random.choice(["male", "female"]),
            "address": f"{random.randint(1, 500)}, {random.choice(['MG Road', 'Park Street', 'Ring Road', 'Main Street', 'Gandhi Nagar'])}, City",
            "city": random.choice(["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad"]),
            "state": random.choice(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana"]),
            "pincode": f"{random.randint(100000, 999999)}",
            "status": "active",
            "is_active": True,
            "total_donations": random.randint(0, 5),
            "last_donation_date": None,  # No recent donation - eligible
            "created_at": (screening_date - timedelta(days=random.randint(30, 365))).isoformat(),
            "updated_at": screening_date.isoformat()
        }
        new_donors.append(donor)
        
        # Create ELIGIBLE screening - passed all checks
        screening = {
            "id": screening_id,
            "org_id": org_id,
            "screening_number": f"SCR-2026-{donor_num:06d}",
            "donor_id": donor_id,
            "donor_name": f"{first_name} {last_name}",
            "blood_group": blood_group,
            "screening_date": screening_date.strftime("%Y-%m-%d"),
            "screening_time": screening_date.strftime("%H:%M:%S"),
            
            # Vital signs - all within normal range for eligibility
            "weight": round(random.uniform(55, 85), 1),  # Min 50kg required
            "height": round(random.uniform(155, 180), 1),
            "blood_pressure_systolic": random.randint(110, 130),  # Normal range
            "blood_pressure_diastolic": random.randint(70, 85),   # Normal range
            "pulse": random.randint(60, 80),  # Normal range
            "temperature": round(random.uniform(36.5, 37.2), 1),  # Normal
            "hemoglobin": round(random.uniform(13.0, 16.0), 1),  # Above 12.5 required
            
            # Blood group confirmation
            "preliminary_blood_group": blood_group,
            
            # Questionnaire and eligibility
            "questionnaire_passed": True,
            "eligibility_status": "eligible",  # KEY: Makes them appear in collection
            "rejection_reason": None,
            
            # Medical history - all clear
            "recent_illness": False,
            "recent_surgery": False,
            "recent_medication": False,
            "recent_tattoo": False,
            "recent_travel": False,
            "pregnancy_status": "not_applicable" if donor["gender"] == "male" else "no",
            
            # Screening staff
            "screened_by": screener["email"],
            "screener_name": screener["full_name"],
            "verified_by": admin["email"] if admin else None,
            "verifier_name": admin["full_name"] if admin else None,
            
            # Notes
            "remarks": "All parameters within normal limits. Cleared for donation.",
            "medical_notes": None,
            
            # Timestamps
            "created_at": screening_date.isoformat(),
            "updated_at": screening_date.isoformat()
        }
        new_screenings.append(screening)
        
        print(f"  Created donor {donor['donor_code']} ({blood_group}) - ELIGIBLE for collection")
    
    # ========================================
    # Insert all data
    # ========================================
    print("\n=== Inserting data into database ===")
    
    if new_donors:
        await db.donors.insert_many(new_donors)
        print(f"  Inserted {len(new_donors)} donors")
    
    if new_screenings:
        await db.screenings.insert_many(new_screenings)
        print(f"  Inserted {len(new_screenings)} screenings")
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "="*60)
    print("SUMMARY - ELIGIBLE DONORS FOR COLLECTION")
    print("="*60)
    
    eligible_count = await db.screenings.count_documents({
        "org_id": org_id, 
        "eligibility_status": "eligible"
    })
    
    print(f"\nCOLLECTION PAGE:")
    print(f"  {eligible_count} donors with eligible screening")
    print(f"  -> Go to Collection page")
    print(f"  -> Select a donor from 'Eligible Donors' tab")
    print(f"  -> Click 'Start Collection' to begin donation")
    print(f"  -> Fill collection details and complete")
    
    print("\nEligible Donors Created:")
    for donor in new_donors:
        print(f"  - {donor['donor_code']}: {donor['full_name']} ({donor['blood_group']})")
    
    print("\n" + "="*60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_eligible_donors_for_collection())
