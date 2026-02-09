"""
Comprehensive Demo Data Seeder for Blood Link
Creates data for ALL modules with both pending and completed states.
"""
import random
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from services.helpers import generate_barcode_base64

# Malaysian data constants
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
COMPONENT_TYPES = ['whole_blood', 'prc', 'ffp', 'platelets', 'cryoprecipitate']
FIRST_NAMES = ['Ahmad', 'Siti', 'Muhammad', 'Nur', 'Mohamed', 'Fatimah', 'Ali', 'Aishah', 'Hassan', 'Zainab', 
               'Raj', 'Priya', 'Lee', 'Wong', 'Tan', 'Lim', 'Kumar', 'Devi', 'Chen', 'Amir']
LAST_NAMES = ['Abdullah', 'Rahman', 'Hassan', 'Ibrahim', 'Ismail', 'Ahmad', 'Yusof', 'Omar', 'Zakaria', 'Ali',
              'Kumar', 'Singh', 'Tan', 'Lee', 'Wong', 'Lim', 'Chen', 'Ng', 'Krishnan', 'Muthu']
CITIES = [
    {'city': 'Kuala Lumpur', 'state': 'Wilayah Persekutuan', 'lat': 3.1390, 'lng': 101.6869},
    {'city': 'Petaling Jaya', 'state': 'Selangor', 'lat': 3.1073, 'lng': 101.6067},
    {'city': 'Shah Alam', 'state': 'Selangor', 'lat': 3.0733, 'lng': 101.5185},
    {'city': 'Johor Bahru', 'state': 'Johor', 'lat': 1.4927, 'lng': 103.7414},
    {'city': 'George Town', 'state': 'Penang', 'lat': 5.4141, 'lng': 100.3288},
]
HOSPITALS = ['Hospital Kuala Lumpur', 'Hospital Selayang', 'Hospital Sungai Buloh', 
             'Pusat Perubatan Universiti Malaya', 'Hospital Sultanah Aminah']

def hash_pw(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def gen_phone():
    return f"+60-{random.choice(['11', '12', '13', '14', '16', '17', '18', '19'])}-{random.randint(1000000, 9999999)}"

def gen_mykad():
    return f"{random.randint(70, 99):02d}{random.randint(1, 12):02d}{random.randint(1, 28):02d}-{random.randint(1, 14):02d}-{random.randint(1000, 9999)}"

def rand_date(days_min, days_max):
    days = random.randint(days_min, days_max)
    return datetime.now(timezone.utc) - timedelta(days=days)

def rand_date_str(days_min, days_max):
    return rand_date(days_min, days_max).strftime("%Y-%m-%d")

def rand_datetime_str(days_min, days_max):
    return rand_date(days_min, days_max).isoformat()

def gen_barcode(unit_id):
    """Generate base64 barcode image from unit ID"""
    try:
        return generate_barcode_base64(unit_id)
    except:
        return f"BC{random.randint(100000000, 999999999)}"  # Fallback to text


async def seed_comprehensive_demo_data(db, logger):
    """Seed complete demo data for all modules"""
    
    # Check if data exists
    donor_count = await db.donors.count_documents({})
    if donor_count > 0:
        logger.info(f"Demo data exists ({donor_count} donors). Skipping.")
        return
    
    logger.info("=" * 60)
    logger.info("SEEDING COMPREHENSIVE DEMO DATA")
    logger.info("=" * 60)
    
    try:
        # ============================================
        # 1. ORGANIZATION & USERS
        # ============================================
        org_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())
        city = CITIES[0]
        
        org = {
            "id": org_id,
            "org_name": "Pusat Darah Negara Malaysia",
            "org_type": "standalone",
            "is_parent": True,
            "address": "Jalan Tun Razak, 50400",
            "city": city['city'],
            "state": city['state'],
            "country": "Malaysia",
            "pincode": "50400",
            "latitude": city['lat'],
            "longitude": city['lng'],
            "location": {"type": "Point", "coordinates": [city['lng'], city['lat']]},
            "contact_person": "Dr. Ahmad bin Hassan",
            "contact_phone": "+60-3-26132688",
            "contact_email": "admin@pdn.gov.my",
            "license_number": "PDN-001-2024",
            "is_active": True,
            "is_24x7": True,
            "blood_link_visible": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.organizations.insert_one(org)
        await db.organizations.create_index([("location", "2dsphere")])
        
        # Admin user
        await db.users.insert_one({
            "id": admin_id,
            "email": "admin@pdn.gov.my",
            "password_hash": hash_pw("Admin@123"),
            "full_name": "Dr. Ahmad bin Hassan",
            "phone": "+60-3-26132688",
            "role": "admin",
            "user_type": "super_admin",
            "org_id": org_id,
            "org_name": org['org_name'],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        
        # Staff users
        staff_ids = []
        staff_data = [
            ("labtech@pdn.gov.my", "Siti Aminah binti Razak", "lab_tech"),
            ("nurse@pdn.gov.my", "Fatimah binti Omar", "registration"),
            ("inventory@pdn.gov.my", "Ali bin Rahman", "inventory"),
            ("distribution@pdn.gov.my", "Hassan bin Ibrahim", "distribution"),
        ]
        for email, name, role in staff_data:
            sid = str(uuid.uuid4())
            staff_ids.append(sid)
            await db.users.insert_one({
                "id": sid, "email": email, "password_hash": hash_pw("Staff@123"),
                "full_name": name, "phone": gen_phone(), "role": role,
                "user_type": "staff", "org_id": org_id, "org_name": org['org_name'],
                "is_active": True, "created_at": datetime.now(timezone.utc).isoformat(),
            })
        
        logger.info(f"✓ Created organization: {org['org_name']}")
        logger.info(f"✓ Created {len(staff_ids) + 1} users")
        
        # ============================================
        # 2. DONORS (30 with various statuses)
        # We create 30 donors to ensure we have enough for all demo scenarios:
        # - First 20: Eligible donors (will have screenings)
        # - Next 5: Eligible donors ready for collection (completed screening, no donation)
        # - Last 5: Various statuses (pending, deferred) for demo variety
        # ============================================
        donors = []
        
        # First 20 donors - eligible with past donations (> 56 days ago)
        for i in range(20):
            city = random.choice(CITIES)
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            
            donor = {
                "id": str(uuid.uuid4()),
                "donor_id": f"PDN-D-{2024001 + i}",
                "id_type": random.choice(['mykad', 'mykas', 'passport']),
                "id_number": gen_mykad(),
                "first_name": first,
                "last_name": last,
                "full_name": f"{first} {last}",
                "date_of_birth": f"{random.randint(1965, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "gender": random.choice(['male', 'female']),
                "blood_group": random.choice(BLOOD_GROUPS),
                "rh_factor": random.choice(['+', '-']),
                "phone": gen_phone(),
                "email": f"{first.lower()}.{last.lower()}{random.randint(10,99)}@email.com.my",
                "address": f"No. {random.randint(1, 200)}, Jalan {random.choice(['Merdeka', 'Ampang', 'Cheras', 'Bangsar'])} {random.randint(1, 30)}",
                "city": city['city'],
                "state": city['state'],
                "country": "Malaysia",
                "pincode": f"{random.randint(40000, 81000)}",
                "latitude": city['lat'] + random.uniform(-0.02, 0.02),
                "longitude": city['lng'] + random.uniform(-0.02, 0.02),
                "occupation": random.choice(['Engineer', 'Teacher', 'Doctor', 'Accountant', 'Business Owner']),
                "emergency_contact_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "emergency_contact_phone": gen_phone(),
                "status": "eligible",
                "is_active": True,
                "eligibility_status": "eligible",
                "donation_count": random.randint(1, 15),
                "total_donations": random.randint(1, 15),
                # Last donation was 60-365 days ago (> 56 days, so eligible)
                "last_donation_date": rand_date_str(60, 365),
                "medical_conditions": random.choice([None, None, None, "Controlled Hypertension"]),
                "allergies": random.choice([None, None, None, "Penicillin"]),
                "org_id": org_id,
                "created_at": rand_datetime_str(30, 180),
                "created_by": admin_id,
            }
            donors.append(donor)
        
        # Next 5 donors (indices 20-24) - READY FOR COLLECTION
        # These have NO last_donation_date (or very old) so they show as eligible
        for i in range(5):
            city = random.choice(CITIES)
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            
            donor = {
                "id": str(uuid.uuid4()),
                "donor_id": f"PDN-D-{2024021 + i}",
                "id_type": "mykad",
                "id_number": gen_mykad(),
                "first_name": first,
                "last_name": last,
                "full_name": f"{first} {last}",
                "date_of_birth": f"{random.randint(1975, 1995)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "gender": random.choice(['male', 'female']),
                "blood_group": random.choice(BLOOD_GROUPS),
                "rh_factor": random.choice(['+', '-']),
                "phone": gen_phone(),
                "email": f"{first.lower()}.{last.lower()}{random.randint(10,99)}@email.com.my",
                "address": f"No. {random.randint(1, 200)}, Jalan {random.choice(['Merdeka', 'Ampang', 'Cheras', 'Bangsar'])} {random.randint(1, 30)}",
                "city": city['city'],
                "state": city['state'],
                "country": "Malaysia",
                "pincode": f"{random.randint(40000, 81000)}",
                "latitude": city['lat'] + random.uniform(-0.02, 0.02),
                "longitude": city['lng'] + random.uniform(-0.02, 0.02),
                "occupation": random.choice(['Engineer', 'Teacher', 'Doctor', 'Accountant', 'Business Owner']),
                "emergency_contact_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "emergency_contact_phone": gen_phone(),
                "status": "eligible",
                "is_active": True,
                "eligibility_status": "eligible",
                "donation_count": 0,
                "total_donations": 0,
                # NO last_donation_date - these are new donors ready for first/next donation
                "last_donation_date": None,
                "medical_conditions": None,
                "allergies": None,
                "org_id": org_id,
                "created_at": rand_datetime_str(1, 7),  # Recent registration
                "created_by": admin_id,
            }
            donors.append(donor)
        
        # Last 5 donors (indices 25-29) - various non-eligible statuses for demo
        for i in range(5):
            city = random.choice(CITIES)
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            status = random.choice(['pending', 'deferred'])
            
            donor = {
                "id": str(uuid.uuid4()),
                "donor_id": f"PDN-D-{2024026 + i}",
                "id_type": random.choice(['mykad', 'passport']),
                "id_number": gen_mykad(),
                "first_name": first,
                "last_name": last,
                "full_name": f"{first} {last}",
                "date_of_birth": f"{random.randint(1970, 2005)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "gender": random.choice(['male', 'female']),
                "blood_group": random.choice(BLOOD_GROUPS),
                "rh_factor": random.choice(['+', '-']),
                "phone": gen_phone(),
                "email": f"{first.lower()}.{last.lower()}{random.randint(10,99)}@email.com.my",
                "address": f"No. {random.randint(1, 200)}, Jalan {random.choice(['Merdeka', 'Ampang', 'Cheras'])} {random.randint(1, 30)}",
                "city": city['city'],
                "state": city['state'],
                "country": "Malaysia",
                "pincode": f"{random.randint(40000, 81000)}",
                "latitude": city['lat'] + random.uniform(-0.02, 0.02),
                "longitude": city['lng'] + random.uniform(-0.02, 0.02),
                "occupation": random.choice(['Student', 'Retired', 'Homemaker']),
                "emergency_contact_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "emergency_contact_phone": gen_phone(),
                "status": status,
                "is_active": True,
                "eligibility_status": "pending" if status == "pending" else "deferred",
                "donation_count": 0,
                "total_donations": 0,
                "last_donation_date": None,
                "medical_conditions": "Under evaluation" if status == "pending" else "Temporary medical condition",
                "allergies": None,
                "org_id": org_id,
                "created_at": rand_datetime_str(1, 30),
                "created_by": admin_id,
            }
            donors.append(donor)
        
        await db.donors.insert_many(donors)
        logger.info(f"✓ Created {len(donors)} donors (20 with past donations, 5 ready for collection, 5 pending/deferred)")
        
        # ============================================
        # 3. SCREENINGS - Create for donors who need them
        # Structure:
        # - Donors 0-11: Completed screening + completed donation (past)
        # - Donors 12-14: Completed screening + in-progress donation
        # - Donors 15-19: Completed screening (past, but eligible for new donation)
        # - Donors 20-24: Completed screening TODAY - READY FOR COLLECTION (no donation yet)
        # - Donors 25-29: Pending screening (demo pending status)
        # ============================================
        screenings = []
        
        # Screenings for donors 0-19 (past screenings with completed eligibility)
        for i in range(20):
            donor = donors[i]
            scr_date = rand_date(60, 120)  # 60-120 days ago (old enough)
            
            screening = {
                "id": str(uuid.uuid4()),
                "screening_id": f"PDN-SCR-{2024001 + i}",
                "donor_id": donor['id'],
                "donor_name": donor['full_name'],
                "blood_group": donor['blood_group'],
                "screening_date": scr_date.strftime("%Y-%m-%d"),
                "screening_time": f"{random.randint(8, 16):02d}:{random.randint(0, 59):02d}",
                # Vital signs - all within normal range
                "hemoglobin": round(random.uniform(13.0, 16.0), 1),
                "hemoglobin_unit": "g/dL",
                "blood_pressure_systolic": random.randint(100, 130),
                "blood_pressure_diastolic": random.randint(65, 85),
                "pulse": random.randint(60, 90),
                "temperature": round(random.uniform(36.2, 37.0), 1),
                "weight_kg": round(random.uniform(55, 85), 1),
                "height_cm": random.randint(155, 180),
                # Blood typing
                "preliminary_blood_group": donor['blood_group'],
                "preliminary_rh": '+' if '+' in donor['blood_group'] else '-',
                # Questionnaire - all passed
                "questionnaire_completed": True,
                "questionnaire_passed": True,
                "recent_illness": False,
                "recent_travel": False,
                "recent_surgery": False,
                "recent_tattoo": False,
                "high_risk_behavior": False,
                # Status - COMPLETED and ELIGIBLE
                "status": "completed",
                "eligibility_status": "eligible",
                "eligibility_reason": None,
                "screened_by": random.choice(staff_ids),
                "screened_by_name": "Nurse Fatimah",
                "verified_by": admin_id,
                "verified_at": scr_date.isoformat(),
                "notes": "Donor cleared for donation",
                "org_id": org_id,
                "created_at": scr_date.isoformat(),
            }
            screenings.append(screening)
        
        # Screenings for donors 20-24: READY FOR COLLECTION (recent screening, no donation)
        for i in range(5):
            donor = donors[20 + i]
            scr_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 6))  # Today, few hours ago
            
            screening = {
                "id": str(uuid.uuid4()),
                "screening_id": f"PDN-SCR-{2024021 + i}",
                "donor_id": donor['id'],
                "donor_name": donor['full_name'],
                "blood_group": donor['blood_group'],
                "screening_date": scr_date.strftime("%Y-%m-%d"),
                "screening_time": scr_date.strftime("%H:%M"),
                # Vital signs - all within normal range (these will be collected)
                "hemoglobin": round(random.uniform(13.5, 15.5), 1),
                "hemoglobin_unit": "g/dL",
                "blood_pressure_systolic": random.randint(105, 125),
                "blood_pressure_diastolic": random.randint(68, 82),
                "pulse": random.randint(65, 85),
                "temperature": round(random.uniform(36.3, 36.8), 1),
                "weight_kg": round(random.uniform(55, 80), 1),
                "height_cm": random.randint(158, 178),
                # Blood typing
                "preliminary_blood_group": donor['blood_group'],
                "preliminary_rh": '+' if '+' in donor['blood_group'] else '-',
                # Questionnaire - all passed
                "questionnaire_completed": True,
                "questionnaire_passed": True,
                "recent_illness": False,
                "recent_travel": False,
                "recent_surgery": False,
                "recent_tattoo": False,
                "high_risk_behavior": False,
                # Status - COMPLETED and ELIGIBLE (ready for collection!)
                "status": "completed",
                "eligibility_status": "eligible",
                "eligibility_reason": None,
                "screened_by": random.choice(staff_ids),
                "screened_by_name": "Nurse Fatimah",
                "verified_by": admin_id,
                "verified_at": scr_date.isoformat(),
                "notes": "Donor screened and cleared - ready for blood collection",
                "org_id": org_id,
                "created_at": scr_date.isoformat(),
            }
            screenings.append(screening)
        
        # Screenings for donors 25-29: PENDING (awaiting review for demo)
        for i in range(5):
            donor = donors[25 + i]
            scr_date = rand_date(0, 3)  # Recent
            
            screening = {
                "id": str(uuid.uuid4()),
                "screening_id": f"PDN-SCR-{2024026 + i}",
                "donor_id": donor['id'],
                "donor_name": donor['full_name'],
                "blood_group": donor['blood_group'],
                "screening_date": scr_date.strftime("%Y-%m-%d"),
                "screening_time": f"{random.randint(9, 15):02d}:{random.randint(0, 59):02d}",
                # Vital signs - some may be borderline
                "hemoglobin": round(random.uniform(11.5, 14.0), 1),
                "hemoglobin_unit": "g/dL",
                "blood_pressure_systolic": random.randint(95, 145),
                "blood_pressure_diastolic": random.randint(60, 95),
                "pulse": random.randint(55, 105),
                "temperature": round(random.uniform(36.0, 37.3), 1),
                "weight_kg": round(random.uniform(48, 90), 1),
                "height_cm": random.randint(150, 185),
                # Blood typing
                "preliminary_blood_group": donor['blood_group'],
                "preliminary_rh": '+' if '+' in donor['blood_group'] else '-',
                # Questionnaire - needs review
                "questionnaire_completed": True,
                "questionnaire_passed": None,  # Pending review
                "recent_illness": random.choice([False, True]),
                "recent_travel": random.choice([False, True]),
                "recent_surgery": False,
                "recent_tattoo": False,
                "high_risk_behavior": False,
                # Status - PENDING
                "status": "pending",
                "eligibility_status": "pending",
                "eligibility_reason": "Awaiting physician review",
                "screened_by": random.choice(staff_ids),
                "screened_by_name": "Nurse Fatimah",
                "verified_by": None,
                "verified_at": None,
                "notes": "Pending medical officer review",
                "org_id": org_id,
                "created_at": scr_date.isoformat(),
            }
            screenings.append(screening)
        
        await db.screenings.insert_many(screenings)
        logger.info(f"✓ Created {len(screenings)} screenings:")
        logger.info(f"  → 20 completed (past donations)")
        logger.info(f"  → 5 completed TODAY - READY FOR COLLECTION")
        logger.info(f"  → 5 pending (awaiting review)")
        
        # ============================================
        # 4. DONATIONS - Create for donors with completed screenings
        # Structure:
        # - Donors 0-11: COMPLETED donations (past, successful)
        # - Donors 12-14: IN_PROGRESS donations (currently being collected)
        # - Donors 15-19: NO donations (old screenings, eligible for new cycle)
        # - Donors 20-24: NO donations - THESE ARE READY FOR COLLECTION
        # ============================================
        donations = []
        
        # Completed donations for donors 0-11 (matching their old screenings)
        for i in range(12):
            screening = screenings[i]
            donor = donors[i]
            don_date = datetime.fromisoformat(screening['created_at'].replace('Z', '+00:00')) + timedelta(minutes=30)
            
            donation = {
                "id": str(uuid.uuid4()),
                "donation_id": f"PDN-DON-{2024001 + i}",
                "donor_id": donor['id'],
                "donor_name": donor['full_name'],
                "screening_id": screening['id'],
                "blood_group": donor['blood_group'],
                "donation_type": random.choice(['whole_blood', 'apheresis_platelet', 'apheresis_plasma']),
                "donation_date": don_date.strftime("%Y-%m-%d"),
                "donation_time": don_date.strftime("%H:%M"),
                "collection_start_time": don_date.isoformat(),
                "collection_end_time": (don_date + timedelta(minutes=12)).isoformat(),
                "volume_collected": random.choice([350, 450, 500]),
                "volume_ml": random.choice([350, 450, 500]),
                "bag_type": random.choice(['Single', 'Double', 'Triple', 'Quadruple']),
                "bag_lot_number": f"BG-{random.randint(10000, 99999)}",
                "phlebotomist_id": random.choice(staff_ids),
                "phlebotomist_name": "Nurse Fatimah",
                "arm_used": random.choice(['left', 'right']),
                "needle_gauge": random.choice(['16G', '17G']),
                "venipuncture_attempts": 1,
                "status": "completed",
                "adverse_reaction": False,
                "adverse_reaction_details": None,
                "post_donation_care": "Refreshments provided, rested 15 minutes",
                "notes": "Successful donation - donor tolerated well",
                "org_id": org_id,
                "created_at": don_date.isoformat(),
                "created_by": random.choice(staff_ids),
            }
            donations.append(donation)
        
        # In-progress donations for donors 12-14 (recent)
        for i in range(3):
            screening = screenings[12 + i]
            donor = donors[12 + i]
            don_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 3))
            
            donation = {
                "id": str(uuid.uuid4()),
                "donation_id": f"PDN-DON-{2024013 + i}",
                "donor_id": donor['id'],
                "donor_name": donor['full_name'],
                "screening_id": screening['id'],
                "blood_group": donor['blood_group'],
                "donation_type": "whole_blood",
                "donation_date": don_date.strftime("%Y-%m-%d"),
                "donation_time": don_date.strftime("%H:%M"),
                "collection_start_time": don_date.isoformat(),
                "collection_end_time": None,
                "volume_collected": None,
                "volume_ml": None,
                "bag_type": random.choice(['Double', 'Triple']),
                "bag_lot_number": f"BG-{random.randint(10000, 99999)}",
                "phlebotomist_id": random.choice(staff_ids),
                "phlebotomist_name": "Nurse Fatimah",
                "arm_used": random.choice(['left', 'right']),
                "needle_gauge": "16G",
                "venipuncture_attempts": 1,
                "status": "in_progress",
                "adverse_reaction": False,
                "notes": "Collection in progress - awaiting completion",
                "org_id": org_id,
                "created_at": don_date.isoformat(),
                "created_by": random.choice(staff_ids),
            }
            donations.append(donation)
        
        # NOTE: Donors 15-19 have old screenings but no donation for that screening
        # NOTE: Donors 20-24 have TODAY's completed screenings and NO donations - READY FOR COLLECTION!
        
        await db.donations.insert_many(donations)
        logger.info(f"✓ Created {len(donations)} donations:")
        logger.info(f"  → 12 completed (past)")
        logger.info(f"  → 3 in_progress (ongoing)")
        logger.info(f"  → 5 donors (20-24) with completed screenings READY FOR COLLECTION")
        
        # ============================================
        # 5. LAB TESTS (20 - mix of completed, pending & in_progress)
        # Structure:
        # - 10 completed (all tests passed)
        # - 5 in_progress (some tests done, some pending)
        # - 5 pending (awaiting testing)
        # ============================================
        lab_tests = []
        completed_donations = [d for d in donations if d['status'] == 'completed']
        
        # 10 Completed lab tests
        for i, donation in enumerate(completed_donations[:10]):
            test_date = datetime.fromisoformat(donation['created_at'].replace('Z', '+00:00')) + timedelta(hours=2)
            
            lab_test = {
                "id": str(uuid.uuid4()),
                "test_id": f"PDN-LAB-{2024001 + i}",
                "donation_id": donation['id'],
                "donor_id": donation['donor_id'],
                "donor_name": donation['donor_name'],
                "blood_unit_id": None,
                "unit_id": f"PDN-BU-{2024001 + i}",  # Reference matching blood unit
                # Blood typing
                "blood_group_abo": donation['blood_group'][:-1] if donation['blood_group'][-1] in ['+', '-'] else donation['blood_group'],
                "blood_group_rh": '+' if '+' in donation['blood_group'] else '-',
                "blood_group_confirmed": donation['blood_group'],
                "confirmed_blood_group": donation['blood_group'],  # Frontend expects this field
                # Serology - all negative (passed) - with FRONTEND-EXPECTED field names
                "hiv_result": "non_reactive",
                "hbsag_result": "non_reactive",
                "hcv_result": "non_reactive",
                "syphilis_result": "non_reactive",
                # Extended serology fields
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
                # Antibody
                "antibody_screen": "negative",
                "crossmatch_compatible": True,
                "dat_result": "negative",
                # Results
                "overall_result": "pass",
                "overall_status": "non_reactive",  # Frontend expects this field
                "test_date": test_date.strftime("%Y-%m-%d"),
                "test_time": test_date.strftime("%H:%M"),
                "tested_by": random.choice(staff_ids),
                "tested_by_name": "Lab Tech Siti",
                "verified_by": admin_id,
                "verified_by_name": "Dr. Ahmad",
                "status": "completed",
                "equipment_id": f"ANALYZER-{random.randint(1, 3)}",
                "reagent_lot": f"RG-{random.randint(1000, 9999)}",
                "notes": "All tests passed - cleared for processing",
                "org_id": org_id,
                "created_at": test_date.isoformat(),
            }
            lab_tests.append(lab_test)
        
        # 5 In-Progress lab tests (some tests done, awaiting remaining)
        for i in range(5):
            if i + 10 < len(completed_donations):
                donation = completed_donations[i + 10]
            else:
                donation = completed_donations[i % len(completed_donations)]
            test_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(2, 8))
            
            lab_test = {
                "id": str(uuid.uuid4()),
                "test_id": f"PDN-LAB-{2024011 + i}",
                "donation_id": donation['id'],
                "donor_id": donation['donor_id'],
                "donor_name": donation['donor_name'],
                "blood_unit_id": None,
                # Blood typing - done
                "blood_group_abo": donation['blood_group'][:-1] if donation['blood_group'][-1] in ['+', '-'] else donation['blood_group'],
                "blood_group_rh": '+' if '+' in donation['blood_group'] else '-',
                "blood_group_confirmed": donation['blood_group'],
                # Serology - some done, some pending
                "hiv_elisa": "negative",
                "hiv_nat": random.choice(["negative", "pending"]),
                "hbsag": "negative",
                "hbv_nat": "pending",
                "anti_hcv": random.choice(["negative", "pending"]),
                "hcv_nat": "pending",
                "syphilis_rpr": "negative",
                "syphilis_tpha": "pending",
                "malaria_antigen": "pending",
                "htlv": "pending",
                # Antibody - pending
                "antibody_screen": "pending",
                "crossmatch_compatible": None,
                "dat_result": "pending",
                # Results
                "overall_result": "pending",
                "test_date": test_date.strftime("%Y-%m-%d"),
                "test_time": test_date.strftime("%H:%M"),
                "tested_by": random.choice(staff_ids),
                "tested_by_name": "Lab Tech Siti",
                "verified_by": None,
                "verified_by_name": None,
                "status": "in_progress",
                "equipment_id": f"ANALYZER-{random.randint(1, 3)}",
                "reagent_lot": f"RG-{random.randint(1000, 9999)}",
                "notes": "Initial tests completed, awaiting NAT and antibody screening",
                "org_id": org_id,
                "created_at": test_date.isoformat(),
            }
            lab_tests.append(lab_test)
        
        # 5 Pending lab tests (awaiting all testing)
        in_progress_donations = [d for d in donations if d['status'] == 'in_progress']
        for i in range(5):
            # Create dummy donation references for pending tests
            test_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 4))
            blood_group = random.choice(BLOOD_GROUPS)
            donor = random.choice(donors[:20])
            
            lab_test = {
                "id": str(uuid.uuid4()),
                "test_id": f"PDN-LAB-{2024016 + i}",
                "donation_id": in_progress_donations[i % len(in_progress_donations)]['id'] if in_progress_donations else str(uuid.uuid4()),
                "donor_id": donor['id'],
                "donor_name": donor['full_name'],
                "blood_unit_id": None,
                # Blood typing - not done yet
                "blood_group_abo": None,
                "blood_group_rh": None,
                "blood_group_confirmed": None,
                # Serology - all pending
                "hiv_elisa": "pending",
                "hiv_nat": "pending",
                "hbsag": "pending",
                "hbv_nat": "pending",
                "anti_hcv": "pending",
                "hcv_nat": "pending",
                "syphilis_rpr": "pending",
                "syphilis_tpha": "pending",
                "malaria_antigen": "pending",
                "htlv": "pending",
                # Antibody - pending
                "antibody_screen": "pending",
                "crossmatch_compatible": None,
                "dat_result": "pending",
                # Results
                "overall_result": "pending",
                "test_date": test_date.strftime("%Y-%m-%d"),
                "test_time": test_date.strftime("%H:%M"),
                "tested_by": None,
                "tested_by_name": None,
                "verified_by": None,
                "verified_by_name": None,
                "status": "pending",
                "equipment_id": None,
                "reagent_lot": None,
                "notes": "Sample received - awaiting testing queue",
                "org_id": org_id,
                "created_at": test_date.isoformat(),
            }
            lab_tests.append(lab_test)
        
        await db.lab_tests.insert_many(lab_tests)
        logger.info(f"✓ Created {len(lab_tests)} lab tests:")
        logger.info(f"  → 10 completed (all tests passed)")
        logger.info(f"  → 5 in_progress (partial testing done)")
        logger.info(f"  → 5 pending (awaiting testing)")
        
        # ============================================
        # 6. BLOOD UNITS (26 total - various statuses for lab & processing demo)
        # Structure:
        # - 10 processed (from completed tests, already processed into components)
        # - 8 collected (awaiting laboratory testing - for Lab page demo)
        # - 8 lab (tested and ready for processing - for Processing page demo)
        # ============================================
        blood_units = []
        
        # 10 Processed blood units (from completed lab tests)
        completed_tests = [t for t in lab_tests if t['status'] == 'completed']
        for i, test in enumerate(completed_tests[:10]):
            donation = next(d for d in donations if d['id'] == test['donation_id'])
            collection_date = datetime.fromisoformat(donation['created_at'].replace('Z', '+00:00'))
            
            blood_unit = {
                "id": str(uuid.uuid4()),
                "unit_id": f"PDN-BU-{2024001 + i}",
                "donation_id": donation['id'],
                "donor_id": donation['donor_id'],
                "blood_group": donation['blood_group'],
                "confirmed_blood_group": donation['blood_group'],  # Add confirmed blood group
                "preliminary_blood_group": donation['blood_group'],
                "volume": donation.get('volume_collected', 450),
                "collection_date": collection_date.strftime("%Y-%m-%d"),
                "expiry_date": (collection_date + timedelta(days=42)).strftime("%Y-%m-%d"),
                "status": "processed",
                "bag_barcode": gen_barcode(f"PDN-BU-{2024001 + i}"),
                "sample_labels": [f"PDN-BU-{2024001+i}-S1", f"PDN-BU-{2024001+i}-S2"],
                "storage_location": f"REF-{random.choice(['A', 'B'])}-{random.randint(1, 5)}",
                "current_location": f"Storage - {random.choice(['PRC', 'Plasma', 'Platelets'])}",
                "temperature_log": [{"temp": round(random.uniform(2, 6), 1), "time": collection_date.isoformat()}],
                "qc_status": "passed",
                "org_id": org_id,
                "created_at": collection_date.isoformat(),
                "created_by": random.choice(staff_ids),
            }
            blood_units.append(blood_unit)
        
        # 8 Collected blood units (AWAITING LAB TESTING - for Laboratory page demo)
        for i in range(8):
            collection_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 12))
            donor = random.choice(donors[:20])
            blood_group = random.choice(BLOOD_GROUPS)
            
            blood_unit = {
                "id": str(uuid.uuid4()),
                "unit_id": f"PDN-BU-PEND-{i + 1}",
                "donation_id": None,
                "donor_id": donor['id'],
                "blood_group": None,
                "preliminary_blood_group": blood_group,
                "volume": random.choice([350, 450, 500]),
                "collection_date": collection_date.strftime("%Y-%m-%d"),
                "expiry_date": None,
                "status": "collected",
                "bag_barcode": gen_barcode(f"PDN-BU-PEND-{i + 1}"),
                "sample_labels": [f"PDN-BU-PEND-{i+1}-S1", f"PDN-BU-PEND-{i+1}-S2"],
                "storage_location": f"LAB-QUEUE-{random.randint(1, 3)}",
                "current_location": "Laboratory Queue",
                "temperature_log": [{"temp": round(random.uniform(2, 6), 1), "time": collection_date.isoformat()}],
                "qc_status": "pending",
                "notes": "Awaiting blood group confirmation and infectious disease screening",
                "org_id": org_id,
                "created_at": collection_date.isoformat(),
                "created_by": random.choice(staff_ids),
            }
            blood_units.append(blood_unit)
        
        # 8 Lab-completed blood units (READY FOR PROCESSING - for Processing page demo)
        for i in range(8):
            collection_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(12, 36))
            donor = random.choice(donors[:20])
            blood_group = random.choice(BLOOD_GROUPS)
            
            blood_unit = {
                "id": str(uuid.uuid4()),
                "unit_id": f"PDN-BU-LAB-{i + 1}",
                "donation_id": None,
                "donor_id": donor['id'],
                "blood_group": blood_group,  # Confirmed by lab
                "confirmed_blood_group": blood_group,  # Add confirmed blood group
                "preliminary_blood_group": blood_group,
                "volume": random.choice([350, 450, 500]),
                "collection_date": collection_date.strftime("%Y-%m-%d"),
                "expiry_date": (collection_date + timedelta(days=42)).strftime("%Y-%m-%d"),
                "status": "lab",  # Tested and ready for component separation
                "bag_barcode": gen_barcode(f"PDN-BU-LAB-{i + 1}"),
                "sample_labels": [f"PDN-BU-LAB-{i+1}-S1", f"PDN-BU-LAB-{i+1}-S2"],
                "storage_location": f"PROCESSING-QUEUE-{random.randint(1, 3)}",
                "current_location": "Processing Unit",
                "temperature_log": [{"temp": round(random.uniform(2, 6), 1), "time": collection_date.isoformat()}],
                "qc_status": "passed",
                "lab_status": "passed",
                "notes": "All lab tests passed - ready for component separation",
                "org_id": org_id,
                "created_at": collection_date.isoformat(),
                "created_by": random.choice(staff_ids),
            }
            blood_units.append(blood_unit)
        
        await db.blood_units.insert_many(blood_units)
        logger.info(f"✓ Created {len(blood_units)} blood units:")
        logger.info(f"  → 10 processed (testing completed)")
        logger.info(f"  → 8 collected (AWAITING LAB TESTING)")
        logger.info(f"  → 8 lab (READY FOR PROCESSING)")
        
        # ============================================
        # 7. COMPONENTS (50+ - various statuses for processing demo)
        # Structure:
        # - From processed blood units: available, reserved, issued, quarantine
        # - Additional processing items: pending_processing, in_processing
        # ============================================
        components = []
        
        # Components from processed blood units (only ones with donation_id)
        processed_units = [u for u in blood_units if u.get('donation_id') and u['status'] == 'processed']
        for i, unit in enumerate(processed_units):
            donation = next((d for d in donations if d['id'] == unit['donation_id']), None)
            if not donation:
                continue
            collection_date = datetime.fromisoformat(unit['created_at'].replace('Z', '+00:00'))
            
            # Create 3-4 components per unit
            for j, comp_type in enumerate(random.sample(COMPONENT_TYPES, random.randint(3, 4))):
                exp_days = 42 if comp_type == 'prc' else 5 if comp_type == 'platelets' else 365
                status = random.choices(['available', 'reserved', 'issued', 'quarantine'], weights=[40, 30, 20, 10])[0]
                
                component = {
                    "id": str(uuid.uuid4()),
                    "component_id": f"PDN-CMP-{2024001 + i}-{j + 1}",
                    "blood_unit_id": unit['id'],
                    "donation_id": unit['donation_id'],
                    "donor_id": unit['donor_id'],
                    "component_type": comp_type,
                    "component_name": comp_type.upper().replace('_', ' '),
                    "blood_group": unit['blood_group'],
                    "volume_ml": random.randint(150, 350),
                    "collection_date": collection_date.strftime("%Y-%m-%d"),
                    "processing_date": (collection_date + timedelta(hours=4)).strftime("%Y-%m-%d"),
                    "expiry_date": (collection_date + timedelta(days=exp_days)).strftime("%Y-%m-%d"),
                    "expiry_time": "23:59",
                    "status": status,
                    "storage_location": f"STORAGE-{comp_type[:3].upper()}-{random.randint(1, 10)}",
                    "storage_temperature": -25.0 if comp_type in ['ffp', 'cryoprecipitate'] else 4.0,
                    "qc_status": "passed",
                    "qc_date": (collection_date + timedelta(hours=6)).strftime("%Y-%m-%d"),
                    "barcode": f"CMP{random.randint(100000000, 999999999)}",
                    "irradiated": random.choice([True, False]) if comp_type == 'prc' else False,
                    "leukoreduced": random.choice([True, False]),
                    "issued_to": random.choice(HOSPITALS) if status == 'issued' else None,
                    "issued_date": (collection_date + timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d") if status == 'issued' else None,
                    "org_id": org_id,
                    "created_at": collection_date.isoformat(),
                }
                components.append(component)
        
        # Additional PENDING PROCESSING items (just collected, awaiting separation)
        for i in range(8):
            collection_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 6))
            blood_group = random.choice(BLOOD_GROUPS)
            donor = random.choice(donors[:20])
            
            for j, comp_type in enumerate(['prc', 'ffp', 'platelets']):
                exp_days = 42 if comp_type == 'prc' else 5 if comp_type == 'platelets' else 365
                
                component = {
                    "id": str(uuid.uuid4()),
                    "component_id": f"PDN-CMP-PEND-{i + 1}-{j + 1}",
                    "blood_unit_id": None,  # Not yet assigned
                    "donation_id": None,
                    "donor_id": donor['id'],
                    "component_type": comp_type,
                    "component_name": comp_type.upper().replace('_', ' '),
                    "blood_group": blood_group,
                    "volume_ml": None,  # Not measured yet
                    "collection_date": collection_date.strftime("%Y-%m-%d"),
                    "processing_date": None,  # Not processed yet
                    "expiry_date": None,  # Will be set after processing
                    "expiry_time": None,
                    "status": "pending_processing",
                    "storage_location": "CENTRIFUGE-QUEUE",
                    "storage_temperature": 4.0,
                    "qc_status": "pending",
                    "qc_date": None,
                    "barcode": f"CMP{random.randint(100000000, 999999999)}",
                    "irradiated": False,
                    "leukoreduced": False,
                    "issued_to": None,
                    "issued_date": None,
                    "notes": "Awaiting centrifugation and component separation",
                    "org_id": org_id,
                    "created_at": collection_date.isoformat(),
                }
                components.append(component)
        
        # Additional IN PROCESSING items (currently being separated)
        for i in range(5):
            collection_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(2, 4))
            blood_group = random.choice(BLOOD_GROUPS)
            donor = random.choice(donors[:20])
            
            for j, comp_type in enumerate(['prc', 'ffp']):
                component = {
                    "id": str(uuid.uuid4()),
                    "component_id": f"PDN-CMP-PROC-{i + 1}-{j + 1}",
                    "blood_unit_id": None,
                    "donation_id": None,
                    "donor_id": donor['id'],
                    "component_type": comp_type,
                    "component_name": comp_type.upper().replace('_', ' '),
                    "blood_group": blood_group,
                    "volume_ml": random.randint(200, 300) if j == 0 else None,  # PRC measured, FFP pending
                    "collection_date": collection_date.strftime("%Y-%m-%d"),
                    "processing_date": collection_date.strftime("%Y-%m-%d"),  # Processing started today
                    "expiry_date": None,
                    "expiry_time": None,
                    "status": "in_processing",
                    "storage_location": f"CENTRIFUGE-{random.randint(1, 3)}",
                    "storage_temperature": 4.0,
                    "qc_status": "pending",
                    "qc_date": None,
                    "barcode": f"CMP{random.randint(100000000, 999999999)}",
                    "irradiated": False,
                    "leukoreduced": False,
                    "issued_to": None,
                    "issued_date": None,
                    "notes": "Component separation in progress",
                    "org_id": org_id,
                    "created_at": collection_date.isoformat(),
                }
                components.append(component)
        
        # Additional PROCESSING items (separated and ready for QC validation)
        # Status 'processing' is what QCValidation.js page expects for pending validation
        for i in range(6):
            collection_date = datetime.now(timezone.utc) - timedelta(hours=random.randint(6, 12))
            blood_group = random.choice(BLOOD_GROUPS)
            donor = random.choice(donors[:20])
            exp_days = 42
            
            component = {
                "id": str(uuid.uuid4()),
                "component_id": f"PDN-CMP-QC-{i + 1}",
                "blood_unit_id": None,
                "donation_id": None,
                "donor_id": donor['id'],
                "component_type": "prc",
                "component_name": "PACKED RED CELLS",
                "blood_group": blood_group,
                "volume_ml": random.randint(250, 350),
                "collection_date": collection_date.strftime("%Y-%m-%d"),
                "processing_date": collection_date.strftime("%Y-%m-%d"),
                "expiry_date": (collection_date + timedelta(days=exp_days)).strftime("%Y-%m-%d"),
                "expiry_time": "23:59",
                "status": "processing",  # Changed from 'qc_pending' to match frontend expectation
                "storage_location": f"QC-HOLD-{random.randint(1, 5)}",
                "storage_temperature": 4.0,
                "qc_status": "pending",
                "qc_date": None,
                "barcode": f"CMP{random.randint(100000000, 999999999)}",
                "irradiated": False,
                "leukoreduced": True,
                "issued_to": None,
                "issued_date": None,
                "notes": "Awaiting quality control verification",
                "org_id": org_id,
                "created_at": collection_date.isoformat(),
            }
            components.append(component)
        
        await db.components.insert_many(components)
        logger.info(f"✓ Created {len(components)} components:")
        logger.info(f"  → ~37 from blood units (available/reserved/issued/quarantine)")
        logger.info(f"  → 24 pending_processing (awaiting separation)")
        logger.info(f"  → 10 in_processing (currently separating)")
        logger.info(f"  → 6 processing (awaiting QC verification)")
        
        # ============================================
        # 8. BLOOD REQUESTS (15 - various statuses)
        # ============================================
        blood_requests = []
        request_statuses = ['pending', 'pending', 'pending', 'approved', 'approved', 
                           'processing', 'processing', 'fulfilled', 'fulfilled', 'fulfilled',
                           'fulfilled', 'fulfilled', 'cancelled', 'pending', 'approved']
        
        for i, status in enumerate(request_statuses):
            req_date = rand_date(0, 14)
            hospital = random.choice(HOSPITALS)
            
            request = {
                "id": str(uuid.uuid4()),
                "request_id": f"PDN-REQ-{2024001 + i}",
                "request_type": random.choice(['routine', 'urgent', 'emergency']),
                "requester_name": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "requester_contact": gen_phone(),
                "requester_email": f"doctor{i+1}@{hospital.lower().replace(' ', '')}.gov.my",
                "hospital_name": hospital,
                "hospital_address": f"Jalan Hospital, {random.choice(CITIES)['city']}",
                "department": random.choice(['Surgery', 'ICU', 'Emergency', 'Oncology', 'Obstetrics']),
                "ward": f"Ward {random.randint(1, 20)}",
                "patient_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "patient_id": f"MRN-{random.randint(100000, 999999)}",
                "patient_age": random.randint(5, 80),
                "patient_gender": random.choice(['male', 'female']),
                "patient_diagnosis": random.choice(['Anemia', 'Surgery', 'Trauma', 'Cancer', 'Delivery', 'GI Bleeding']),
                "blood_group": random.choice(BLOOD_GROUPS),
                "product_type": random.choice(COMPONENT_TYPES),
                "quantity": random.randint(1, 6),
                "urgency": random.choice(['routine', 'urgent', 'stat']),
                "status": status,
                "requested_date": req_date.strftime("%Y-%m-%d"),
                "required_by_date": (req_date + timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d"),
                "required_by_time": f"{random.randint(8, 18):02d}:00",
                "approved_by": admin_id if status in ['approved', 'processing', 'fulfilled'] else None,
                "approved_date": (req_date + timedelta(hours=2)).isoformat() if status in ['approved', 'processing', 'fulfilled'] else None,
                "fulfilled_date": (req_date + timedelta(days=1)).isoformat() if status == 'fulfilled' else None,
                "crossmatch_required": True,
                "special_requirements": random.choice([None, "CMV Negative", "Irradiated", "Leukoreduced"]),
                "clinical_notes": f"Patient requires blood for {random.choice(['surgery', 'transfusion', 'treatment'])}",
                "org_id": org_id,
                "created_at": req_date.isoformat(),
                "created_by": admin_id,
            }
            blood_requests.append(request)
        
        await db.blood_requests.insert_many(blood_requests)
        logger.info(f"✓ Created {len(blood_requests)} blood requests (3 pending, 3 approved, 2 processing, 5 fulfilled, 1 cancelled)")
        
        # ============================================
        # 9. ISSUANCES (8 - for fulfilled requests)
        # ============================================
        issuances = []
        fulfilled_requests = [r for r in blood_requests if r['status'] == 'fulfilled']
        available_components = [c for c in components if c['status'] in ['available', 'issued']]
        
        for i, request in enumerate(fulfilled_requests[:8]):
            issue_date = rand_date(0, 10)
            comp = available_components[i % len(available_components)]
            
            issuance = {
                "id": str(uuid.uuid4()),
                "issuance_id": f"PDN-ISS-{2024001 + i}",
                "request_id": request['id'],
                "component_id": comp['id'],
                "component_type": comp['component_type'],
                "blood_group": comp['blood_group'],
                "volume_ml": comp['volume_ml'],
                "recipient_name": request['patient_name'],
                "recipient_id": request['patient_id'],
                "hospital_name": request['hospital_name'],
                "department": request['department'],
                "ward": request['ward'],
                "issued_date": issue_date.strftime("%Y-%m-%d"),
                "issued_time": issue_date.strftime("%H:%M"),
                "issued_by": random.choice(staff_ids),
                "issued_by_name": "Hassan bin Ibrahim",
                "received_by": f"Nurse {random.choice(FIRST_NAMES)}",
                "crossmatch_result": "compatible",
                "crossmatch_date": (issue_date - timedelta(hours=2)).strftime("%Y-%m-%d"),
                "status": "completed",
                "transfusion_started": (issue_date + timedelta(minutes=30)).isoformat(),
                "transfusion_completed": (issue_date + timedelta(hours=2)).isoformat(),
                "adverse_reaction": False,
                "notes": "Transfusion completed successfully",
                "org_id": org_id,
                "created_at": issue_date.isoformat(),
            }
            issuances.append(issuance)
        
        await db.issuances.insert_many(issuances)
        logger.info(f"✓ Created {len(issuances)} issuances")
        
        # ============================================
        # 10. RETURNS (5 - mix of pending & completed)
        # ============================================
        returns = []
        return_reasons = ['not_used', 'patient_discharged', 'transfusion_reaction', 'expired', 'wrong_product']
        
        for i in range(5):
            ret_date = rand_date(0, 15)
            is_completed = i < 3
            comp = random.choice(components)
            
            return_record = {
                "id": str(uuid.uuid4()),
                "return_id": f"PDN-RET-{2024001 + i}",
                "component_id": comp['id'],
                "component_type": comp['component_type'],
                "blood_group": comp['blood_group'],
                "volume_ml": comp['volume_ml'],
                "return_reason": random.choice(return_reasons),
                "returned_from": random.choice(HOSPITALS),
                "returned_by": f"Nurse {random.choice(FIRST_NAMES)}",
                "return_date": ret_date.strftime("%Y-%m-%d"),
                "return_time": ret_date.strftime("%H:%M"),
                "received_by": random.choice(staff_ids) if is_completed else None,
                "received_by_name": "Ali bin Rahman" if is_completed else None,
                "condition_on_return": random.choice(['good', 'acceptable', 'damaged']),
                "temperature_on_return": round(random.uniform(2, 8), 1),
                "seal_intact": random.choice([True, True, True, False]),
                "reusable": is_completed and random.choice([True, True, False]),
                "status": "processed" if is_completed else "pending",
                "inspection_notes": "Unit inspected and cleared for reuse" if is_completed else "Awaiting inspection",
                "processed_date": (ret_date + timedelta(hours=2)).isoformat() if is_completed else None,
                "org_id": org_id,
                "created_at": ret_date.isoformat(),
            }
            returns.append(return_record)
        
        await db.returns.insert_many(returns)
        logger.info(f"✓ Created {len(returns)} returns (3 processed, 2 pending)")
        
        # ============================================
        # 11. DISCARDS (6 - mix of pending & completed)
        # ============================================
        discards = []
        discard_reasons = ['expired', 'contaminated', 'damaged', 'qc_failed', 'reactive_test', 'hemolyzed']
        
        for i in range(6):
            disc_date = rand_date(0, 20)
            is_completed = i < 4
            comp = random.choice(components)
            
            discard = {
                "id": str(uuid.uuid4()),
                "discard_id": f"PDN-DIS-{2024001 + i}",
                "component_id": comp['id'],
                "component_type": comp['component_type'],
                "blood_group": comp['blood_group'],
                "volume_ml": comp['volume_ml'],
                "discard_reason": random.choice(discard_reasons),
                "discard_method": random.choice(['incineration', 'autoclave', 'chemical_treatment']),
                "discard_date": disc_date.strftime("%Y-%m-%d"),
                "discard_time": disc_date.strftime("%H:%M"),
                "discarded_by": random.choice(staff_ids) if is_completed else None,
                "discarded_by_name": "Ali bin Rahman" if is_completed else None,
                "witnessed_by": admin_id if is_completed else None,
                "witnessed_by_name": "Dr. Ahmad" if is_completed else None,
                "certificate_number": f"DISP-CERT-{random.randint(10000, 99999)}" if is_completed else None,
                "status": "completed" if is_completed else "pending",
                "approval_status": "approved" if is_completed else "pending_approval",
                "notes": f"Disposed due to {random.choice(discard_reasons)}",
                "org_id": org_id,
                "created_at": disc_date.isoformat(),
            }
            discards.append(discard)
        
        await db.discards.insert_many(discards)
        logger.info(f"✓ Created {len(discards)} discards (4 completed, 2 pending)")
        
        # ============================================
        # 12. LOGISTICS (8 - various statuses)
        # ============================================
        logistics = []
        logistics_statuses = ['pending', 'pending', 'assigned', 'in_transit', 'in_transit', 'delivered', 'delivered', 'delivered']
        
        for i, status in enumerate(logistics_statuses):
            log_date = rand_date(0, 10)
            dest_hospital = random.choice(HOSPITALS)
            
            logistic = {
                "id": str(uuid.uuid4()),
                "logistics_id": f"PDN-LOG-{2024001 + i}",
                "order_type": random.choice(['delivery', 'pickup', 'transfer']),
                "source_org_id": org_id,
                "source_org_name": org['org_name'],
                "source_address": org['address'],
                "destination_org_id": str(uuid.uuid4()),
                "destination_org_name": dest_hospital,
                "destination_address": f"Jalan Hospital, {random.choice(CITIES)['city']}",
                "component_ids": [random.choice(components)['id']],
                "component_count": random.randint(1, 5),
                "blood_groups": [random.choice(BLOOD_GROUPS)],
                "priority": random.choice(['normal', 'urgent', 'stat']),
                "status": status,
                "scheduled_pickup": log_date.isoformat(),
                "scheduled_delivery": (log_date + timedelta(hours=2)).isoformat(),
                "actual_pickup": (log_date + timedelta(minutes=15)).isoformat() if status in ['in_transit', 'delivered'] else None,
                "actual_delivery": (log_date + timedelta(hours=2, minutes=30)).isoformat() if status == 'delivered' else None,
                "driver_name": f"{random.choice(FIRST_NAMES)} bin {random.choice(LAST_NAMES)}" if status != 'pending' else None,
                "driver_phone": gen_phone() if status != 'pending' else None,
                "driver_id": str(uuid.uuid4()) if status != 'pending' else None,
                "vehicle_number": f"W{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1000, 9999)}" if status != 'pending' else None,
                "temperature_maintained": True,
                "temperature_log": [{"temp": round(random.uniform(2, 6), 1), "time": log_date.isoformat()}],
                "special_instructions": random.choice([None, "Handle with care", "Urgent", "Keep refrigerated"]),
                "delivery_notes": "Delivered successfully" if status == 'delivered' else None,
                "recipient_name": f"Nurse {random.choice(FIRST_NAMES)}" if status == 'delivered' else None,
                "recipient_signature": True if status == 'delivered' else None,
                "org_id": org_id,
                "created_at": log_date.isoformat(),
                "created_by": admin_id,
            }
            logistics.append(logistic)
        
        await db.logistics.insert_many(logistics)
        logger.info(f"✓ Created {len(logistics)} logistics orders (2 pending, 1 assigned, 2 in_transit, 3 delivered)")
        
        # ============================================
        # 13. QC VALIDATIONS (10 - various statuses for Validation History)
        # The frontend QCValidation.js expects fields: unit_component_id, unit_type, 
        # data_complete, screening_complete, custody_complete, status (approved/hold)
        # ============================================
        qc_validations = []
        
        for i, comp in enumerate(components[:10]):
            qc_date = rand_date(0, 15)
            is_completed = i < 8
            
            qc = {
                "id": str(uuid.uuid4()),
                "qc_id": f"PDN-QC-{2024001 + i}",
                "unit_component_id": comp['id'],  # Frontend expects this field
                "unit_type": "component",  # Frontend expects this field
                "component_id": comp['id'],
                "component_type": comp['component_type'],
                "blood_group": comp['blood_group'],
                "qc_date": qc_date.strftime("%Y-%m-%d"),
                "qc_time": qc_date.strftime("%H:%M"),
                # Frontend checklist fields
                "data_complete": True if is_completed else False,
                "screening_complete": True if is_completed else False,
                "custody_complete": True if is_completed else False,
                # Visual inspection
                "visual_inspection": "pass" if is_completed else "pending",
                "color": "normal" if is_completed else None,
                "turbidity": "clear" if is_completed else None,
                "clots_present": False if is_completed else None,
                "bag_integrity": "intact" if is_completed else None,
                "label_verification": "verified" if is_completed else None,
                # Volume
                "volume_ml": comp['volume_ml'],
                "volume_within_spec": True if is_completed else None,
                # Sterility
                "sterility_test": "negative" if is_completed else "pending",
                "bacterial_contamination": "negative" if is_completed else "pending",
                # Component specific
                "platelet_count": random.randint(200, 400) * 1000 if comp['component_type'] == 'platelets' and is_completed else None,
                "hematocrit": random.randint(55, 80) if comp['component_type'] == 'prc' and is_completed else None,
                "ph_level": round(random.uniform(6.4, 7.4), 1) if comp['component_type'] == 'platelets' and is_completed else None,
                # Results
                "qc_status": "approved" if is_completed else "hold",  # Frontend reads this
                "overall_result": "pass" if is_completed else "pending",
                "status": "approved" if is_completed else "hold",  # Frontend expects approved/hold
                "hold_reason": None if is_completed else "Missing validation checks",
                "performed_by": random.choice(staff_ids),
                "performed_by_name": "Lab Tech Siti",
                "verified_by": admin_id if is_completed else None,
                "notes": "QC passed" if is_completed else "Awaiting QC",
                "org_id": org_id,
                "created_at": qc_date.isoformat(),
            }
            qc_validations.append(qc)
        
        await db.qc_validation.insert_many(qc_validations)
        logger.info(f"✓ Created {len(qc_validations)} QC validations (8 completed, 2 pending)")
        
        # ============================================
        # 14. QUARANTINE (5)
        # ============================================
        quarantine_records = []
        quarantine_reasons = ['reactive_screening', 'donor_callback', 'qc_investigation', 'suspected_contamination']
        
        for i in range(5):
            q_date = rand_date(0, 20)
            is_released = i < 2
            comp = random.choice(components)
            
            quarantine = {
                "id": str(uuid.uuid4()),
                "quarantine_id": f"PDN-QUA-{2024001 + i}",
                # Frontend expects these field names
                "unit_component_id": comp['id'],
                "component_id": comp['id'],
                "component_type": comp['component_type'],
                "blood_group": comp['blood_group'],
                "reason": random.choice(quarantine_reasons),  # Frontend expects 'reason'
                "quarantine_reason": random.choice(quarantine_reasons),  # Keep for backwards compat
                "quarantine_date": q_date.strftime("%Y-%m-%d"),
                "quarantine_location": "Quarantine Storage",
                "status": "released" if is_released else "quarantined",
                "investigation_status": "completed" if is_released else "in_progress",
                "investigation_notes": "Investigation complete, cleared" if is_released else "Under investigation",
                "retest_result": "non_reactive" if is_released else None,  # Frontend expects this
                "quarantined_by": random.choice(staff_ids),
                "quarantined_by_name": "Lab Tech Siti",
                "released_by": admin_id if is_released else None,
                "released_date": (q_date + timedelta(days=3)).isoformat() if is_released else None,
                "release_notes": "Cleared for use" if is_released else None,
                "org_id": org_id,
                "created_at": q_date.isoformat(),
            }
            quarantine_records.append(quarantine)
        
        await db.quarantine.insert_many(quarantine_records)
        logger.info(f"✓ Created {len(quarantine_records)} quarantine records (2 released, 3 quarantined)")
        
        # ============================================
        # 15. STORAGE LOCATIONS (6)
        # ============================================
        storage_locations = [
            {"id": str(uuid.uuid4()), "name": "Refrigerator A", "code": "REF-A", "type": "refrigerator", "temperature_min": 2, "temperature_max": 6, "current_temperature": 4.2, "capacity": 500, "current_count": 120, "status": "active", "location": "Blood Bank Floor 1", "org_id": org_id, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "name": "Refrigerator B", "code": "REF-B", "type": "refrigerator", "temperature_min": 2, "temperature_max": 6, "current_temperature": 3.8, "capacity": 500, "current_count": 95, "status": "active", "location": "Blood Bank Floor 1", "org_id": org_id, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "name": "Freezer Unit 1", "code": "FRZ-1", "type": "freezer", "temperature_min": -30, "temperature_max": -18, "current_temperature": -25.5, "capacity": 300, "current_count": 180, "status": "active", "location": "Blood Bank Floor 2", "org_id": org_id, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "name": "Freezer Unit 2", "code": "FRZ-2", "type": "freezer", "temperature_min": -30, "temperature_max": -18, "current_temperature": -24.0, "capacity": 300, "current_count": 145, "status": "active", "location": "Blood Bank Floor 2", "org_id": org_id, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "name": "Platelet Incubator", "code": "PLT-INC", "type": "incubator", "temperature_min": 20, "temperature_max": 24, "current_temperature": 22.0, "capacity": 100, "current_count": 35, "status": "active", "location": "Blood Bank Floor 1", "org_id": org_id, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "name": "Quarantine Storage", "code": "QUA-1", "type": "quarantine", "temperature_min": 2, "temperature_max": 6, "current_temperature": 4.0, "capacity": 50, "current_count": 8, "status": "active", "location": "Blood Bank Floor 2", "org_id": org_id, "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        await db.storage_locations.insert_many(storage_locations)
        logger.info(f"✓ Created {len(storage_locations)} storage locations")
        
        # ============================================
        # 16. REQUESTORS (6 hospitals)
        # ============================================
        requestors = []
        for i, hospital in enumerate(HOSPITALS[:6] if len(HOSPITALS) >= 6 else HOSPITALS):
            city = random.choice(CITIES)
            status = "approved" if i < 4 else "pending"
            
            requestor = {
                "id": str(uuid.uuid4()),
                "organization_name": hospital,
                "organization_type": "hospital",
                "registration_number": f"MOH-{random.randint(10000, 99999)}",
                "license_number": f"HOS-{random.randint(1000, 9999)}",
                "contact_person": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "designation": random.choice(['Medical Director', 'Blood Bank Manager']),
                "email": f"bloodbank@{hospital.lower().replace(' ', '')}.gov.my",
                "phone": gen_phone(),
                "address": f"Jalan Hospital {random.randint(1, 20)}",
                "city": city['city'],
                "state": city['state'],
                "country": "Malaysia",
                "latitude": city['lat'],
                "longitude": city['lng'],
                "status": status,
                "password_hash": hash_pw("Hospital@123"),
                "approved_by": admin_id if status == 'approved' else None,
                "approved_at": rand_datetime_str(1, 30) if status == 'approved' else None,
                "created_at": rand_datetime_str(30, 180),
            }
            requestors.append(requestor)
        
        await db.requestors.insert_many(requestors)
        logger.info(f"✓ Created {len(requestors)} requestors (4 approved, 2 pending)")
        
        # ============================================
        # 17. BROADCASTS (5)
        # ============================================
        broadcasts = []
        for btype in ['urgent_need', 'urgent_need', 'surplus_alert', 'surplus_alert', 'announcement']:
            broadcasts.append({
                "id": str(uuid.uuid4()),
                "org_id": org_id,
                "org_name": org['org_name'],
                "broadcast_type": btype,
                "blood_group": random.choice(BLOOD_GROUPS) if btype != 'announcement' else None,
                "component_type": random.choice(COMPONENT_TYPES) if btype != 'announcement' else None,
                "units_needed": random.randint(5, 15) if btype == 'urgent_need' else None,
                "units_available": random.randint(10, 30) if btype == 'surplus_alert' else None,
                "priority": random.choice(['normal', 'high', 'critical']),
                "title": "URGENT: Blood Needed" if btype == 'urgent_need' else "Surplus Available" if btype == 'surplus_alert' else "Blood Drive Announcement",
                "description": "Critical need for blood units" if btype == 'urgent_need' else "Surplus units available" if btype == 'surplus_alert' else "Upcoming blood donation drive",
                "contact_name": "Dr. Ahmad",
                "contact_phone": org['contact_phone'],
                "visibility": "network_wide",
                "status": "active",
                "response_count": random.randint(0, 10),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
                "created_by": admin_id,
                "created_at": rand_datetime_str(0, 5),
            })
        
        await db.broadcasts.insert_many(broadcasts)
        logger.info(f"✓ Created {len(broadcasts)} broadcasts")
        
        # ============================================
        # 18. INTER-ORG REQUESTS (6)
        # ============================================
        inter_org = []
        inter_statuses = ['pending', 'pending', 'approved', 'dispatched', 'delivered', 'delivered']
        
        for i, status in enumerate(inter_statuses):
            inter_org.append({
                "id": str(uuid.uuid4()),
                "request_type": random.choice(['internal', 'external']),
                "requesting_org_id": org_id,
                "requesting_org_name": org['org_name'],
                "fulfilling_org_id": org_id,
                "fulfilling_org_name": org['org_name'],
                "component_type": random.choice(COMPONENT_TYPES),
                "blood_group": random.choice(BLOOD_GROUPS),
                "quantity": random.randint(1, 10),
                "urgency_level": random.choice(['routine', 'urgent', 'emergency']),
                "clinical_indication": f"Patient: {random.choice(FIRST_NAMES)} - {random.choice(['Surgery', 'Trauma', 'Cancer'])}",
                "status": status,
                "required_by": (datetime.now(timezone.utc) + timedelta(days=random.randint(0, 3))).isoformat(),
                "approved_by": admin_id if status not in ['pending'] else None,
                "approved_at": rand_datetime_str(0, 2) if status not in ['pending'] else None,
                "dispatched_at": rand_datetime_str(0, 1) if status in ['dispatched', 'delivered'] else None,
                "delivered_at": rand_datetime_str(0, 1) if status == 'delivered' else None,
                "created_by": admin_id,
                "org_id": org_id,
                "created_at": rand_datetime_str(0, 7),
            })
        
        await db.inter_org_requests.insert_many(inter_org)
        logger.info(f"✓ Created {len(inter_org)} inter-org requests")
        
        # ============================================
        # 19. ALERTS (10)
        # ============================================
        alerts = []
        alert_types = ['low_inventory', 'expiring_soon', 'temperature_alert', 'equipment_maintenance', 'donor_callback']
        
        for i in range(10):
            a_date = rand_date(0, 7)
            is_resolved = i < 6
            
            alerts.append({
                "id": str(uuid.uuid4()),
                "alert_id": f"PDN-ALT-{2024001 + i}",
                "alert_type": random.choice(alert_types),
                "severity": random.choice(['low', 'medium', 'high', 'critical']),
                "title": f"Alert: {random.choice(['Low O- Stock', 'Units Expiring', 'Temperature Warning', 'Equipment Check', 'Donor Follow-up'])}",
                "message": "Please take necessary action.",
                "blood_group": random.choice(BLOOD_GROUPS) if random.random() > 0.3 else None,
                "status": "resolved" if is_resolved else random.choice(['active', 'acknowledged']),
                "acknowledged_by": admin_id if is_resolved or random.random() > 0.5 else None,
                "acknowledged_at": (a_date + timedelta(hours=1)).isoformat() if is_resolved else None,
                "resolved_by": admin_id if is_resolved else None,
                "resolved_at": (a_date + timedelta(hours=4)).isoformat() if is_resolved else None,
                "resolution_notes": "Issue resolved" if is_resolved else None,
                "org_id": org_id,
                "created_at": a_date.isoformat(),
            })
        
        await db.alerts.insert_many(alerts)
        logger.info(f"✓ Created {len(alerts)} alerts (6 resolved, 4 active/acknowledged)")
        
        # ============================================
        # 20. AUDIT LOGS (30)
        # ============================================
        audit_logs = []
        actions = [
            ("login", "auth", "User logged in"),
            ("logout", "auth", "User logged out"),
            ("create", "donors", "Donor registered"),
            ("update", "donors", "Donor updated"),
            ("create", "donations", "Donation recorded"),
            ("update", "donations", "Donation completed"),
            ("create", "lab_tests", "Lab test created"),
            ("update", "lab_tests", "Lab test completed"),
            ("create", "components", "Component created"),
            ("update", "components", "Component issued"),
            ("create", "requests", "Request created"),
            ("approve", "requests", "Request approved"),
            ("create", "issuances", "Blood issued"),
            ("create", "returns", "Return processed"),
            ("create", "discards", "Discard recorded"),
        ]
        
        for _ in range(30):
            action, module, desc = random.choice(actions)
            audit_logs.append({
                "id": str(uuid.uuid4()),
                "user_id": random.choice([admin_id] + staff_ids),
                "user_email": random.choice(["admin@pdn.gov.my", "labtech@pdn.gov.my", "nurse@pdn.gov.my", "distribution@pdn.gov.my"]),
                "user_name": random.choice(["Dr. Ahmad", "Siti Aminah", "Nurse Fatimah", "Hassan Ibrahim"]),
                "action": action,
                "module": module,
                "description": desc,
                "ip_address": f"192.168.1.{random.randint(1, 255)}",
                "org_id": org_id,
                "created_at": rand_datetime_str(0, 30),
            })
        
        await db.audit_logs.insert_many(audit_logs)
        logger.info(f"✓ Created {len(audit_logs)} audit logs")
        
        # ============================================
        # 21. DONOR REQUESTS (16 - registration requests)
        # ============================================
        donor_requests = []
        
        # 8 pending requests (for demo approval/rejection)
        for i in range(8):
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            donor_requests.append({
                "id": str(uuid.uuid4()),
                "request_id": f"DR-{2024001 + i}",
                "donor_id": None,
                "identity_type": random.choice(["mykad", "passport"]),
                "identity_number": f"{random.randint(70, 99):02d}{random.randint(1, 12):02d}{random.randint(1, 28):02d}-{random.randint(1, 14):02d}-{random.randint(1000, 9999)}",
                "full_name": f"{first} {last}",
                "date_of_birth": f"{random.randint(1970, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "gender": random.choice(["male", "female"]),
                "blood_group": random.choice(BLOOD_GROUPS),
                "weight": round(random.uniform(50, 90), 1),
                "height": random.randint(150, 185),
                "phone": f"+60-{random.choice(['11', '12', '13', '16', '17', '18', '19'])}-{random.randint(1000000, 9999999)}",
                "email": f"{first.lower()}.{last.lower()}{random.randint(10,99)}@email.com.my",
                "address": f"No. {random.randint(1, 200)}, Jalan {random.choice(['Merdeka', 'Ampang', 'Cheras'])} {random.randint(1, 30)}, Kuala Lumpur",
                "health_questionnaire": {
                    "recent_illness": False,
                    "on_medication": random.choice([False, False, True]),
                    "recent_surgery": False,
                    "recent_tattoo": False,
                },
                "consent_given": True,
                "request_type": "new_registration",
                "status": "pending",
                "reviewed_by": None,
                "reviewed_at": None,
                "rejection_reason": None,
                "created_at": rand_date(0, 5).isoformat(),
            })
        
        # 5 approved requests
        for i in range(5):
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            created = rand_date(10, 30)
            reviewed = created + timedelta(hours=random.randint(2, 24))
            donor_requests.append({
                "id": str(uuid.uuid4()),
                "request_id": f"DR-{2024020 + i}",
                "donor_id": f"PDN-D-{2024100 + i}",
                "identity_type": "mykad",
                "identity_number": f"{random.randint(70, 99):02d}{random.randint(1, 12):02d}{random.randint(1, 28):02d}-{random.randint(1, 14):02d}-{random.randint(1000, 9999)}",
                "full_name": f"{first} {last}",
                "date_of_birth": f"{random.randint(1970, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "gender": random.choice(["male", "female"]),
                "blood_group": random.choice(BLOOD_GROUPS),
                "weight": round(random.uniform(50, 90), 1),
                "height": random.randint(150, 185),
                "phone": f"+60-{random.choice(['11', '12', '16', '17'])}-{random.randint(1000000, 9999999)}",
                "email": f"{first.lower()}.{last.lower()}{random.randint(10,99)}@email.com.my",
                "address": f"No. {random.randint(1, 200)}, Jalan Example, Kuala Lumpur",
                "health_questionnaire": {"recent_illness": False, "on_medication": False},
                "consent_given": True,
                "request_type": "new_registration",
                "status": "approved",
                "reviewed_by": "admin@pdn.gov.my",
                "reviewed_at": reviewed.isoformat(),
                "rejection_reason": None,
                "created_at": created.isoformat(),
            })
        
        # 3 rejected requests
        rejection_reasons = ["Age below minimum requirement", "Failed health screening", "Incomplete documentation"]
        for i, reason in enumerate(rejection_reasons):
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            created = rand_date(15, 45)
            reviewed = created + timedelta(hours=random.randint(4, 48))
            donor_requests.append({
                "id": str(uuid.uuid4()),
                "request_id": f"DR-{2024030 + i}",
                "donor_id": None,
                "identity_type": "mykad",
                "identity_number": f"{random.randint(70, 99):02d}{random.randint(1, 12):02d}{random.randint(1, 28):02d}-{random.randint(1, 14):02d}-{random.randint(1000, 9999)}",
                "full_name": f"{first} {last}",
                "date_of_birth": f"{random.randint(1970, 2005)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "gender": random.choice(["male", "female"]),
                "blood_group": random.choice(BLOOD_GROUPS),
                "weight": round(random.uniform(45, 90), 1),
                "height": random.randint(150, 185),
                "phone": f"+60-{random.choice(['11', '12', '16', '17'])}-{random.randint(1000000, 9999999)}",
                "email": f"{first.lower()}.{last.lower()}{random.randint(10,99)}@email.com.my",
                "address": f"No. {random.randint(1, 200)}, Jalan Example, Kuala Lumpur",
                "health_questionnaire": {"recent_illness": False, "on_medication": False},
                "consent_given": True,
                "request_type": "new_registration",
                "status": "rejected",
                "reviewed_by": "admin@pdn.gov.my",
                "reviewed_at": reviewed.isoformat(),
                "rejection_reason": reason,
                "created_at": created.isoformat(),
            })
        
        await db.donor_requests.insert_many(donor_requests)
        logger.info(f"✓ Created {len(donor_requests)} donor requests (8 pending, 5 approved, 3 rejected)")
        
        # ============================================
        # COMPLETION SUMMARY
        # ============================================
        logger.info("=" * 60)
        logger.info("✅ COMPREHENSIVE DEMO DATA SEEDING COMPLETE!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Data Summary:")
        logger.info(f"  • Organization: {org['org_name']}")
        logger.info(f"  • Users: {len(staff_ids) + 1}")
        logger.info(f"  • Donors: {len(donors)} (20 eligible, 5 ready for collection, 5 pending/deferred)")
        logger.info(f"  • Screenings: {len(screenings)} (25 completed, 5 pending)")
        logger.info(f"  • Donations: {len(donations)} (12 completed, 3 in_progress)")
        logger.info(f"  • ★ READY FOR COLLECTION: 5 donors (PDN-D-2024021 to PDN-D-2024025)")
        logger.info(f"  • Lab Tests: {len(lab_tests)} (10 completed, 5 in_progress, 5 pending)")
        logger.info(f"  • Blood Units: {len(blood_units)} (10 processed, 8 awaiting lab, 8 ready for processing)")
        logger.info(f"  • Components: {len(components)} (various processing statuses)")
        logger.info(f"  • Blood Requests: {len(blood_requests)} (pending/approved/fulfilled)")
        logger.info(f"  • Issuances: {len(issuances)}")
        logger.info(f"  • Returns: {len(returns)} (3 processed, 2 pending)")
        logger.info(f"  • Discards: {len(discards)} (4 completed, 2 pending)")
        logger.info(f"  • Logistics: {len(logistics)} (various statuses)")
        logger.info(f"  • QC Validations: {len(qc_validations)} (8 completed, 2 pending)")
        logger.info(f"  • Quarantine: {len(quarantine_records)}")
        logger.info(f"  • Storage Locations: {len(storage_locations)}")
        logger.info(f"  • Requestors: {len(requestors)} (4 approved, 2 pending)")
        logger.info(f"  • Broadcasts: {len(broadcasts)}")
        logger.info(f"  • Inter-Org Requests: {len(inter_org)}")
        logger.info(f"  • Alerts: {len(alerts)} (6 resolved, 4 active)")
        logger.info(f"  • Audit Logs: {len(audit_logs)}")
        logger.info(f"  • Donor Requests: {len(donor_requests)} (8 pending, 5 approved, 3 rejected)")
        logger.info("")
        logger.info("Processing Queue Summary:")
        logger.info(f"  • Pending Processing: 24 components awaiting separation")
        logger.info(f"  • In Processing: 10 components currently being separated")
        logger.info(f"  • QC Pending: 6 components awaiting quality check")
        logger.info("")
        logger.info("Login Credentials:")
        logger.info("  Admin: admin@pdn.gov.my / Admin@123")
        logger.info("  Staff: labtech@pdn.gov.my, nurse@pdn.gov.my / Staff@123")
        logger.info("  Requestor: bloodbank@hospitalkualalumpur.gov.my / Hospital@123")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error seeding demo data: {e}")
        import traceback
        traceback.print_exc()
