"""
Comprehensive Demo Data Seeding Script for Blood Link
Creates end-to-end data for ALL modules to demonstrate the complete workflow.

Usage:
  cd /app/backend
  DB_NAME=bloodlink_production python scripts/seed_demo_data.py
  
For production deployment, set MONGO_URL to your production MongoDB connection string.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import bcrypt

# Password hashing (using native bcrypt to match backend)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "bloodlink_production")

# Demo data constants
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
COMPONENT_TYPES = ['whole_blood', 'prc', 'ffp', 'platelets', 'cryoprecipitate']
MALAYSIAN_ID_TYPES = ['mykad', 'mykas', 'mykid', 'mypr', 'passport']

# Malaysian names
FIRST_NAMES = ['Ahmad', 'Siti', 'Muhammad', 'Nur', 'Mohamed', 'Fatimah', 'Ali', 'Aishah', 'Hassan', 'Zainab', 
               'Raj', 'Priya', 'Lee', 'Wong', 'Tan', 'Lim', 'Kumar', 'Devi', 'Chen', 'Amir']
LAST_NAMES = ['Abdullah', 'Rahman', 'Hassan', 'Ibrahim', 'Ismail', 'Ahmad', 'Yusof', 'Omar', 'Zakaria', 'Ali',
              'Kumar', 'Singh', 'Tan', 'Lee', 'Wong', 'Lim', 'Chen', 'Ng', 'Krishnan', 'Muthu']

# Malaysian cities with coordinates
CITIES = [
    {'city': 'Kuala Lumpur', 'state': 'Wilayah Persekutuan', 'lat': 3.1390, 'lng': 101.6869},
    {'city': 'Petaling Jaya', 'state': 'Selangor', 'lat': 3.1073, 'lng': 101.6067},
    {'city': 'Shah Alam', 'state': 'Selangor', 'lat': 3.0733, 'lng': 101.5185},
    {'city': 'Johor Bahru', 'state': 'Johor', 'lat': 1.4927, 'lng': 103.7414},
    {'city': 'George Town', 'state': 'Penang', 'lat': 5.4141, 'lng': 100.3288},
    {'city': 'Ipoh', 'state': 'Perak', 'lat': 4.5975, 'lng': 101.0901},
]

# Malaysian hospitals
HOSPITALS = [
    'Hospital Kuala Lumpur', 'Hospital Selayang', 'Hospital Sungai Buloh',
    'Pusat Perubatan Universiti Malaya', 'Hospital Sultan Ismail',
    'Hospital Pulau Pinang', 'Hospital Sultanah Aminah'
]

def generate_mykad():
    """Generate Malaysian IC number"""
    year = random.randint(70, 99)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    state = random.randint(1, 14)
    seq = random.randint(1000, 9999)
    return f"{year:02d}{month:02d}{day:02d}-{state:02d}-{seq}"

def generate_phone():
    """Generate Malaysian phone number"""
    prefixes = ['011', '012', '013', '014', '016', '017', '018', '019']
    return f"+60-{random.choice(prefixes)[1:]}-{random.randint(1000000, 9999999)}"

def random_date(days_ago_min, days_ago_max):
    """Generate random datetime between days ago range"""
    days = random.randint(days_ago_min, days_ago_max)
    return datetime.now(timezone.utc) - timedelta(days=days)

def random_date_str(days_ago_min, days_ago_max):
    """Generate random date string"""
    return random_date(days_ago_min, days_ago_max).strftime("%Y-%m-%d")

def random_datetime_str(days_ago_min, days_ago_max):
    """Generate random datetime ISO string"""
    return random_date(days_ago_min, days_ago_max).isoformat()

async def clear_all_data(db):
    """Clear all demo data"""
    collections = [
        'donors', 'donations', 'screenings', 'lab_tests', 'blood_units', 
        'components', 'blood_requests', 'requestors', 'broadcasts',
        'inter_org_requests', 'storage_locations', 'audit_logs',
        'qc_records', 'disposal_records', 'alerts', 'logistics_orders',
        'training_records', 'compliance_records', 'quarantine_records',
        'inventory_transactions', 'organizations', 'users', 'roles'
    ]
    
    for coll in collections:
        await db[coll].delete_many({})
    
    print("✓ Cleared all existing data")

async def seed_demo_data():
    """Main function to seed all demo data"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 60)
    print("BLOOD LINK - Comprehensive Demo Data Seeding")
    print("=" * 60)
    
    # Clear existing data
    await clear_all_data(db)
    
    # ========================================
    # 1. ORGANIZATION & ADMIN
    # ========================================
    print("\n🏢 Creating Organization & Admin...")
    org_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    city_info = CITIES[0]
    
    organization = {
        "id": org_id,
        "org_name": "Pusat Darah Negara Malaysia",
        "org_type": "blood_bank",
        "is_parent": True,
        "parent_org_id": None,
        "address": "Jalan Tun Razak, 50400",
        "city": city_info['city'],
        "state": city_info['state'],
        "country": "Malaysia",
        "pincode": "50400",
        "latitude": city_info['lat'],
        "longitude": city_info['lng'],
        "location": {"type": "Point", "coordinates": [city_info['lng'], city_info['lat']]},
        "contact_person": "Dr. Ahmad bin Hassan",
        "contact_phone": "+60-3-26132688",
        "contact_email": "admin@pdn.gov.my",
        "license_number": "PDN-001-2024",
        "is_active": True,
        "is_24x7": True,
        "operating_hours": "24/7",
        "blood_link_visible": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.organizations.insert_one(organization)
    await db.organizations.create_index([("location", "2dsphere")])
    
    admin_user = {
        "id": admin_id,
        "email": "admin@pdn.gov.my",
        "password_hash": pwd_context.hash("Admin@123"),
        "full_name": "Dr. Ahmad bin Hassan",
        "phone": "+60-3-26132688",
        "role": "admin",
        "user_type": "super_admin",
        "org_id": org_id,
        "org_name": organization['org_name'],
        "is_active": True,
        "mfa_enabled": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(admin_user)
    
    # Create additional staff users
    staff_roles = [
        ("labtech@pdn.gov.my", "Siti Aminah", "lab_technician"),
        ("nurse@pdn.gov.my", "Nurse Fatimah", "registration"),
        ("inventory@pdn.gov.my", "Ali Rahman", "inventory"),
    ]
    staff_ids = []
    for email, name, role in staff_roles:
        staff_id = str(uuid.uuid4())
        staff_ids.append(staff_id)
        await db.users.insert_one({
            "id": staff_id,
            "email": email,
            "password_hash": pwd_context.hash("Staff@123"),
            "full_name": name,
            "phone": generate_phone(),
            "role": role,
            "user_type": "staff",
            "org_id": org_id,
            "org_name": organization['org_name'],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    
    print(f"   ✓ Created organization: {organization['org_name']}")
    print(f"   ✓ Created admin: admin@pdn.gov.my / Admin@123")
    print(f"   ✓ Created 3 staff users")
    
    # ========================================
    # 2. DONORS (20 with complete data)
    # ========================================
    print("\n👤 Creating Donors...")
    donors = []
    for i in range(20):
        city = random.choice(CITIES)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        status = random.choices(['eligible', 'pending', 'deferred', 'blacklisted'], weights=[70, 15, 10, 5])[0]
        dob = f"{random.randint(1960, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        
        donor = {
            "id": str(uuid.uuid4()),
            "donor_id": f"PDN-D-{2024001 + i}",
            "id_type": random.choice(MALAYSIAN_ID_TYPES),
            "id_number": generate_mykad(),
            "first_name": first,
            "last_name": last,
            "full_name": f"{first} {last}",
            "date_of_birth": dob,
            "gender": random.choice(['male', 'female']),
            "blood_group": random.choice(BLOOD_GROUPS),
            "rh_factor": random.choice(['+', '-']),
            "phone": generate_phone(),
            "email": f"{first.lower()}.{last.lower()}{random.randint(10,99)}@email.com.my",
            "address": f"No. {random.randint(1, 200)}, Jalan {random.choice(['Merdeka', 'Bukit Bintang', 'Ampang', 'Cheras', 'Bangsar'])} {random.randint(1, 20)}",
            "city": city['city'],
            "state": city['state'],
            "country": "Malaysia",
            "pincode": f"{random.randint(40000, 81000)}",
            "latitude": city['lat'] + random.uniform(-0.02, 0.02),
            "longitude": city['lng'] + random.uniform(-0.02, 0.02),
            "occupation": random.choice(['Engineer', 'Teacher', 'Doctor', 'Accountant', 'Business Owner', 'Government Staff', 'Student']),
            "employer": random.choice(['Petronas', 'Maybank', 'TNB', 'TM', 'AirAsia', 'Self-employed', 'Government']),
            "emergency_contact_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "emergency_contact_phone": generate_phone(),
            "emergency_contact_relationship": random.choice(['spouse', 'parent', 'sibling', 'friend']),
            "status": status,
            "eligibility_status": "eligible" if status == "eligible" else "pending",
            "donation_count": random.randint(0, 15) if status == 'eligible' else 0,
            "total_donations": random.randint(0, 15) if status == 'eligible' else 0,
            "last_donation_date": random_date_str(60, 365) if status == 'eligible' and random.random() > 0.3 else None,
            "next_eligible_date": random_date_str(-30, 30) if status == 'eligible' else None,
            "medical_conditions": None if random.random() > 0.2 else random.choice(['None', 'Controlled Hypertension', 'Controlled Diabetes']),
            "medications": None if random.random() > 0.1 else random.choice(['None', 'Paracetamol PRN']),
            "allergies": None if random.random() > 0.15 else random.choice(['None', 'Penicillin', 'Shellfish']),
            "notes": "Regular donor" if status == 'eligible' and random.random() > 0.7 else None,
            "org_id": org_id,
            "created_at": random_datetime_str(30, 365),
            "created_by": admin_id,
            "updated_at": random_datetime_str(1, 30),
        }
        donors.append(donor)
    
    await db.donors.insert_many(donors)
    print(f"   ✓ Created {len(donors)} donors")
    
    # ========================================
    # 3. SCREENINGS (15 screenings)
    # ========================================
    print("\n🔬 Creating Screenings...")
    screenings = []
    eligible_donors = [d for d in donors if d['status'] == 'eligible'][:15]
    
    for i, donor in enumerate(eligible_donors):
        screening_date = random_date(1, 30)
        screening = {
            "id": str(uuid.uuid4()),
            "screening_id": f"PDN-SCR-{2024001 + i}",
            "donor_id": donor['id'],
            "donor_name": donor['full_name'],
            "screening_date": screening_date.strftime("%Y-%m-%d"),
            "screening_time": f"{random.randint(8, 16):02d}:{random.randint(0, 59):02d}",
            # Vital signs
            "hemoglobin": round(random.uniform(12.5, 17.0), 1),
            "hemoglobin_unit": "g/dL",
            "blood_pressure_systolic": random.randint(100, 140),
            "blood_pressure_diastolic": random.randint(60, 90),
            "pulse": random.randint(60, 100),
            "temperature": round(random.uniform(36.0, 37.5), 1),
            "weight_kg": round(random.uniform(50, 95), 1),
            "height_cm": random.randint(150, 185),
            # Blood typing
            "preliminary_blood_group": donor['blood_group'],
            "preliminary_rh": '+' if '+' in donor['blood_group'] else '-',
            # Health questionnaire
            "questionnaire_completed": True,
            "recent_illness": False,
            "recent_travel": random.choice([True, False]),
            "recent_travel_details": "Singapore - 2 weeks ago" if random.random() > 0.8 else None,
            "recent_surgery": False,
            "recent_tattoo": False,
            "recent_medication": random.choice([True, False]),
            "recent_medication_details": "Paracetamol for headache" if random.random() > 0.8 else None,
            "high_risk_behavior": False,
            # Result
            "eligibility_status": "eligible",
            "eligibility_reason": None,
            "screened_by": random.choice(staff_ids),
            "screened_by_name": "Nurse Fatimah",
            "verified_by": admin_id if random.random() > 0.5 else None,
            "notes": "Donor in good health, cleared for donation" if random.random() > 0.5 else None,
            "org_id": org_id,
            "created_at": screening_date.isoformat(),
        }
        screenings.append(screening)
    
    await db.screenings.insert_many(screenings)
    print(f"   ✓ Created {len(screenings)} screenings")
    
    # ========================================
    # 4. DONATIONS (12 completed donations)
    # ========================================
    print("\n🩸 Creating Donations...")
    donations = []
    
    for i, screening in enumerate(screenings[:12]):
        donor = next(d for d in donors if d['id'] == screening['donor_id'])
        donation_date = datetime.fromisoformat(screening['created_at'].replace('Z', '+00:00'))
        start_time = donation_date + timedelta(minutes=30)
        end_time = start_time + timedelta(minutes=random.randint(8, 15))
        
        donation = {
            "id": str(uuid.uuid4()),
            "donation_id": f"PDN-DON-{2024001 + i}",
            "donor_id": donor['id'],
            "donor_name": donor['full_name'],
            "screening_id": screening['id'],
            "blood_group": donor['blood_group'],
            "donation_type": random.choice(['whole_blood', 'apheresis_platelet', 'apheresis_plasma']),
            "donation_date": donation_date.strftime("%Y-%m-%d"),
            "donation_time": start_time.strftime("%H:%M"),
            "collection_start_time": start_time.isoformat(),
            "collection_end_time": end_time.isoformat(),
            "volume_collected": random.choice([350, 450, 500]),
            "volume_ml": random.choice([350, 450, 500]),
            "bag_type": random.choice(['Single', 'Double', 'Triple', 'Quadruple']),
            "bag_lot_number": f"BG-{random.randint(10000, 99999)}",
            "phlebotomist_id": random.choice(staff_ids),
            "phlebotomist_name": "Nurse Fatimah",
            "arm_used": random.choice(['left', 'right']),
            "needle_gauge": random.choice(['16G', '17G']),
            "venipuncture_attempts": random.choices([1, 2], weights=[90, 10])[0],
            "status": "completed",
            "adverse_reaction": random.choice([False, False, False, True]),
            "adverse_reaction_type": None,
            "adverse_reaction_details": "Mild dizziness, resolved with rest" if random.random() > 0.9 else None,
            "post_donation_care": "Refreshments provided, rested 15 minutes",
            "notes": f"Successful donation. Donor tolerated well.",
            "org_id": org_id,
            "created_at": donation_date.isoformat(),
            "created_by": random.choice(staff_ids),
            "updated_at": end_time.isoformat(),
        }
        donations.append(donation)
    
    await db.donations.insert_many(donations)
    print(f"   ✓ Created {len(donations)} donations (all completed)")
    
    # ========================================
    # 5. LAB TESTS (for each donation)
    # ========================================
    print("\n🧪 Creating Lab Tests...")
    lab_tests = []
    
    for donation in donations:
        test_date = datetime.fromisoformat(donation['created_at'].replace('Z', '+00:00')) + timedelta(hours=2)
        
        lab_test = {
            "id": str(uuid.uuid4()),
            "test_id": f"PDN-LAB-{donation['donation_id'].split('-')[-1]}",
            "donation_id": donation['id'],
            "donor_id": donation['donor_id'],
            "blood_unit_id": None,  # Will be linked later
            # Blood typing
            "blood_group_abo": donation['blood_group'][:-1] if donation['blood_group'][-1] in ['+', '-'] else donation['blood_group'],
            "blood_group_rh": '+' if '+' in donation['blood_group'] else '-',
            "blood_group_confirmed": donation['blood_group'],
            # Serology tests
            "hiv_elisa": "negative",
            "hiv_nat": "negative",
            "hbsag": "negative",
            "hbv_nat": "negative",
            "anti_hcv": "negative",
            "hcv_nat": "negative",
            "syphilis_rpr": "negative",
            "syphilis_tpha": "negative",
            "malaria_antigen": "negative",
            "htlv": "negative",
            # Antibody screening
            "antibody_screen": "negative",
            "antibody_identification": None,
            "crossmatch_compatible": True,
            "dat_result": "negative",
            # Results
            "overall_result": "pass",
            "test_date": test_date.strftime("%Y-%m-%d"),
            "test_time": test_date.strftime("%H:%M"),
            "tested_by": random.choice(staff_ids),
            "tested_by_name": "Lab Tech Siti",
            "verified_by": admin_id,
            "verified_by_name": "Dr. Ahmad",
            "verification_date": (test_date + timedelta(hours=1)).isoformat(),
            "status": "completed",
            "equipment_id": f"ANALYZER-{random.randint(1, 3)}",
            "reagent_lot": f"RG-{random.randint(1000, 9999)}",
            "notes": "All tests within normal parameters",
            "org_id": org_id,
            "created_at": test_date.isoformat(),
        }
        lab_tests.append(lab_test)
    
    await db.lab_tests.insert_many(lab_tests)
    print(f"   ✓ Created {len(lab_tests)} lab tests")
    
    # ========================================
    # 6. BLOOD UNITS & COMPONENTS
    # ========================================
    print("\n🏷️ Creating Blood Units & Components...")
    blood_units = []
    components = []
    
    for i, donation in enumerate(donations):
        collection_date = datetime.fromisoformat(donation['created_at'].replace('Z', '+00:00'))
        
        unit_id = f"PDN-BU-{donation['donation_id'].split('-')[-1]}"
        blood_unit = {
            "id": str(uuid.uuid4()),
            "unit_id": unit_id,
            "donation_id": donation['id'],
            "donor_id": donation['donor_id'],
            "blood_group": donation['blood_group'],
            "volume": donation['volume_collected'],
            "collection_date": collection_date.strftime("%Y-%m-%d"),
            "expiry_date": (collection_date + timedelta(days=42)).strftime("%Y-%m-%d"),
            "status": "processed",
            "bag_barcode": f"BC{random.randint(100000000, 999999999)}",
            "sample_labels": [f"{unit_id}-S1", f"{unit_id}-S2", f"{unit_id}-S3"],
            "storage_location": f"REF-{random.choice(['A', 'B', 'C'])}-{random.randint(1, 5)}",
            "temperature_log": [{"temp": round(random.uniform(2, 6), 1), "time": collection_date.isoformat()}],
            "qc_status": "passed",
            "org_id": org_id,
            "created_at": collection_date.isoformat(),
            "created_by": random.choice(staff_ids),
        }
        blood_units.append(blood_unit)
        
        # Create 2-4 components per unit
        comp_types = random.sample(COMPONENT_TYPES, random.randint(2, 4))
        for j, comp_type in enumerate(comp_types):
            comp_expiry = collection_date + timedelta(days=42)
            if comp_type == 'platelets':
                comp_expiry = collection_date + timedelta(days=5)
            elif comp_type in ['ffp', 'cryoprecipitate']:
                comp_expiry = collection_date + timedelta(days=365)
            
            status = random.choices(['available', 'reserved', 'issued', 'quarantine'], weights=[50, 25, 20, 5])[0]
            
            component = {
                "id": str(uuid.uuid4()),
                "component_id": f"PDN-CMP-{donation['donation_id'].split('-')[-1]}-{j+1}",
                "blood_unit_id": blood_unit['id'],
                "donation_id": donation['id'],
                "donor_id": donation['donor_id'],
                "component_type": comp_type,
                "component_name": comp_type.upper().replace('_', ' '),
                "blood_group": donation['blood_group'],
                "volume_ml": random.randint(150, 350),
                "collection_date": collection_date.strftime("%Y-%m-%d"),
                "processing_date": (collection_date + timedelta(hours=4)).strftime("%Y-%m-%d"),
                "expiry_date": comp_expiry.strftime("%Y-%m-%d"),
                "expiry_time": "23:59",
                "status": status,
                "storage_location": f"STORAGE-{comp_type[:3].upper()}-{random.randint(1, 10)}",
                "storage_temperature": round(random.uniform(-30, 6), 1) if comp_type in ['ffp', 'cryoprecipitate'] else round(random.uniform(2, 6), 1),
                "qc_status": "passed",
                "qc_date": (collection_date + timedelta(hours=6)).strftime("%Y-%m-%d"),
                "barcode": f"CMP{random.randint(100000000, 999999999)}",
                "irradiated": random.choice([True, False]) if comp_type == 'prc' else False,
                "leukoreduced": random.choice([True, False]),
                "washed": False,
                "special_testing": None,
                "issued_to": f"Hospital {random.choice(['KL', 'Selayang', 'Sungai Buloh'])}" if status == 'issued' else None,
                "issued_date": (collection_date + timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d") if status == 'issued' else None,
                "issued_by": random.choice(staff_ids) if status == 'issued' else None,
                "notes": None,
                "org_id": org_id,
                "created_at": collection_date.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            components.append(component)
    
    await db.blood_units.insert_many(blood_units)
    await db.components.insert_many(components)
    print(f"   ✓ Created {len(blood_units)} blood units")
    print(f"   ✓ Created {len(components)} components")
    
    # ========================================
    # 7. QC RECORDS
    # ========================================
    print("\n✅ Creating QC Records...")
    qc_records = []
    
    for component in components[:15]:
        qc_date = datetime.fromisoformat(component['created_at'].replace('Z', '+00:00')) + timedelta(hours=6)
        
        qc_record = {
            "id": str(uuid.uuid4()),
            "qc_id": f"PDN-QC-{random.randint(10000, 99999)}",
            "component_id": component['id'],
            "component_type": component['component_type'],
            "blood_group": component['blood_group'],
            "qc_date": qc_date.strftime("%Y-%m-%d"),
            "qc_time": qc_date.strftime("%H:%M"),
            # Visual inspection
            "visual_inspection": "pass",
            "color": "normal",
            "turbidity": "clear",
            "clots_present": False,
            "bag_integrity": "intact",
            "label_verification": "verified",
            # Volume check
            "volume_ml": component['volume_ml'],
            "volume_within_spec": True,
            # Sterility
            "sterility_test": "negative",
            "bacterial_contamination": "negative",
            # Component-specific tests
            "platelet_count": random.randint(200, 400) * 1000 if component['component_type'] == 'platelets' else None,
            "wbc_count": random.randint(1, 5) * 1000 if component['component_type'] in ['prc', 'whole_blood'] else None,
            "hematocrit": random.randint(55, 80) if component['component_type'] == 'prc' else None,
            "ph_level": round(random.uniform(6.4, 7.4), 1) if component['component_type'] == 'platelets' else None,
            "factor_viii": random.randint(70, 150) if component['component_type'] == 'cryoprecipitate' else None,
            "fibrinogen": random.randint(150, 400) if component['component_type'] == 'cryoprecipitate' else None,
            # Results
            "overall_result": "pass",
            "performed_by": random.choice(staff_ids),
            "performed_by_name": "Lab Tech Siti",
            "verified_by": admin_id,
            "notes": "QC parameters within acceptable limits",
            "org_id": org_id,
            "created_at": qc_date.isoformat(),
        }
        qc_records.append(qc_record)
    
    await db.qc_records.insert_many(qc_records)
    print(f"   ✓ Created {len(qc_records)} QC records")
    
    # ========================================
    # 8. STORAGE LOCATIONS
    # ========================================
    print("\n🗄️ Creating Storage Locations...")
    storage_locations = [
        {"id": str(uuid.uuid4()), "name": "Refrigerator A", "code": "REF-A", "type": "refrigerator", "temperature_min": 2, "temperature_max": 6, "current_temperature": 4.2, "capacity": 500, "current_count": 120, "status": "active", "location": "Blood Bank Floor 1", "org_id": org_id},
        {"id": str(uuid.uuid4()), "name": "Refrigerator B", "code": "REF-B", "type": "refrigerator", "temperature_min": 2, "temperature_max": 6, "current_temperature": 3.8, "capacity": 500, "current_count": 95, "status": "active", "location": "Blood Bank Floor 1", "org_id": org_id},
        {"id": str(uuid.uuid4()), "name": "Freezer Unit 1", "code": "FRZ-1", "type": "freezer", "temperature_min": -30, "temperature_max": -18, "current_temperature": -25.5, "capacity": 300, "current_count": 180, "status": "active", "location": "Blood Bank Floor 2", "org_id": org_id},
        {"id": str(uuid.uuid4()), "name": "Freezer Unit 2", "code": "FRZ-2", "type": "freezer", "temperature_min": -30, "temperature_max": -18, "current_temperature": -24.0, "capacity": 300, "current_count": 145, "status": "active", "location": "Blood Bank Floor 2", "org_id": org_id},
        {"id": str(uuid.uuid4()), "name": "Platelet Incubator", "code": "PLT-INC", "type": "incubator", "temperature_min": 20, "temperature_max": 24, "current_temperature": 22.0, "capacity": 100, "current_count": 35, "status": "active", "location": "Blood Bank Floor 1", "org_id": org_id},
        {"id": str(uuid.uuid4()), "name": "Quarantine Storage", "code": "QUA-1", "type": "quarantine", "temperature_min": 2, "temperature_max": 6, "current_temperature": 4.0, "capacity": 50, "current_count": 8, "status": "active", "location": "Blood Bank Floor 2", "org_id": org_id},
    ]
    
    await db.storage_locations.insert_many(storage_locations)
    print(f"   ✓ Created {len(storage_locations)} storage locations")
    
    # ========================================
    # 9. BLOOD REQUESTS
    # ========================================
    print("\n📝 Creating Blood Requests...")
    blood_requests = []
    statuses = ['pending', 'approved', 'processing', 'fulfilled', 'cancelled']
    
    for i in range(10):
        req_date = random_date(0, 14)
        hospital = random.choice(HOSPITALS)
        
        request = {
            "id": str(uuid.uuid4()),
            "request_id": f"PDN-REQ-{2024001 + i}",
            "request_type": random.choice(['routine', 'urgent', 'emergency']),
            "requester_name": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "requester_contact": generate_phone(),
            "requester_email": f"doctor{i+1}@{hospital.lower().replace(' ', '')}.gov.my",
            "hospital_name": hospital,
            "hospital_address": f"Jalan Hospital, {random.choice(CITIES)['city']}",
            "department": random.choice(['Surgery', 'ICU', 'Emergency', 'Oncology', 'Obstetrics', 'Pediatrics']),
            "ward": f"Ward {random.randint(1, 20)}",
            "patient_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "patient_id": f"MRN-{random.randint(100000, 999999)}",
            "patient_age": random.randint(1, 85),
            "patient_gender": random.choice(['male', 'female']),
            "patient_diagnosis": random.choice(['Anemia', 'Surgery', 'Trauma', 'Cancer Treatment', 'Delivery', 'GI Bleeding', 'Thalassemia']),
            "blood_group": random.choice(BLOOD_GROUPS),
            "product_type": random.choice(COMPONENT_TYPES),
            "quantity": random.randint(1, 6),
            "urgency": random.choice(['routine', 'urgent', 'stat']),
            "status": random.choice(statuses),
            "requested_date": req_date.strftime("%Y-%m-%d"),
            "required_by_date": (req_date + timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d"),
            "required_by_time": f"{random.randint(8, 18):02d}:00",
            "approved_by": admin_id if random.random() > 0.3 else None,
            "approved_date": (req_date + timedelta(hours=random.randint(1, 4))).isoformat() if random.random() > 0.3 else None,
            "fulfilled_date": (req_date + timedelta(days=1)).isoformat() if random.random() > 0.5 else None,
            "crossmatch_required": True,
            "special_requirements": random.choice([None, "CMV Negative", "Irradiated", "Leukoreduced"]),
            "clinical_notes": f"Patient requires blood for {random.choice(['surgery', 'transfusion', 'treatment'])}",
            "notes": None,
            "org_id": org_id,
            "created_at": req_date.isoformat(),
            "created_by": admin_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        blood_requests.append(request)
    
    await db.blood_requests.insert_many(blood_requests)
    print(f"   ✓ Created {len(blood_requests)} blood requests")
    
    # ========================================
    # 10. REQUESTORS (Hospitals)
    # ========================================
    print("\n🏥 Creating Requestors...")
    requestors = []
    
    for i, hospital in enumerate(HOSPITALS[:5]):
        city = random.choice(CITIES)
        status = random.choices(['approved', 'pending', 'rejected'], weights=[60, 30, 10])[0]
        
        requestor = {
            "id": str(uuid.uuid4()),
            "organization_name": hospital,
            "organization_type": random.choice(['hospital', 'clinic']),
            "registration_number": f"MOH-{random.randint(10000, 99999)}",
            "license_number": f"HOS-{random.randint(1000, 9999)}",
            "contact_person": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "designation": random.choice(['Medical Director', 'Blood Bank Manager', 'Administrator']),
            "email": f"bloodbank@{hospital.lower().replace(' ', '')}.gov.my",
            "phone": generate_phone(),
            "fax": f"+60-3-{random.randint(1000, 9999)}{random.randint(1000, 9999)}",
            "address": f"Jalan {random.choice(['Hospital', 'Perubatan', 'Kesihatan'])} {random.randint(1, 20)}",
            "city": city['city'],
            "state": city['state'],
            "pincode": f"{random.randint(40000, 81000)}",
            "country": "Malaysia",
            "latitude": city['lat'] + random.uniform(-0.01, 0.01),
            "longitude": city['lng'] + random.uniform(-0.01, 0.01),
            "status": status,
            "password_hash": pwd_context.hash("Hospital@123"),
            "mou_signed": status == 'approved',
            "mou_date": random_date_str(30, 365) if status == 'approved' else None,
            "approved_by": admin_id if status == 'approved' else None,
            "approved_at": random_datetime_str(1, 30) if status == 'approved' else None,
            "rejection_reason": "Incomplete documentation" if status == 'rejected' else None,
            "notes": None,
            "created_at": random_datetime_str(30, 180),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        requestors.append(requestor)
    
    await db.requestors.insert_many(requestors)
    print(f"   ✓ Created {len(requestors)} requestors")
    
    # ========================================
    # 11. BROADCASTS
    # ========================================
    print("\n📢 Creating Broadcasts...")
    broadcasts = []
    broadcast_types = ['urgent_need', 'surplus_alert', 'urgent_need', 'announcement', 'surplus_alert']
    
    for i, btype in enumerate(broadcast_types):
        broadcast = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "org_name": organization['org_name'],
            "broadcast_type": btype,
            "blood_group": random.choice(BLOOD_GROUPS) if btype != 'announcement' else None,
            "component_type": random.choice(COMPONENT_TYPES) if btype != 'announcement' else None,
            "units_needed": random.randint(5, 20) if btype == 'urgent_need' else None,
            "units_available": random.randint(10, 50) if btype == 'surplus_alert' else None,
            "priority": random.choice(['normal', 'high', 'critical']),
            "title": f"{'URGENT: Blood Needed' if btype == 'urgent_need' else 'Surplus Available' if btype == 'surplus_alert' else 'Announcement'}",
            "description": f"{'Critical shortage of blood. Please donate.' if btype == 'urgent_need' else 'We have surplus units available for transfer.' if btype == 'surplus_alert' else 'Blood donation drive next week.'}",
            "contact_name": "Dr. Ahmad",
            "contact_phone": organization['contact_phone'],
            "visibility": "network_wide",
            "status": "active",
            "response_count": random.randint(0, 10),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=random.randint(24, 72))).isoformat(),
            "created_by": admin_id,
            "created_at": random_datetime_str(0, 5),
        }
        broadcasts.append(broadcast)
    
    await db.broadcasts.insert_many(broadcasts)
    print(f"   ✓ Created {len(broadcasts)} broadcasts")
    
    # ========================================
    # 12. INTER-ORG REQUESTS
    # ========================================
    print("\n🔄 Creating Inter-Org Requests...")
    inter_org_requests = []
    
    for i in range(5):
        req = {
            "id": str(uuid.uuid4()),
            "request_type": random.choice(['internal', 'external']),
            "requesting_org_id": org_id,
            "requesting_org_name": organization['org_name'],
            "fulfilling_org_id": org_id,
            "fulfilling_org_name": organization['org_name'],
            "component_type": random.choice(COMPONENT_TYPES),
            "blood_group": random.choice(BLOOD_GROUPS),
            "quantity": random.randint(1, 10),
            "urgency_level": random.choice(['routine', 'urgent', 'emergency']),
            "clinical_indication": f"Patient: {random.choice(FIRST_NAMES)} - {random.choice(['Surgery', 'Trauma', 'Transfusion', 'Cancer Treatment'])}",
            "status": random.choice(['pending', 'approved', 'dispatched', 'delivered', 'cancelled']),
            "required_by": (datetime.now(timezone.utc) + timedelta(days=random.randint(0, 3))).isoformat(),
            "approved_by": admin_id if random.random() > 0.3 else None,
            "approved_at": random_datetime_str(0, 2) if random.random() > 0.3 else None,
            "dispatched_at": random_datetime_str(0, 1) if random.random() > 0.5 else None,
            "delivered_at": random_datetime_str(0, 1) if random.random() > 0.6 else None,
            "notes": None,
            "created_by": admin_id,
            "created_at": random_datetime_str(0, 7),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        inter_org_requests.append(req)
    
    await db.inter_org_requests.insert_many(inter_org_requests)
    print(f"   ✓ Created {len(inter_org_requests)} inter-org requests")
    
    # ========================================
    # 13. LOGISTICS ORDERS
    # ========================================
    print("\n🚚 Creating Logistics Orders...")
    logistics_orders = []
    
    for i in range(5):
        order_date = random_date(0, 10)
        logistics_order = {
            "id": str(uuid.uuid4()),
            "order_id": f"PDN-LOG-{2024001 + i}",
            "order_type": random.choice(['delivery', 'pickup', 'transfer']),
            "source_org_id": org_id,
            "source_org_name": organization['org_name'],
            "source_address": organization['address'],
            "destination_org_id": org_id,
            "destination_org_name": random.choice(HOSPITALS),
            "destination_address": f"Jalan Hospital, {random.choice(CITIES)['city']}",
            "component_ids": [random.choice(components)['id']],
            "component_count": random.randint(1, 5),
            "blood_groups": [random.choice(BLOOD_GROUPS)],
            "priority": random.choice(['normal', 'urgent', 'stat']),
            "status": random.choice(['pending', 'assigned', 'in_transit', 'delivered', 'cancelled']),
            "scheduled_pickup": order_date.isoformat(),
            "scheduled_delivery": (order_date + timedelta(hours=2)).isoformat(),
            "actual_pickup": (order_date + timedelta(minutes=15)).isoformat() if random.random() > 0.3 else None,
            "actual_delivery": (order_date + timedelta(hours=2, minutes=30)).isoformat() if random.random() > 0.4 else None,
            "driver_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" if random.random() > 0.3 else None,
            "driver_phone": generate_phone() if random.random() > 0.3 else None,
            "vehicle_number": f"W{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1000, 9999)}" if random.random() > 0.3 else None,
            "temperature_maintained": True,
            "temperature_log": [{"temp": round(random.uniform(2, 6), 1), "time": order_date.isoformat()}],
            "special_instructions": random.choice([None, "Handle with care", "Urgent delivery", "Keep refrigerated"]),
            "notes": None,
            "created_by": admin_id,
            "org_id": org_id,
            "created_at": order_date.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        logistics_orders.append(logistics_order)
    
    await db.logistics_orders.insert_many(logistics_orders)
    print(f"   ✓ Created {len(logistics_orders)} logistics orders")
    
    # ========================================
    # 14. DISPOSAL RECORDS
    # ========================================
    print("\n🗑️ Creating Disposal Records...")
    disposal_records = []
    disposal_reasons = ['expired', 'contaminated', 'damaged', 'qc_failed', 'unused_returned']
    
    for i in range(5):
        disposal_date = random_date(1, 30)
        disposal_record = {
            "id": str(uuid.uuid4()),
            "disposal_id": f"PDN-DIS-{2024001 + i}",
            "component_id": random.choice(components)['id'] if components else None,
            "component_type": random.choice(COMPONENT_TYPES),
            "blood_group": random.choice(BLOOD_GROUPS),
            "volume_ml": random.randint(150, 450),
            "disposal_reason": random.choice(disposal_reasons),
            "disposal_method": random.choice(['incineration', 'autoclave', 'chemical_treatment']),
            "disposal_date": disposal_date.strftime("%Y-%m-%d"),
            "disposal_time": disposal_date.strftime("%H:%M"),
            "disposed_by": random.choice(staff_ids),
            "disposed_by_name": "Ali Rahman",
            "witnessed_by": admin_id,
            "witnessed_by_name": "Dr. Ahmad",
            "certificate_number": f"DISP-CERT-{random.randint(10000, 99999)}",
            "notes": f"Disposed due to {random.choice(disposal_reasons)}",
            "org_id": org_id,
            "created_at": disposal_date.isoformat(),
        }
        disposal_records.append(disposal_record)
    
    await db.disposal_records.insert_many(disposal_records)
    print(f"   ✓ Created {len(disposal_records)} disposal records")
    
    # ========================================
    # 15. QUARANTINE RECORDS
    # ========================================
    print("\n⚠️ Creating Quarantine Records...")
    quarantine_records = []
    quarantine_reasons = ['reactive_screening', 'donor_callback', 'qc_investigation', 'suspected_contamination']
    
    for i in range(3):
        quarantine_date = random_date(1, 20)
        quarantine_record = {
            "id": str(uuid.uuid4()),
            "quarantine_id": f"PDN-QUA-{2024001 + i}",
            "component_id": random.choice(components)['id'] if components else None,
            "component_type": random.choice(COMPONENT_TYPES),
            "blood_group": random.choice(BLOOD_GROUPS),
            "quarantine_reason": random.choice(quarantine_reasons),
            "quarantine_date": quarantine_date.strftime("%Y-%m-%d"),
            "quarantine_location": "Quarantine Storage",
            "status": random.choice(['quarantined', 'released', 'disposed']),
            "investigation_status": random.choice(['pending', 'in_progress', 'completed']),
            "investigation_notes": "Under investigation",
            "quarantined_by": random.choice(staff_ids),
            "quarantined_by_name": "Lab Tech Siti",
            "released_by": admin_id if random.random() > 0.5 else None,
            "released_date": (quarantine_date + timedelta(days=3)).isoformat() if random.random() > 0.5 else None,
            "release_notes": "Investigation complete, unit cleared" if random.random() > 0.5 else None,
            "org_id": org_id,
            "created_at": quarantine_date.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        quarantine_records.append(quarantine_record)
    
    await db.quarantine_records.insert_many(quarantine_records)
    print(f"   ✓ Created {len(quarantine_records)} quarantine records")
    
    # ========================================
    # 16. ALERTS
    # ========================================
    print("\n🔔 Creating Alerts...")
    alerts = []
    alert_types = ['low_inventory', 'expiring_soon', 'temperature_alert', 'equipment_maintenance', 'donor_callback']
    
    for i in range(8):
        alert_date = random_date(0, 7)
        alert = {
            "id": str(uuid.uuid4()),
            "alert_id": f"PDN-ALT-{2024001 + i}",
            "alert_type": random.choice(alert_types),
            "severity": random.choice(['low', 'medium', 'high', 'critical']),
            "title": f"Alert: {random.choice(['Low O- Stock', 'Units Expiring', 'Temperature Warning', 'Equipment Check Due', 'Donor Follow-up'])}",
            "message": "Please take necessary action.",
            "blood_group": random.choice(BLOOD_GROUPS) if random.random() > 0.3 else None,
            "component_type": random.choice(COMPONENT_TYPES) if random.random() > 0.3 else None,
            "threshold_value": random.randint(5, 20) if random.random() > 0.5 else None,
            "current_value": random.randint(1, 10) if random.random() > 0.5 else None,
            "status": random.choice(['active', 'acknowledged', 'resolved']),
            "acknowledged_by": admin_id if random.random() > 0.4 else None,
            "acknowledged_at": (alert_date + timedelta(hours=1)).isoformat() if random.random() > 0.4 else None,
            "resolved_by": admin_id if random.random() > 0.6 else None,
            "resolved_at": (alert_date + timedelta(hours=4)).isoformat() if random.random() > 0.6 else None,
            "resolution_notes": "Issue resolved" if random.random() > 0.6 else None,
            "org_id": org_id,
            "created_at": alert_date.isoformat(),
        }
        alerts.append(alert)
    
    await db.alerts.insert_many(alerts)
    print(f"   ✓ Created {len(alerts)} alerts")
    
    # ========================================
    # 17. TRAINING RECORDS
    # ========================================
    print("\n📚 Creating Training Records...")
    training_records = []
    training_types = ['phlebotomy', 'blood_safety', 'quality_control', 'emergency_response', 'infection_control', 'equipment_operation']
    
    for staff_id in staff_ids + [admin_id]:
        for _ in range(2):
            training_date = random_date(30, 365)
            training = {
                "id": str(uuid.uuid4()),
                "training_id": f"PDN-TRN-{random.randint(10000, 99999)}",
                "user_id": staff_id,
                "user_name": "Staff Member",
                "training_type": random.choice(training_types),
                "training_title": f"{random.choice(['Basic', 'Advanced', 'Refresher'])} {random.choice(training_types).replace('_', ' ').title()} Training",
                "training_provider": random.choice(['PDN Training Center', 'MOH Malaysia', 'External Consultant']),
                "training_date": training_date.strftime("%Y-%m-%d"),
                "training_duration_hours": random.choice([2, 4, 8, 16]),
                "training_location": random.choice(['On-site', 'Online', 'External']),
                "certificate_number": f"CERT-{random.randint(10000, 99999)}",
                "certificate_expiry": (training_date + timedelta(days=365)).strftime("%Y-%m-%d"),
                "score": random.randint(75, 100) if random.random() > 0.2 else None,
                "passed": True,
                "trainer_name": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "notes": "Training completed successfully",
                "org_id": org_id,
                "created_at": training_date.isoformat(),
            }
            training_records.append(training)
    
    await db.training_records.insert_many(training_records)
    print(f"   ✓ Created {len(training_records)} training records")
    
    # ========================================
    # 18. COMPLIANCE RECORDS
    # ========================================
    print("\n📋 Creating Compliance Records...")
    compliance_records = []
    compliance_types = ['audit', 'inspection', 'certification', 'license_renewal', 'quality_review']
    
    for i in range(5):
        compliance_date = random_date(30, 365)
        compliance = {
            "id": str(uuid.uuid4()),
            "compliance_id": f"PDN-CMP-{2024001 + i}",
            "compliance_type": random.choice(compliance_types),
            "title": f"{random.choice(['Annual', 'Quarterly', 'Monthly'])} {random.choice(compliance_types).replace('_', ' ').title()}",
            "description": "Compliance check completed",
            "conducted_by": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "conducted_date": compliance_date.strftime("%Y-%m-%d"),
            "result": random.choice(['pass', 'pass_with_observations', 'fail']),
            "score": random.randint(80, 100),
            "findings": random.choice([None, "Minor documentation issues", "All requirements met"]),
            "corrective_actions": random.choice([None, "Update SOPs", "Staff retraining"]),
            "next_review_date": (compliance_date + timedelta(days=random.choice([90, 180, 365]))).strftime("%Y-%m-%d"),
            "attachments": [],
            "verified_by": admin_id,
            "verified_at": (compliance_date + timedelta(days=1)).isoformat(),
            "notes": None,
            "org_id": org_id,
            "created_at": compliance_date.isoformat(),
        }
        compliance_records.append(compliance)
    
    await db.compliance_records.insert_many(compliance_records)
    print(f"   ✓ Created {len(compliance_records)} compliance records")
    
    # ========================================
    # 19. AUDIT LOGS
    # ========================================
    print("\n📝 Creating Audit Logs...")
    audit_logs = []
    audit_actions = [
        ("login", "auth", "User logged in successfully"),
        ("logout", "auth", "User logged out"),
        ("create", "donors", "New donor registered"),
        ("update", "donors", "Donor record updated"),
        ("create", "donations", "Blood donation recorded"),
        ("update", "donations", "Donation completed"),
        ("create", "components", "Component created"),
        ("update", "components", "Component status updated"),
        ("create", "requests", "Blood request created"),
        ("approve", "requests", "Blood request approved"),
        ("issue", "inventory", "Blood unit issued"),
        ("view", "reports", "Report generated"),
    ]
    
    for i in range(30):
        action, module, desc = random.choice(audit_actions)
        log_date = random_date(0, 30)
        
        log = {
            "id": str(uuid.uuid4()),
            "user_id": random.choice(staff_ids + [admin_id]),
            "user_email": random.choice(["admin@pdn.gov.my", "labtech@pdn.gov.my", "nurse@pdn.gov.my"]),
            "user_name": random.choice(["Dr. Ahmad", "Siti Aminah", "Nurse Fatimah"]),
            "user_type": random.choice(["super_admin", "staff"]),
            "action": action,
            "module": module,
            "description": desc,
            "resource_type": module,
            "resource_id": str(uuid.uuid4()),
            "ip_address": f"192.168.1.{random.randint(1, 255)}",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "session_id": str(uuid.uuid4()),
            "org_id": org_id,
            "created_at": log_date.isoformat(),
        }
        audit_logs.append(log)
    
    await db.audit_logs.insert_many(audit_logs)
    print(f"   ✓ Created {len(audit_logs)} audit logs")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("✅ COMPREHENSIVE DEMO DATA SEEDING COMPLETE!")
    print("=" * 60)
    print(f"""
Summary of created data:
------------------------
Organization & Users:
  • Organization:        1 (Pusat Darah Negara Malaysia)
  • Admin Users:         1
  • Staff Users:         3

Donor Management:
  • Donors:              {len(donors)}
  • Screenings:          {len(screenings)}

Blood Collection:
  • Donations:           {len(donations)} (all COMPLETED)
  • Lab Tests:           {len(lab_tests)}

Inventory:
  • Blood Units:         {len(blood_units)}
  • Components:          {len(components)}
  • QC Records:          {len(qc_records)}
  • Storage Locations:   {len(storage_locations)}

Requests & Distribution:
  • Blood Requests:      {len(blood_requests)}
  • Requestors:          {len(requestors)}
  • Inter-Org Requests:  {len(inter_org_requests)}
  • Logistics Orders:    {len(logistics_orders)}

Quality & Compliance:
  • Disposal Records:    {len(disposal_records)}
  • Quarantine Records:  {len(quarantine_records)}
  • Alerts:              {len(alerts)}
  • Training Records:    {len(training_records)}
  • Compliance Records:  {len(compliance_records)}
  • Audit Logs:          {len(audit_logs)}

Network:
  • Broadcasts:          {len(broadcasts)}

Test Credentials:
-----------------
Admin Login:
  Email: admin@pdn.gov.my
  Password: Admin@123

Staff Logins:
  Email: labtech@pdn.gov.my / nurse@pdn.gov.my / inventory@pdn.gov.my
  Password: Staff@123

Requestor Login:
  Email: bloodbank@hospitalkualalumpur.gov.my
  Password: Hospital@123
""")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
