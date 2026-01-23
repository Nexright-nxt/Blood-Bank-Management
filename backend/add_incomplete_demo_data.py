"""
Add INCOMPLETE demo data for Laboratory, Processing, and QC Validation
to demonstrate the workflow completion process
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
FIRST_NAMES = ["Rahul", "Priya", "Amit", "Sunita", "Vikram", "Anjali", "Rajesh", "Meera", "Suresh", "Kavita"]
LAST_NAMES = ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Verma", "Reddy", "Nair", "Das", "Mehta"]

async def add_incomplete_demo_data():
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
    labtech = await db.users.find_one({"email": "labtech@testorg.com"}, {"_id": 0})
    admin = await db.users.find_one({"email": "admin@testorg.com"}, {"_id": 0})
    registration = await db.users.find_one({"email": "registration@testorg.com"}, {"_id": 0})
    
    if not labtech or not admin:
        print("ERROR: Required users not found!")
        return
    
    # Get storage locations
    storage_locations = await db.storage_locations.find({"org_id": org_id}, {"_id": 0}).to_list(100)
    
    # Get current counts for ID generation
    donor_count = await db.donors.count_documents({"org_id": org_id})
    donation_count = await db.donations.count_documents({"org_id": org_id})
    blood_unit_count = await db.blood_units.count_documents({"org_id": org_id})
    lab_test_count = await db.lab_tests.count_documents({"org_id": org_id})
    component_count = await db.components.count_documents({"org_id": org_id})
    
    print(f"Current counts - Donors: {donor_count}, Donations: {donation_count}, Units: {blood_unit_count}")
    
    new_donors = []
    new_donations = []
    new_blood_units = []
    new_lab_tests = []
    new_components = []
    new_qc_pending = []
    
    # ========================================
    # 1. LABORATORY - Units awaiting lab testing (status: collected)
    # ========================================
    print("\n=== Creating units for LABORATORY testing ===")
    
    for i in range(4):
        donor_num = donor_count + i + 1
        donation_num = donation_count + i + 1
        unit_num = blood_unit_count + i + 1
        
        donor_id = str(uuid.uuid4())
        donation_id = str(uuid.uuid4())
        unit_id = str(uuid.uuid4())
        
        blood_group = BLOOD_GROUPS[i % len(BLOOD_GROUPS)]
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        collection_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(2, 24))
        
        # Create donor
        donor = {
            "id": donor_id,
            "org_id": org_id,
            "donor_code": f"DNR-2026-{donor_num:06d}",
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "email": f"{first_name.lower()}.{last_name.lower()}{donor_num}@email.com",
            "phone": f"+91 98765{random.randint(10000, 99999)}",
            "blood_group": blood_group,
            "date_of_birth": f"{random.randint(1975, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "gender": random.choice(["male", "female"]),
            "address": f"{random.randint(1, 500)}, {random.choice(['MG Road', 'Park Street', 'Ring Road', 'Main Street'])}, City",
            "status": "active",
            "total_donations": 1,
            "last_donation_date": collection_date.strftime("%Y-%m-%d"),
            "created_at": (collection_date - timedelta(days=30)).isoformat(),
            "updated_at": collection_date.isoformat()
        }
        new_donors.append(donor)
        
        # Create donation
        donation = {
            "id": donation_id,
            "org_id": org_id,
            "donation_number": f"DON-2026-{donation_num:06d}",
            "donor_id": donor_id,
            "donor_name": f"{first_name} {last_name}",
            "blood_group": blood_group,
            "donation_type": random.choice(["whole_blood", "whole_blood", "apheresis"]),
            "donation_date": collection_date.strftime("%Y-%m-%d"),
            "donation_time": collection_date.strftime("%H:%M:%S"),
            "volume_ml": random.randint(350, 450),
            "status": "completed",
            "hemoglobin_level": round(random.uniform(12.5, 16.0), 1),
            "blood_pressure_systolic": random.randint(110, 130),
            "blood_pressure_diastolic": random.randint(70, 85),
            "pulse_rate": random.randint(60, 80),
            "temperature": round(random.uniform(36.5, 37.2), 1),
            "collected_by": registration["email"] if registration else admin["email"],
            "collector_name": registration["full_name"] if registration else admin["full_name"],
            "remarks": "Routine donation",
            "created_at": collection_date.isoformat(),
            "updated_at": collection_date.isoformat()
        }
        new_donations.append(donation)
        
        # Create blood unit with status "collected" - AWAITING LAB TESTING
        blood_unit = {
            "id": unit_id,
            "org_id": org_id,
            "unit_id": f"BU-2026-{unit_num:06d}",
            "donation_id": donation_id,
            "donor_id": donor_id,
            "donor_name": f"{first_name} {last_name}",
            "blood_group": blood_group,
            "rh_factor": blood_group[-1],
            "volume": random.randint(350, 450),
            "collection_date": collection_date.strftime("%Y-%m-%d"),
            "collection_time": collection_date.strftime("%H:%M:%S"),
            "status": "collected",  # AWAITING LAB TESTING
            "bag_type": random.choice(["single", "double", "triple", "quadruple"]),
            "bag_lot_number": f"BAG-{random.randint(1000, 9999)}",
            "anticoagulant": random.choice(["CPDA-1", "CPD", "ACD-A"]),
            "created_at": collection_date.isoformat(),
            "updated_at": collection_date.isoformat()
        }
        new_blood_units.append(blood_unit)
        print(f"  Created unit {blood_unit['unit_id']} (status: collected) - AWAITING LAB")
    
    # ========================================
    # 2. PROCESSING - Units that passed lab tests (status: lab) awaiting processing
    # ========================================
    print("\n=== Creating units for PROCESSING ===")
    
    for i in range(4):
        idx = i + 4  # offset from lab units
        donor_num = donor_count + idx + 1
        donation_num = donation_count + idx + 1
        unit_num = blood_unit_count + idx + 1
        lab_num = lab_test_count + i + 1
        
        donor_id = str(uuid.uuid4())
        donation_id = str(uuid.uuid4())
        unit_id = str(uuid.uuid4())
        lab_test_id = str(uuid.uuid4())
        
        blood_group = BLOOD_GROUPS[(i + 4) % len(BLOOD_GROUPS)]
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        collection_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 3))
        test_date = collection_date + timedelta(hours=random.randint(4, 12))
        
        # Create donor
        donor = {
            "id": donor_id,
            "org_id": org_id,
            "donor_code": f"DNR-2026-{donor_num:06d}",
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "email": f"{first_name.lower()}.{last_name.lower()}{donor_num}@email.com",
            "phone": f"+91 98765{random.randint(10000, 99999)}",
            "blood_group": blood_group,
            "date_of_birth": f"{random.randint(1975, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "gender": random.choice(["male", "female"]),
            "address": f"{random.randint(1, 500)}, {random.choice(['MG Road', 'Park Street', 'Ring Road', 'Main Street'])}, City",
            "status": "active",
            "total_donations": 1,
            "last_donation_date": collection_date.strftime("%Y-%m-%d"),
            "created_at": (collection_date - timedelta(days=30)).isoformat(),
            "updated_at": test_date.isoformat()
        }
        new_donors.append(donor)
        
        # Create donation
        donation = {
            "id": donation_id,
            "org_id": org_id,
            "donation_number": f"DON-2026-{donation_num:06d}",
            "donor_id": donor_id,
            "donor_name": f"{first_name} {last_name}",
            "blood_group": blood_group,
            "donation_type": "whole_blood",
            "donation_date": collection_date.strftime("%Y-%m-%d"),
            "donation_time": collection_date.strftime("%H:%M:%S"),
            "volume_ml": random.randint(400, 450),
            "status": "completed",
            "hemoglobin_level": round(random.uniform(13.0, 15.5), 1),
            "blood_pressure_systolic": random.randint(110, 125),
            "blood_pressure_diastolic": random.randint(70, 80),
            "pulse_rate": random.randint(65, 75),
            "temperature": round(random.uniform(36.6, 37.0), 1),
            "collected_by": registration["email"] if registration else admin["email"],
            "collector_name": registration["full_name"] if registration else admin["full_name"],
            "remarks": "Good donation",
            "created_at": collection_date.isoformat(),
            "updated_at": test_date.isoformat()
        }
        new_donations.append(donation)
        
        # Create blood unit with status "lab" - PASSED TESTING, AWAITING PROCESSING
        blood_unit = {
            "id": unit_id,
            "org_id": org_id,
            "unit_id": f"BU-2026-{unit_num:06d}",
            "donation_id": donation_id,
            "donor_id": donor_id,
            "donor_name": f"{first_name} {last_name}",
            "blood_group": blood_group,
            "confirmed_blood_group": blood_group,
            "rh_factor": blood_group[-1],
            "volume": random.randint(400, 450),
            "collection_date": collection_date.strftime("%Y-%m-%d"),
            "collection_time": collection_date.strftime("%H:%M:%S"),
            "status": "lab",  # PASSED LAB TESTS, READY FOR PROCESSING
            "bag_type": random.choice(["triple", "quadruple"]),
            "bag_lot_number": f"BAG-{random.randint(1000, 9999)}",
            "anticoagulant": "CPDA-1",
            "created_at": collection_date.isoformat(),
            "updated_at": test_date.isoformat()
        }
        new_blood_units.append(blood_unit)
        
        # Create COMPLETED lab test for this unit
        lab_test = {
            "id": lab_test_id,
            "org_id": org_id,
            "test_number": f"LAB-2026-{lab_num:06d}",
            "unit_id": unit_id,
            "unit_number": blood_unit["unit_id"],
            "donation_id": donation_id,
            "donor_id": donor_id,
            "blood_group": blood_group,
            "rh_factor": blood_group[-1],
            "test_date": test_date.strftime("%Y-%m-%d"),
            "test_time": test_date.strftime("%H:%M:%S"),
            "received_date": test_date.strftime("%Y-%m-%d"),
            "received_time": test_date.strftime("%H:%M:%S"),
            "tested_by": labtech["email"],
            "technician_name": labtech["full_name"],
            "verified_by": admin["email"],
            "verifier_name": admin["full_name"],
            "hiv_status": "non_reactive",
            "hiv_result": "non_reactive",
            "hiv_method": "ELISA 4th Generation",
            "hiv_kit": "Abbott Architect HIV Ag/Ab",
            "hiv_lot": f"LOT{random.randint(2026001, 2026999)}",
            "hbsag_status": "non_reactive",
            "hbsag_result": "non_reactive",
            "hbsag_method": "ELISA",
            "hbsag_kit": "Abbott Architect HBsAg",
            "hbsag_lot": f"LOT{random.randint(2026001, 2026999)}",
            "hcv_status": "non_reactive",
            "hcv_result": "non_reactive",
            "hcv_method": "ELISA 3rd Generation",
            "hcv_kit": "Abbott Architect Anti-HCV",
            "hcv_lot": f"LOT{random.randint(2026001, 2026999)}",
            "syphilis_status": "non_reactive",
            "syphilis_result": "non_reactive",
            "syphilis_method": "TPHA",
            "syphilis_kit": "Serodia TPPA",
            "syphilis_lot": f"LOT{random.randint(2026001, 2026999)}",
            "malaria_status": "non_reactive",
            "malaria_result": "non_reactive",
            "malaria_method": "Rapid ICT",
            "malaria_kit": "SD Bioline Malaria",
            "malaria_lot": f"LOT{random.randint(2026001, 2026999)}",
            "blood_group_forward": blood_group,
            "blood_group_reverse": blood_group,
            "blood_group_confirmed": blood_group,
            "rh_typing": blood_group[-1],
            "antibody_screen": "negative",
            "dat_result": "negative",
            "irregular_antibodies": "none detected",
            "overall_status": "passed",
            "status": "completed",
            "remarks": "All tests non-reactive. Cleared for processing.",
            "verified_at": (test_date + timedelta(hours=4)).isoformat(),
            "created_at": test_date.isoformat(),
            "updated_at": test_date.isoformat()
        }
        new_lab_tests.append(lab_test)
        print(f"  Created unit {blood_unit['unit_id']} (status: lab) - AWAITING PROCESSING")
    
    # ========================================
    # 3. QC VALIDATION - Components awaiting QC (status: processing)
    # ========================================
    print("\n=== Creating components for QC VALIDATION ===")
    
    for i in range(4):
        idx = i + 8  # offset from previous units
        donor_num = donor_count + idx + 1
        donation_num = donation_count + idx + 1
        unit_num = blood_unit_count + idx + 1
        lab_num = lab_test_count + i + 5  # offset from processing lab tests
        comp_num = component_count + i + 1
        
        donor_id = str(uuid.uuid4())
        donation_id = str(uuid.uuid4())
        unit_id = str(uuid.uuid4())
        lab_test_id = str(uuid.uuid4())
        
        blood_group = BLOOD_GROUPS[i % len(BLOOD_GROUPS)]
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        collection_date = datetime.now(timezone.utc) - timedelta(days=random.randint(2, 5))
        test_date = collection_date + timedelta(hours=6)
        processing_date = test_date + timedelta(hours=4)
        
        # Create donor
        donor = {
            "id": donor_id,
            "org_id": org_id,
            "donor_code": f"DNR-2026-{donor_num:06d}",
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "email": f"{first_name.lower()}.{last_name.lower()}{donor_num}@email.com",
            "phone": f"+91 98765{random.randint(10000, 99999)}",
            "blood_group": blood_group,
            "date_of_birth": f"{random.randint(1975, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "gender": random.choice(["male", "female"]),
            "status": "active",
            "total_donations": 1,
            "last_donation_date": collection_date.strftime("%Y-%m-%d"),
            "created_at": (collection_date - timedelta(days=30)).isoformat(),
            "updated_at": processing_date.isoformat()
        }
        new_donors.append(donor)
        
        # Create donation
        donation = {
            "id": donation_id,
            "org_id": org_id,
            "donation_number": f"DON-2026-{donation_num:06d}",
            "donor_id": donor_id,
            "donor_name": f"{first_name} {last_name}",
            "blood_group": blood_group,
            "donation_type": "whole_blood",
            "donation_date": collection_date.strftime("%Y-%m-%d"),
            "donation_time": collection_date.strftime("%H:%M:%S"),
            "volume_ml": 450,
            "status": "completed",
            "created_at": collection_date.isoformat(),
            "updated_at": processing_date.isoformat()
        }
        new_donations.append(donation)
        
        # Create blood unit (already processed)
        blood_unit = {
            "id": unit_id,
            "org_id": org_id,
            "unit_id": f"BU-2026-{unit_num:06d}",
            "donation_id": donation_id,
            "donor_id": donor_id,
            "donor_name": f"{first_name} {last_name}",
            "blood_group": blood_group,
            "confirmed_blood_group": blood_group,
            "rh_factor": blood_group[-1],
            "volume": 450,
            "collection_date": collection_date.strftime("%Y-%m-%d"),
            "status": "processing",  # Components created, awaiting QC
            "created_at": collection_date.isoformat(),
            "updated_at": processing_date.isoformat()
        }
        new_blood_units.append(blood_unit)
        
        # Create completed lab test
        lab_test = {
            "id": lab_test_id,
            "org_id": org_id,
            "test_number": f"LAB-2026-{lab_num:06d}",
            "unit_id": unit_id,
            "unit_number": blood_unit["unit_id"],
            "donation_id": donation_id,
            "donor_id": donor_id,
            "blood_group": blood_group,
            "test_date": test_date.strftime("%Y-%m-%d"),
            "tested_by": labtech["email"],
            "technician_name": labtech["full_name"],
            "verified_by": admin["email"],
            "verifier_name": admin["full_name"],
            "hiv_status": "non_reactive",
            "hiv_result": "non_reactive",
            "hbsag_status": "non_reactive",
            "hbsag_result": "non_reactive",
            "hcv_status": "non_reactive",
            "hcv_result": "non_reactive",
            "syphilis_status": "non_reactive",
            "syphilis_result": "non_reactive",
            "malaria_status": "non_reactive",
            "malaria_result": "non_reactive",
            "blood_group_confirmed": blood_group,
            "overall_status": "passed",
            "status": "completed",
            "created_at": test_date.isoformat(),
            "updated_at": test_date.isoformat()
        }
        new_lab_tests.append(lab_test)
        
        # Create COMPONENT with status "processing" - AWAITING QC
        storage_loc = random.choice(storage_locations) if storage_locations else None
        component_types = [
            ("prbc", "Packed Red Blood Cells", 280, 42),
            ("ffp", "Fresh Frozen Plasma", 200, 365),
            ("platelets", "Platelet Concentrate", 50, 5),
        ]
        
        comp_type, comp_name, volume, expiry_days = component_types[i % 3]
        
        component = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "component_id": f"CMP-{comp_type.upper()}-{comp_num:06d}",
            "unit_id": unit_id,
            "unit_number": blood_unit["unit_id"],
            "component_type": comp_type,
            "component_name": comp_name,
            "blood_group": blood_group,
            "volume_ml": volume,
            "status": "processing",  # AWAITING QC VALIDATION
            "storage_location": storage_loc["id"] if storage_loc else None,
            "storage_location_name": storage_loc.get("name") if storage_loc else "Pending Assignment",
            "processing_date": processing_date.isoformat(),
            "processing_start": processing_date.isoformat(),
            "processing_end": (processing_date + timedelta(hours=1)).isoformat(),
            "processing_number": f"PRC-2026-{comp_num:06d}",
            "processing_method": "centrifugation",
            "processed_by": labtech["email"],
            "processor_name": labtech["full_name"],
            "centrifuge_speed": random.randint(3000, 4500),
            "centrifuge_time_minutes": random.randint(10, 18),
            "separation_quality": random.choice(["good", "excellent"]),
            "leukoreduced": random.choice([True, False]),
            "irradiated": False,
            "expiry_date": (processing_date + timedelta(days=expiry_days)).isoformat(),
            "quality_notes": "Processing complete. Awaiting QC validation.",
            "created_at": processing_date.isoformat(),
            "updated_at": processing_date.isoformat()
        }
        new_components.append(component)
        print(f"  Created component {component['component_id']} (status: processing) - AWAITING QC")
    
    # ========================================
    # Insert all data
    # ========================================
    print("\n=== Inserting data into database ===")
    
    if new_donors:
        await db.donors.insert_many(new_donors)
        print(f"  Inserted {len(new_donors)} donors")
    
    if new_donations:
        await db.donations.insert_many(new_donations)
        print(f"  Inserted {len(new_donations)} donations")
    
    if new_blood_units:
        await db.blood_units.insert_many(new_blood_units)
        print(f"  Inserted {len(new_blood_units)} blood units")
    
    if new_lab_tests:
        await db.lab_tests.insert_many(new_lab_tests)
        print(f"  Inserted {len(new_lab_tests)} lab tests")
    
    if new_components:
        await db.components.insert_many(new_components)
        print(f"  Inserted {len(new_components)} components")
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "="*60)
    print("SUMMARY - INCOMPLETE DATA FOR DEMO")
    print("="*60)
    
    collected_count = await db.blood_units.count_documents({"org_id": org_id, "status": "collected"})
    lab_count = await db.blood_units.count_documents({"org_id": org_id, "status": "lab"})
    processing_components = await db.components.count_documents({"org_id": org_id, "status": "processing"})
    
    print(f"\n1. LABORATORY PAGE - Units awaiting testing:")
    print(f"   {collected_count} blood units with status 'collected'")
    print(f"   -> These need lab tests to be performed")
    
    print(f"\n2. PROCESSING PAGE - Units ready for processing:")
    print(f"   {lab_count} blood units with status 'lab'")
    print(f"   -> These passed lab tests and need to be processed into components")
    
    print(f"\n3. QC VALIDATION PAGE - Components awaiting QC:")
    print(f"   {processing_components} components with status 'processing'")
    print(f"   -> These need QC validation before release")
    
    print("\n" + "="*60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_incomplete_demo_data())
