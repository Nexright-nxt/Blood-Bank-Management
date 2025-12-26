"""
Seed script to populate Blood Bank Management System with dummy data
Run: python seed_data.py
"""
import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import bcrypt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Sample data
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
GENDERS = ["Male", "Female"]
IDENTITY_TYPES = ["Aadhar", "Passport", "Driving License", "Voter ID", "PAN Card"]

FIRST_NAMES = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Rajesh", "Meera", 
               "Suresh", "Kavita", "Arjun", "Pooja", "Nikhil", "Deepa", "Sanjay", "Nisha",
               "Arun", "Lakshmi", "Kiran", "Sunita", "Ravi", "Anita", "Mohit", "Geeta"]
LAST_NAMES = ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Reddy", "Nair", "Verma",
              "Joshi", "Menon", "Pillai", "Iyer", "Rao", "Das", "Chatterjee", "Banerjee"]

CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad"]
HOSPITALS = ["City Hospital", "Apollo Hospital", "Fortis Hospital", "Max Hospital", 
             "AIIMS", "Medanta", "Lilavati Hospital", "Breach Candy Hospital"]

async def clear_collections():
    """Clear existing data"""
    collections = ['donors', 'donor_requests', 'donations', 'screenings', 'blood_units',
                   'lab_tests', 'components', 'chain_custody', 'quarantine', 'qc_validation',
                   'blood_requests', 'issuances', 'returns', 'discards', 'donor_otps']
    for coll in collections:
        await db[coll].delete_many({})
    print("✓ Cleared existing data")

async def seed_staff_users():
    """Create staff users with different roles"""
    users = [
        {"email": "registration@bloodbank.com", "full_name": "Anita Desai", "role": "registration"},
        {"email": "phlebotomist@bloodbank.com", "full_name": "Dr. Suresh Menon", "role": "phlebotomist"},
        {"email": "labtech@bloodbank.com", "full_name": "Priya Nair", "role": "lab_tech"},
        {"email": "processing@bloodbank.com", "full_name": "Rajesh Iyer", "role": "processing"},
        {"email": "qcmanager@bloodbank.com", "full_name": "Dr. Kavita Sharma", "role": "qc_manager"},
        {"email": "inventory@bloodbank.com", "full_name": "Mohit Gupta", "role": "inventory"},
        {"email": "distribution@bloodbank.com", "full_name": "Arun Verma", "role": "distribution"},
    ]
    
    for user in users:
        existing = await db.users.find_one({"email": user["email"]})
        if not existing:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": user["email"],
                "password_hash": hash_password("password123"),
                "full_name": user["full_name"],
                "role": user["role"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
    print(f"✓ Created {len(users)} staff users")

async def seed_donors():
    """Create 30 donors with varied data"""
    donors = []
    
    for i in range(30):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        gender = random.choice(GENDERS)
        blood_group = random.choice(BLOOD_GROUPS)
        city = random.choice(CITIES)
        
        # Random DOB between 18-55 years ago
        age = random.randint(18, 55)
        dob = (datetime.now() - timedelta(days=age*365 + random.randint(0, 365))).strftime("%Y-%m-%d")
        
        # Random registration date in past 2 years
        reg_days_ago = random.randint(1, 730)
        reg_date = datetime.now(timezone.utc) - timedelta(days=reg_days_ago)
        
        # Some donors have donated, some haven't
        total_donations = random.choice([0, 0, 1, 1, 2, 2, 3, 4, 5])
        last_donation = None
        if total_donations > 0:
            last_donation_days = random.randint(60, 365)
            last_donation = (datetime.now(timezone.utc) - timedelta(days=last_donation_days)).isoformat()
        
        # Some donors are deferred
        status = "active"
        deferral_reason = None
        deferral_end = None
        if random.random() < 0.1:  # 10% deferred
            status = random.choice(["deferred_temporary", "deferred_permanent"])
            deferral_reason = random.choice(["Low hemoglobin", "Recent surgery", "Medication", "Travel history"])
            if status == "deferred_temporary":
                deferral_end = (datetime.now(timezone.utc) + timedelta(days=random.randint(30, 180))).isoformat()
        
        donor = {
            "id": str(uuid.uuid4()),
            "donor_id": f"D-2025-{str(i+1).zfill(4)}",
            "full_name": f"{first_name} {last_name}",
            "date_of_birth": dob,
            "gender": gender,
            "blood_group": blood_group,
            "phone": f"98{random.randint(10000000, 99999999)}",
            "email": f"{first_name.lower()}.{last_name.lower()}@email.com",
            "address": f"{random.randint(1, 500)}, {random.choice(['MG Road', 'Park Street', 'Ring Road', 'Main Street'])}, {city}",
            "identity_type": random.choice(IDENTITY_TYPES),
            "identity_number": str(random.randint(100000000000, 999999999999)),
            "status": status,
            "deferral_reason": deferral_reason,
            "deferral_end_date": deferral_end,
            "consent_given": True,
            "registration_channel": random.choice(["on_site", "online", "camp"]),
            "qr_code": "",  # Would be generated
            "total_donations": total_donations,
            "last_donation_date": last_donation,
            "created_at": reg_date.isoformat(),
            "created_by": None,
            "updated_at": reg_date.isoformat(),
            "updated_by": None
        }
        donors.append(donor)
    
    await db.donors.insert_many(donors)
    print(f"✓ Created {len(donors)} donors")
    return donors

async def seed_donor_requests():
    """Create pending, approved, and rejected donor requests"""
    requests = []
    statuses = ["pending", "pending", "pending", "approved", "approved", "rejected"]
    
    for i in range(12):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        status = statuses[i % len(statuses)]
        
        req = {
            "id": str(uuid.uuid4()),
            "request_id": f"REG-2025-{str(i+100).zfill(5)}",
            "donor_id": None,
            "identity_type": random.choice(IDENTITY_TYPES),
            "identity_number": str(random.randint(100000000000, 999999999999)),
            "full_name": f"{first_name} {last_name}",
            "date_of_birth": (datetime.now() - timedelta(days=random.randint(18, 50)*365)).strftime("%Y-%m-%d"),
            "gender": random.choice(GENDERS),
            "weight": random.randint(50, 90),
            "phone": f"98{random.randint(10000000, 99999999)}",
            "email": f"{first_name.lower()}{random.randint(1,99)}@email.com",
            "address": f"{random.randint(1, 500)}, {random.choice(CITIES)}",
            "consent_given": True,
            "request_type": "new_registration",
            "status": status,
            "reviewed_by": None if status == "pending" else str(uuid.uuid4()),
            "reviewed_at": None if status == "pending" else datetime.now(timezone.utc).isoformat(),
            "rejection_reason": "Incomplete documentation" if status == "rejected" else None,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).isoformat()
        }
        requests.append(req)
    
    await db.donor_requests.insert_many(requests)
    print(f"✓ Created {len(requests)} donor requests")

async def seed_donations_and_units(donors):
    """Create donations, screenings, and blood units"""
    donations = []
    screenings = []
    blood_units = []
    
    # Select donors who have donated
    donating_donors = [d for d in donors if d["total_donations"] > 0]
    
    for donor in donating_donors:
        for don_num in range(donor["total_donations"]):
            donation_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365))
            
            # Create screening
            screening = {
                "id": str(uuid.uuid4()),
                "donor_id": donor["id"],
                "screening_date": donation_date.strftime("%Y-%m-%d"),
                "weight": random.randint(50, 90),
                "height": random.randint(150, 190),
                "blood_pressure_systolic": random.randint(110, 140),
                "blood_pressure_diastolic": random.randint(70, 90),
                "pulse": random.randint(60, 90),
                "temperature": round(random.uniform(36.2, 37.2), 1),
                "hemoglobin": round(random.uniform(12.5, 16.0), 1),
                "preliminary_blood_group": donor["blood_group"],
                "questionnaire_passed": True,
                "eligibility_status": "eligible",
                "rejection_reason": None,
                "screened_by": None,
                "created_at": donation_date.isoformat()
            }
            screenings.append(screening)
            
            # Create donation
            donation = {
                "id": str(uuid.uuid4()),
                "donation_id": f"DON-2025-{str(len(donations)+1).zfill(5)}",
                "donor_id": donor["id"],
                "screening_id": screening["id"],
                "donation_type": random.choice(["whole_blood", "whole_blood", "whole_blood", "apheresis"]),
                "collection_start_time": donation_date.isoformat(),
                "collection_end_time": (donation_date + timedelta(minutes=random.randint(8, 15))).isoformat(),
                "volume_collected": random.choice([350, 400, 450, 450, 450]),
                "adverse_reaction": random.random() < 0.05,
                "adverse_reaction_details": "Mild dizziness" if random.random() < 0.05 else None,
                "phlebotomist_id": None,
                "status": "completed",
                "created_at": donation_date.isoformat()
            }
            donations.append(donation)
            
            # Create blood unit
            expiry_date = donation_date + timedelta(days=42)  # Whole blood expires in 42 days
            statuses = ["ready_to_use", "ready_to_use", "ready_to_use", "processing", "lab", "issued", "quarantine"]
            unit_status = random.choice(statuses)
            
            blood_unit = {
                "id": str(uuid.uuid4()),
                "unit_id": f"BU-2025-{str(len(blood_units)+1).zfill(6)}",
                "donor_id": donor["id"],
                "donation_id": donation["id"],
                "bag_barcode": "",
                "sample_labels": [f"BU-2025-{str(len(blood_units)+1).zfill(6)}-S1", f"BU-2025-{str(len(blood_units)+1).zfill(6)}-S2"],
                "blood_group": donor["blood_group"],
                "confirmed_blood_group": donor["blood_group"],
                "blood_group_verified_by": [str(uuid.uuid4()), str(uuid.uuid4())],
                "status": unit_status,
                "current_location": random.choice(["storage", "lab", "processing"]),
                "storage_location": f"Rack-{random.choice(['A', 'B', 'C', 'D'])}-{random.randint(1,10)}",
                "collection_date": donation_date.strftime("%Y-%m-%d"),
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "volume": donation["volume_collected"],
                "created_at": donation_date.isoformat(),
                "created_by": None,
                "updated_at": donation_date.isoformat()
            }
            blood_units.append(blood_unit)
    
    if screenings:
        await db.screenings.insert_many(screenings)
    if donations:
        await db.donations.insert_many(donations)
    if blood_units:
        await db.blood_units.insert_many(blood_units)
    
    print(f"✓ Created {len(screenings)} screenings")
    print(f"✓ Created {len(donations)} donations")
    print(f"✓ Created {len(blood_units)} blood units")
    return blood_units

async def seed_lab_tests(blood_units):
    """Create lab test records"""
    lab_tests = []
    
    for unit in blood_units:
        if unit["status"] not in ["collected"]:
            test = {
                "id": str(uuid.uuid4()),
                "unit_id": unit["id"],
                "confirmed_blood_group": unit["blood_group"],
                "verified_by_1": str(uuid.uuid4()),
                "verified_by_2": str(uuid.uuid4()),
                "hiv_result": "non_reactive",
                "hbsag_result": "non_reactive",
                "hcv_result": "non_reactive",
                "syphilis_result": "non_reactive",
                "test_method": "ELISA",
                "overall_status": "non_reactive" if unit["status"] != "quarantine" else "gray",
                "tested_by": None,
                "test_date": unit["collection_date"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            lab_tests.append(test)
    
    if lab_tests:
        await db.lab_tests.insert_many(lab_tests)
    print(f"✓ Created {len(lab_tests)} lab tests")

async def seed_components(blood_units):
    """Create blood components from units"""
    components = []
    component_types = ["prc", "plasma", "ffp", "platelets"]
    
    for unit in blood_units:
        if unit["status"] in ["ready_to_use", "issued", "processing"]:
            # Each unit can produce multiple components
            num_components = random.randint(1, 3)
            for _ in range(num_components):
                comp_type = random.choice(component_types)
                
                # Set expiry based on component type
                collection_date = datetime.strptime(unit["collection_date"], "%Y-%m-%d")
                if comp_type == "prc":
                    expiry = collection_date + timedelta(days=42)
                elif comp_type in ["plasma", "ffp"]:
                    expiry = collection_date + timedelta(days=365)
                elif comp_type == "platelets":
                    expiry = collection_date + timedelta(days=5)
                else:
                    expiry = collection_date + timedelta(days=365)
                
                component = {
                    "id": str(uuid.uuid4()),
                    "component_id": f"COMP-2025-{str(len(components)+1).zfill(6)}",
                    "parent_unit_id": unit["id"],
                    "component_type": comp_type,
                    "volume": random.randint(150, 300),
                    "blood_group": unit["blood_group"],
                    "status": random.choice(["ready_to_use", "ready_to_use", "processing", "reserved"]),
                    "storage_temp_min": -30 if comp_type in ["plasma", "ffp"] else 2,
                    "storage_temp_max": -25 if comp_type in ["plasma", "ffp"] else 6,
                    "storage_location": f"Freezer-{random.choice(['A', 'B'])}" if comp_type in ["plasma", "ffp"] else f"Fridge-{random.randint(1,3)}",
                    "batch_id": f"BATCH-{random.randint(100, 999)}",
                    "expiry_date": expiry.strftime("%Y-%m-%d"),
                    "qc_values": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "processed_by": None
                }
                components.append(component)
    
    if components:
        await db.components.insert_many(components)
    print(f"✓ Created {len(components)} components")
    return components

async def seed_blood_requests(components):
    """Create blood requests"""
    requests = []
    
    for i in range(15):
        request_date = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
        status = random.choice(["pending", "pending", "approved", "approved", "fulfilled", "rejected"])
        
        request = {
            "id": str(uuid.uuid4()),
            "request_id": f"REQ-2025-{str(i+1).zfill(5)}",
            "request_type": random.choice(["internal", "external"]),
            "requester_name": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "requester_contact": f"98{random.randint(10000000, 99999999)}",
            "hospital_name": random.choice(HOSPITALS),
            "patient_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "patient_id": f"PAT-{random.randint(10000, 99999)}",
            "blood_group": random.choice(BLOOD_GROUPS),
            "product_type": random.choice(["whole_blood", "prc", "plasma", "ffp", "platelets"]),
            "quantity": random.randint(1, 4),
            "urgency": random.choice(["normal", "normal", "urgent", "emergency"]),
            "status": status,
            "requested_date": request_date.strftime("%Y-%m-%d"),
            "required_by_date": (request_date + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d"),
            "approved_by": str(uuid.uuid4()) if status in ["approved", "fulfilled"] else None,
            "approval_date": request_date.strftime("%Y-%m-%d") if status in ["approved", "fulfilled"] else None,
            "notes": random.choice([None, "Urgent surgery", "Trauma case", "Scheduled operation"]),
            "created_at": request_date.isoformat()
        }
        requests.append(request)
    
    if requests:
        await db.blood_requests.insert_many(requests)
    print(f"✓ Created {len(requests)} blood requests")

async def seed_qc_validations(blood_units, components):
    """Create QC validation records"""
    validations = []
    
    # QC for some blood units
    for unit in blood_units[:10]:
        validation = {
            "id": str(uuid.uuid4()),
            "unit_component_id": unit["id"],
            "unit_type": "unit",
            "data_complete": random.choice([True, True, True, False]),
            "screening_complete": random.choice([True, True, True, False]),
            "custody_complete": random.choice([True, True, True, False]),
            "status": random.choice(["pending", "approved", "approved", "hold"]),
            "hold_reason": None,
            "approved_by": str(uuid.uuid4()) if random.random() > 0.3 else None,
            "approval_timestamp": datetime.now(timezone.utc).isoformat() if random.random() > 0.3 else None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        validations.append(validation)
    
    # QC for some components
    for comp in components[:15]:
        validation = {
            "id": str(uuid.uuid4()),
            "unit_component_id": comp["id"],
            "unit_type": "component",
            "data_complete": True,
            "screening_complete": True,
            "custody_complete": random.choice([True, True, False]),
            "status": random.choice(["pending", "approved", "approved"]),
            "hold_reason": None,
            "approved_by": str(uuid.uuid4()) if random.random() > 0.3 else None,
            "approval_timestamp": datetime.now(timezone.utc).isoformat() if random.random() > 0.3 else None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        validations.append(validation)
    
    if validations:
        await db.qc_validation.insert_many(validations)
    print(f"✓ Created {len(validations)} QC validations")

async def seed_returns_and_discards(components):
    """Create return and discard records"""
    returns = []
    discards = []
    
    # Create some returns
    for i in range(5):
        ret = {
            "id": str(uuid.uuid4()),
            "return_id": f"RET-2025-{str(i+1).zfill(5)}",
            "component_id": components[i]["id"] if i < len(components) else str(uuid.uuid4()),
            "return_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
            "source": random.choice(HOSPITALS),
            "reason": random.choice(["Not used", "Surgery cancelled", "Patient discharged", "Wrong blood type requested"]),
            "qc_pass": random.choice([True, True, False]),
            "decision": random.choice(["accept", "accept", "reject", None]),
            "processed_by": str(uuid.uuid4()) if random.random() > 0.3 else None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        returns.append(ret)
    
    # Create some discards
    discard_reasons = ["expired", "failed_qc", "rejected_return", "reactive", "damaged"]
    for i in range(8):
        discard = {
            "id": str(uuid.uuid4()),
            "discard_id": f"DIS-2025-{str(i+1).zfill(5)}",
            "component_id": components[i+5]["id"] if i+5 < len(components) else str(uuid.uuid4()),
            "reason": random.choice(discard_reasons),
            "reason_details": random.choice([None, "Past expiry date", "Failed screening", "Bag damaged during transport"]),
            "discard_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
            "destruction_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d") if random.random() > 0.3 else None,
            "approved_by": str(uuid.uuid4()) if random.random() > 0.3 else None,
            "processed_by": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        discards.append(discard)
    
    if returns:
        await db.returns.insert_many(returns)
    if discards:
        await db.discards.insert_many(discards)
    
    print(f"✓ Created {len(returns)} returns")
    print(f"✓ Created {len(discards)} discards")

async def seed_chain_of_custody(blood_units):
    """Create chain of custody records"""
    custody_records = []
    locations = ["Collection Room", "Lab", "Processing", "Storage", "QC", "Distribution"]
    
    for unit in blood_units[:20]:
        # Each unit goes through multiple stages
        num_stages = random.randint(2, 5)
        for stage in range(num_stages):
            from_loc = locations[stage % len(locations)]
            to_loc = locations[(stage + 1) % len(locations)]
            
            record = {
                "id": str(uuid.uuid4()),
                "unit_id": unit["id"],
                "stage": f"Stage {stage + 1}",
                "from_location": from_loc,
                "to_location": to_loc,
                "giver_id": str(uuid.uuid4()),
                "receiver_id": str(uuid.uuid4()),
                "timestamp": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))).isoformat(),
                "confirmed": random.choice([True, True, True, False]),
                "notes": random.choice([None, "Temperature verified", "Seal intact", "Handled with care"])
            }
            custody_records.append(record)
    
    if custody_records:
        await db.chain_custody.insert_many(custody_records)
    print(f"✓ Created {len(custody_records)} chain of custody records")

async def main():
    print("\n🩸 Blood Bank Management System - Seeding Database\n")
    print("=" * 50)
    
    # Clear existing data
    await clear_collections()
    
    # Seed data
    await seed_staff_users()
    donors = await seed_donors()
    await seed_donor_requests()
    blood_units = await seed_donations_and_units(donors)
    await seed_lab_tests(blood_units)
    components = await seed_components(blood_units)
    await seed_blood_requests(components)
    await seed_qc_validations(blood_units, components)
    await seed_returns_and_discards(components)
    await seed_chain_of_custody(blood_units)
    
    print("\n" + "=" * 50)
    print("✅ Database seeding complete!\n")
    
    # Print summary
    print("📊 Data Summary:")
    print(f"   - Staff Users: {await db.users.count_documents({})}")
    print(f"   - Donors: {await db.donors.count_documents({})}")
    print(f"   - Donor Requests: {await db.donor_requests.count_documents({})}")
    print(f"   - Screenings: {await db.screenings.count_documents({})}")
    print(f"   - Donations: {await db.donations.count_documents({})}")
    print(f"   - Blood Units: {await db.blood_units.count_documents({})}")
    print(f"   - Lab Tests: {await db.lab_tests.count_documents({})}")
    print(f"   - Components: {await db.components.count_documents({})}")
    print(f"   - Blood Requests: {await db.blood_requests.count_documents({})}")
    print(f"   - QC Validations: {await db.qc_validation.count_documents({})}")
    print(f"   - Returns: {await db.returns.count_documents({})}")
    print(f"   - Discards: {await db.discards.count_documents({})}")
    print(f"   - Chain of Custody: {await db.chain_custody.count_documents({})}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
