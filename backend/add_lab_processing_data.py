"""
Add comprehensive Laboratory and Processing data for Blood Link demo
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

# Test kits and methods
HIV_KITS = ["Abbott Architect HIV Ag/Ab", "Bio-Rad GS HIV Combo", "Roche Elecsys HIV"]
HBSAG_KITS = ["Abbott Architect HBsAg", "Siemens ADVIA HBsAg", "Roche Elecsys HBsAg"]
HCV_KITS = ["Abbott Architect Anti-HCV", "Ortho HCV 3.0", "Bio-Rad Monolisa Anti-HCV"]
SYPHILIS_KITS = ["Serodia TPPA", "Bio-Rad Syphilis Total", "Abbott Architect Syphilis"]
MALARIA_KITS = ["SD Bioline Malaria", "CareStart Malaria", "First Response Malaria"]

TEST_METHODS = {
    "hiv": "ELISA 4th Generation",
    "hbsag": "ELISA",
    "hcv": "ELISA 3rd Generation",
    "syphilis": "TPHA",
    "malaria": "Rapid ICT"
}

ADDITIVE_SOLUTIONS = ["SAGM", "CPDA-1", "AS-1", "AS-3", "AS-5"]
PROCESSING_METHODS = ["centrifugation", "apheresis", "filtration"]
SEPARATION_QUALITIES = ["excellent", "good", "acceptable"]

async def add_lab_processing_data():
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
    
    if not labtech or not admin:
        print("ERROR: Required users not found!")
        return
    
    # Get existing blood units
    blood_units = await db.blood_units.find({"org_id": org_id}, {"_id": 0}).to_list(100)
    print(f"Found {len(blood_units)} blood units")
    
    # Get existing donations
    donations = await db.donations.find({"org_id": org_id}, {"_id": 0}).to_list(100)
    print(f"Found {len(donations)} donations")
    
    # Get storage locations
    storage_locations = await db.storage_locations.find({"org_id": org_id}, {"_id": 0}).to_list(100)
    print(f"Found {len(storage_locations)} storage locations")
    
    # Get existing lab test count
    existing_lab_count = await db.lab_tests.count_documents({"org_id": org_id})
    existing_component_count = await db.components.count_documents({"org_id": org_id})
    print(f"Existing lab tests: {existing_lab_count}, components: {existing_component_count}")
    
    # Create additional lab tests with different statuses
    new_lab_tests = []
    new_components = []
    
    # Additional test scenarios
    test_scenarios = [
        {"overall_status": "passed", "status": "completed"},
        {"overall_status": "passed", "status": "completed"},
        {"overall_status": "pending", "status": "in_progress"},
        {"overall_status": "pending", "status": "pending_verification"},
        {"overall_status": "failed", "status": "completed"},  # One with reactive result
    ]
    
    lab_test_num = existing_lab_count + 1
    component_num = existing_component_count + 1
    
    for idx, unit in enumerate(blood_units):
        if idx >= len(test_scenarios):
            break
            
        scenario = test_scenarios[idx]
        
        # Find matching donation
        donation = next((d for d in donations if d.get("donor_id") == unit.get("donor_id")), None)
        
        base_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 14))
        test_date = base_date.strftime("%Y-%m-%d")
        test_time = f"{random.randint(8, 16):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
        
        # Determine test results based on scenario
        if scenario["overall_status"] == "failed":
            # One reactive result for failed scenario
            hiv_result = "reactive" if random.random() > 0.5 else "non_reactive"
            hbsag_result = "non_reactive" if hiv_result == "reactive" else "reactive"
            hcv_result = "non_reactive"
            syphilis_result = "non_reactive"
            malaria_result = "non_reactive"
        elif scenario["overall_status"] == "pending":
            # Some results pending
            hiv_result = "non_reactive"
            hbsag_result = random.choice(["non_reactive", "pending"])
            hcv_result = random.choice(["non_reactive", "pending"])
            syphilis_result = "non_reactive"
            malaria_result = "non_reactive"
        else:
            # All non-reactive
            hiv_result = "non_reactive"
            hbsag_result = "non_reactive"
            hcv_result = "non_reactive"
            syphilis_result = "non_reactive"
            malaria_result = "non_reactive"
        
        lab_test = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "test_number": f"LAB-2026-{lab_test_num:06d}",
            "unit_id": unit["id"],
            "unit_number": unit.get("unit_id", ""),
            "donation_id": donation["id"] if donation else None,
            "donor_id": unit.get("donor_id"),
            "blood_group": unit.get("blood_group"),
            "rh_factor": unit.get("blood_group", "")[-1] if unit.get("blood_group") else "+",
            "test_date": test_date,
            "test_time": test_time,
            "received_date": test_date,
            "received_time": test_time,
            "tested_by": labtech["email"],
            "technician_name": labtech["full_name"],
            "verified_by": admin["email"] if scenario["status"] == "completed" else None,
            "verifier_name": admin["full_name"] if scenario["status"] == "completed" else None,
            
            # HIV Test
            "hiv_status": hiv_result,
            "hiv_result": hiv_result,
            "hiv_method": TEST_METHODS["hiv"],
            "hiv_kit": random.choice(HIV_KITS),
            "hiv_lot": f"LOT2026{random.randint(100, 999)}",
            "hiv_expiry": (base_date + timedelta(days=180)).strftime("%Y-%m-%d"),
            
            # HBsAg Test
            "hbsag_status": hbsag_result,
            "hbsag_result": hbsag_result,
            "hbsag_method": TEST_METHODS["hbsag"],
            "hbsag_kit": random.choice(HBSAG_KITS),
            "hbsag_lot": f"LOT2026{random.randint(100, 999)}",
            "hbsag_expiry": (base_date + timedelta(days=180)).strftime("%Y-%m-%d"),
            
            # HCV Test
            "hcv_status": hcv_result,
            "hcv_result": hcv_result,
            "hcv_method": TEST_METHODS["hcv"],
            "hcv_kit": random.choice(HCV_KITS),
            "hcv_lot": f"LOT2026{random.randint(100, 999)}",
            "hcv_expiry": (base_date + timedelta(days=180)).strftime("%Y-%m-%d"),
            
            # Syphilis Test
            "syphilis_status": syphilis_result,
            "syphilis_result": syphilis_result,
            "syphilis_method": TEST_METHODS["syphilis"],
            "syphilis_kit": random.choice(SYPHILIS_KITS),
            "syphilis_lot": f"LOT2026{random.randint(100, 999)}",
            "syphilis_expiry": (base_date + timedelta(days=180)).strftime("%Y-%m-%d"),
            
            # Malaria Test
            "malaria_status": malaria_result,
            "malaria_result": malaria_result,
            "malaria_method": TEST_METHODS["malaria"],
            "malaria_kit": random.choice(MALARIA_KITS),
            "malaria_lot": f"LOT2026{random.randint(100, 999)}",
            "malaria_expiry": (base_date + timedelta(days=180)).strftime("%Y-%m-%d"),
            
            # Blood Group Confirmation
            "blood_group_forward": unit.get("blood_group"),
            "blood_group_reverse": unit.get("blood_group"),
            "blood_group_confirmed": unit.get("blood_group"),
            "rh_typing": unit.get("blood_group", "")[-1] if unit.get("blood_group") else "+",
            "antibody_screen": "negative",
            "dat_result": "negative",
            "irregular_antibodies": "none detected",
            
            # Status
            "overall_status": scenario["overall_status"],
            "status": scenario["status"],
            "remarks": "All tests completed" if scenario["status"] == "completed" else "Testing in progress",
            
            # Timestamps
            "verified_at": (base_date + timedelta(hours=4)).isoformat() if scenario["status"] == "completed" else None,
            "created_at": base_date.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        new_lab_tests.append(lab_test)
        lab_test_num += 1
        
        # Create components for passed tests only
        if scenario["overall_status"] == "passed" and scenario["status"] == "completed":
            component_types = [
                ("prbc", "Packed Red Blood Cells", 280, 42, 2, 6),
                ("ffp", "Fresh Frozen Plasma", 200, 365, -30, -25),
                ("platelets", "Platelet Concentrate", 50, 5, 20, 24),
            ]
            
            processing_date = base_date + timedelta(hours=2)
            
            for comp_type, comp_name, volume, expiry_days, temp_min, temp_max in component_types:
                # Find appropriate storage location
                storage_loc = random.choice(storage_locations) if storage_locations else None
                
                component = {
                    "id": str(uuid.uuid4()),
                    "org_id": org_id,
                    "component_id": f"CMP-{comp_type.upper()}-{component_num:06d}",
                    "unit_id": unit["id"],
                    "unit_number": unit.get("unit_id", ""),
                    "component_type": comp_type,
                    "component_name": comp_name,
                    "blood_group": unit.get("blood_group"),
                    "volume_ml": volume + random.randint(-10, 10),
                    "status": random.choice(["available", "reserved", "available"]),
                    "storage_location": storage_loc["id"] if storage_loc else None,
                    "storage_location_name": storage_loc.get("name") if storage_loc else "Default Storage",
                    
                    # Processing details
                    "processing_date": processing_date.isoformat(),
                    "processing_start": processing_date.isoformat(),
                    "processing_end": (processing_date + timedelta(hours=1)).isoformat(),
                    "processing_number": f"PRC-2026-{component_num:06d}",
                    "processing_method": random.choice(PROCESSING_METHODS),
                    "processed_by": labtech["email"],
                    "processor_name": labtech["full_name"],
                    
                    # Centrifuge details
                    "centrifuge_speed": random.randint(3000, 5000),
                    "centrifuge_time_minutes": random.randint(10, 20),
                    "separation_quality": random.choice(SEPARATION_QUALITIES),
                    
                    # Additional processing info
                    "additive_solution": random.choice(ADDITIVE_SOLUTIONS) if comp_type == "prbc" else None,
                    "leukoreduced": random.choice([True, False]),
                    "irradiated": random.choice([True, False]),
                    
                    # Temperature range
                    "storage_temp_min": temp_min,
                    "storage_temp_max": temp_max,
                    
                    # Expiry
                    "expiry_date": (processing_date + timedelta(days=expiry_days)).isoformat(),
                    
                    # Verification
                    "verified_by": admin["email"],
                    "verified_at": (processing_date + timedelta(hours=2)).isoformat(),
                    
                    # Notes
                    "quality_notes": "Processing completed successfully. All parameters within acceptable range.",
                    
                    # Timestamps
                    "created_at": processing_date.isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                new_components.append(component)
                component_num += 1
    
    # Insert new data
    if new_lab_tests:
        print(f"\nInserting {len(new_lab_tests)} new lab tests...")
        await db.lab_tests.insert_many(new_lab_tests)
        print("Lab tests inserted successfully!")
    
    if new_components:
        print(f"Inserting {len(new_components)} new components...")
        await db.components.insert_many(new_components)
        print("Components inserted successfully!")
    
    # Print summary
    final_lab_count = await db.lab_tests.count_documents({"org_id": org_id})
    final_component_count = await db.components.count_documents({"org_id": org_id})
    
    print(f"\n=== Summary ===")
    print(f"Total Lab Tests: {final_lab_count}")
    print(f"Total Components: {final_component_count}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_lab_processing_data())
