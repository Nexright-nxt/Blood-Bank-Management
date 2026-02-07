"""
Comprehensive Demo Data Seeding Script for Blood Link
Creates end-to-end data for all modules to demonstrate the complete workflow.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "bbms")

# Demo data constants
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
COMPONENT_TYPES = ['whole_blood', 'prc', 'ffp', 'platelets', 'cryoprecipitate']
MALAYSIAN_ID_TYPES = ['mykad', 'mykas', 'mykid', 'mypr', 'passport']

# Sample names
FIRST_NAMES = ['Ahmad', 'Siti', 'Muhammad', 'Nur', 'Mohamed', 'Fatimah', 'Ali', 'Aishah', 'Hassan', 'Zainab', 
               'Raj', 'Priya', 'Lee', 'Wong', 'Tan', 'Lim', 'Kumar', 'Devi', 'Chen', 'Singh']
LAST_NAMES = ['Abdullah', 'Rahman', 'Hassan', 'Ibrahim', 'Ismail', 'Ahmad', 'Yusof', 'Omar', 'Zakaria', 'Ali',
              'Kumar', 'Singh', 'Tan', 'Lee', 'Wong', 'Lim', 'Chen', 'Ng', 'Krishnan', 'Muthu']

# Cities with coordinates
CITIES = [
    {'city': 'Kuala Lumpur', 'state': 'Wilayah Persekutuan', 'lat': 3.1390, 'lng': 101.6869},
    {'city': 'Petaling Jaya', 'state': 'Selangor', 'lat': 3.1073, 'lng': 101.6067},
    {'city': 'Shah Alam', 'state': 'Selangor', 'lat': 3.0733, 'lng': 101.5185},
    {'city': 'Johor Bahru', 'state': 'Johor', 'lat': 1.4927, 'lng': 103.7414},
    {'city': 'George Town', 'state': 'Penang', 'lat': 5.4141, 'lng': 100.3288},
    {'city': 'Ipoh', 'state': 'Perak', 'lat': 4.5975, 'lng': 101.0901},
]

def generate_mykad():
    """Generate a valid-looking MyKad number"""
    year = random.randint(70, 99)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    state = random.randint(1, 14)
    seq = random.randint(1000, 9999)
    return f"{year:02d}{month:02d}{day:02d}-{state:02d}-{seq}"

def generate_phone():
    """Generate Malaysian phone number"""
    prefixes = ['011', '012', '013', '014', '016', '017', '018', '019']
    return f"+60{random.choice(prefixes)[1:]}-{random.randint(1000000, 9999999)}"

def random_date_between(start_days_ago, end_days_ago):
    """Generate random date between start and end days ago"""
    # Ensure start is the larger number (further in the past)
    min_days = min(start_days_ago, end_days_ago)
    max_days = max(start_days_ago, end_days_ago)
    days = random.randint(min_days, max_days)
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

async def seed_demo_data():
    """Main function to seed all demo data"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 60)
    print("BLOOD LINK - Demo Data Seeding Script")
    print("=" * 60)
    
    # ========================================
    # 0. CREATE ORGANIZATION & ADMIN IF NEEDED
    # ========================================
    test_org = await db.organizations.find_one({"org_name": "Test Organization"})
    
    if not test_org:
        print("\n🏢 Creating Test Organization and Admin...")
        
        # Create organization
        org_id = str(uuid.uuid4())
        city_info = CITIES[0]  # Kuala Lumpur
        test_org = {
            "id": org_id,
            "org_name": "Test Organization",
            "org_type": "hospital_network",
            "is_parent": True,
            "parent_org_id": None,
            "address": "123 Jalan Darah, Bukit Bintang",
            "city": city_info['city'],
            "state": city_info['state'],
            "country": "Malaysia",
            "latitude": city_info['lat'],
            "longitude": city_info['lng'],
            "location": {
                "type": "Point",
                "coordinates": [city_info['lng'], city_info['lat']]
            },
            "contact_person": "Dr. Ahmad Rahman",
            "contact_phone": "+60-12-3456789",
            "contact_email": "admin@testorg.com",
            "license_number": "LIC-TEST-001",
            "is_active": True,
            "is_24x7": True,
            "operating_hours": "24/7",
            "blood_link_visible": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.organizations.insert_one(test_org)
        
        # Create geospatial index
        try:
            await db.organizations.create_index([("location", "2dsphere")])
        except:
            pass
        
        # Create super admin user
        admin_id = str(uuid.uuid4())
        admin_user = {
            "id": admin_id,
            "email": "admin@testorg.com",
            "password_hash": pwd_context.hash("Test@123"),
            "full_name": "Test Org Admin",
            "phone": "+60-12-3456789",
            "role": "admin",
            "user_type": "super_admin",
            "org_id": org_id,
            "org_name": "Test Organization",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one(admin_user)
        
        print(f"   ✓ Created organization: Test Organization")
        print(f"   ✓ Created admin user: admin@testorg.com / Test@123")
    
    org_id = test_org['id']
    print(f"\n✓ Using organization: {test_org['org_name']} ({org_id})")
    
    # Get admin user for created_by fields
    admin_user = await db.users.find_one({"email": "admin@testorg.com"})
    admin_id = admin_user['id'] if admin_user else "system"
    
    # ========================================
    # 1. DONORS (15 donors with various statuses)
    # ========================================
    print("\n📋 Creating Donors...")
    donors = []
    for i in range(15):
        city_info = random.choice(CITIES)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        status = random.choices(['approved', 'pending', 'deferred'], weights=[70, 20, 10])[0]
        
        donor = {
            "id": str(uuid.uuid4()),
            "donor_id": f"DNR-{2024000 + i}",
            "id_type": random.choice(MALAYSIAN_ID_TYPES),
            "id_number": generate_mykad(),
            "first_name": first,
            "last_name": last,
            "full_name": f"{first} {last}",
            "date_of_birth": f"{random.randint(1970, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "gender": random.choice(['male', 'female']),
            "blood_group": random.choice(BLOOD_GROUPS),
            "phone": generate_phone(),
            "email": f"{first.lower()}.{last.lower()}{random.randint(1,99)}@email.com",
            "address": f"{random.randint(1, 999)} Jalan {random.choice(['Maju', 'Harmoni', 'Bahagia', 'Sentosa', 'Damai'])}",
            "city": city_info['city'],
            "state": city_info['state'],
            "country": "Malaysia",
            "pincode": f"{random.randint(10000, 99999)}",
            "latitude": city_info['lat'] + random.uniform(-0.05, 0.05),
            "longitude": city_info['lng'] + random.uniform(-0.05, 0.05),
            "status": status,
            "donation_count": random.randint(0, 10) if status == 'approved' else 0,
            "last_donation_date": random_date_between(60, 365) if status == 'approved' and random.random() > 0.3 else None,
            "org_id": org_id,
            "created_at": random_date_between(30, 180),
            "created_by": admin_id,
        }
        donors.append(donor)
    
    await db.donors.insert_many(donors)
    print(f"   ✓ Created {len(donors)} donors")
    
    # ========================================
    # 2. DONATIONS (10 completed donations)
    # ========================================
    print("\n🩸 Creating Donations...")
    donations = []
    approved_donors = [d for d in donors if d['status'] == 'approved'][:10]
    
    for i, donor in enumerate(approved_donors):
        donation_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
        donation = {
            "id": str(uuid.uuid4()),
            "donation_id": f"DON-{2024000 + i}",
            "donor_id": donor['id'],
            "donor_name": donor['full_name'],
            "blood_group": donor['blood_group'],
            "donation_type": random.choice(['whole_blood', 'platelet', 'plasma']),
            "volume_ml": random.choice([350, 450, 500]),
            "donation_date": donation_date.strftime("%Y-%m-%d"),
            "donation_time": f"{random.randint(8, 16):02d}:{random.randint(0, 59):02d}",
            "phlebotomist_id": admin_id,
            "phlebotomist_name": "Staff Phlebotomist",
            "status": "completed",
            "arm_used": random.choice(['left', 'right']),
            "needle_gauge": random.choice(['16G', '17G', '18G']),
            "adverse_reactions": None,
            "notes": f"Donation completed successfully. Donor in good condition.",
            "org_id": org_id,
            "created_at": donation_date.isoformat(),
            "created_by": admin_id,
        }
        donations.append(donation)
    
    await db.donations.insert_many(donations)
    print(f"   ✓ Created {len(donations)} donations")
    
    # ========================================
    # 3. SCREENINGS (for each donation)
    # ========================================
    print("\n🔬 Creating Screenings...")
    screenings = []
    for donation in donations:
        screening = {
            "id": str(uuid.uuid4()),
            "screening_id": f"SCR-{donation['donation_id'].split('-')[1]}",
            "donation_id": donation['id'],
            "donor_id": donation['donor_id'],
            "screening_date": donation['donation_date'],
            "hemoglobin": round(random.uniform(12.5, 16.5), 1),
            "blood_pressure_systolic": random.randint(110, 140),
            "blood_pressure_diastolic": random.randint(70, 90),
            "pulse": random.randint(60, 100),
            "temperature": round(random.uniform(36.2, 37.2), 1),
            "weight_kg": round(random.uniform(50, 90), 1),
            "hiv_status": "negative",
            "hbv_status": "negative",
            "hcv_status": "negative",
            "syphilis_status": "negative",
            "malaria_status": "negative",
            "overall_result": "pass",
            "screened_by": admin_id,
            "notes": "All screening tests passed.",
            "org_id": org_id,
            "created_at": donation['created_at'],
        }
        screenings.append(screening)
    
    await db.screenings.insert_many(screenings)
    print(f"   ✓ Created {len(screenings)} screenings")
    
    # ========================================
    # 4. LAB TESTS (for each donation)
    # ========================================
    print("\n🧪 Creating Lab Tests...")
    lab_tests = []
    for donation in donations:
        lab_test = {
            "id": str(uuid.uuid4()),
            "test_id": f"LAB-{donation['donation_id'].split('-')[1]}",
            "donation_id": donation['id'],
            "donor_id": donation['donor_id'],
            "blood_group_abo": donation['blood_group'][:donation['blood_group'].index('+') if '+' in donation['blood_group'] else donation['blood_group'].index('-')],
            "blood_group_rh": '+' if '+' in donation['blood_group'] else '-',
            "antibody_screen": "negative",
            "crossmatch_compatible": True,
            "hiv_elisa": "negative",
            "hiv_nat": "negative",
            "hbsag": "negative",
            "hbv_nat": "negative",
            "anti_hcv": "negative",
            "hcv_nat": "negative",
            "syphilis_rpr": "negative",
            "malaria_antigen": "negative",
            "test_date": donation['donation_date'],
            "tested_by": admin_id,
            "verified_by": admin_id,
            "status": "completed",
            "org_id": org_id,
            "created_at": donation['created_at'],
        }
        lab_tests.append(lab_test)
    
    await db.lab_tests.insert_many(lab_tests)
    print(f"   ✓ Created {len(lab_tests)} lab tests")
    
    # ========================================
    # 5. BLOOD UNITS & COMPONENTS
    # ========================================
    print("\n🏷️ Creating Blood Units & Components...")
    blood_units = []
    components = []
    
    for i, donation in enumerate(donations):
        collection_date = datetime.fromisoformat(donation['created_at'].replace('Z', '+00:00'))
        expiry_date = collection_date + timedelta(days=42)  # Standard expiry for whole blood
        
        # Create blood unit
        blood_unit = {
            "id": str(uuid.uuid4()),
            "unit_id": f"BU-{donation['donation_id'].split('-')[1]}",
            "donation_id": donation['id'],
            "donor_id": donation['donor_id'],
            "blood_group": donation['blood_group'],
            "volume_ml": donation['volume_ml'],
            "collection_date": donation['donation_date'],
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "status": "processed",
            "storage_location": f"Refrigerator-{random.randint(1, 3)}",
            "temperature": round(random.uniform(2, 6), 1),
            "org_id": org_id,
            "created_at": donation['created_at'],
        }
        blood_units.append(blood_unit)
        
        # Create components (2-3 per donation)
        num_components = random.randint(2, 3)
        component_types = random.sample(COMPONENT_TYPES, num_components)
        
        for j, comp_type in enumerate(component_types):
            comp_expiry = expiry_date
            if comp_type == 'platelets':
                comp_expiry = collection_date + timedelta(days=5)
            elif comp_type == 'ffp':
                comp_expiry = collection_date + timedelta(days=365)
            elif comp_type == 'cryoprecipitate':
                comp_expiry = collection_date + timedelta(days=365)
            
            # Vary status - some ready, some reserved, some issued
            status = random.choices(['ready_to_use', 'reserved', 'issued'], weights=[60, 25, 15])[0]
            
            component = {
                "id": str(uuid.uuid4()),
                "component_id": f"CMP-{donation['donation_id'].split('-')[1]}-{j+1}",
                "blood_unit_id": blood_unit['id'],
                "donation_id": donation['id'],
                "donor_id": donation['donor_id'],
                "component_type": comp_type,
                "blood_group": donation['blood_group'],
                "volume_ml": random.randint(150, 300),
                "collection_date": donation['donation_date'],
                "expiry_date": comp_expiry.strftime("%Y-%m-%d"),
                "status": status,
                "storage_location": f"Storage-{comp_type[:3].upper()}-{random.randint(1, 5)}",
                "qc_status": "passed",
                "org_id": org_id,
                "created_at": donation['created_at'],
            }
            components.append(component)
    
    await db.blood_units.insert_many(blood_units)
    await db.components.insert_many(components)
    print(f"   ✓ Created {len(blood_units)} blood units")
    print(f"   ✓ Created {len(components)} components")
    
    # ========================================
    # 6. BLOOD REQUESTS (5 requests in various states)
    # ========================================
    print("\n📝 Creating Blood Requests...")
    requests = []
    request_statuses = ['pending', 'approved', 'fulfilled', 'pending', 'approved']
    
    for i, status in enumerate(request_statuses):
        request = {
            "id": str(uuid.uuid4()),
            "request_id": f"REQ-{2024000 + i}",
            "request_type": "internal",
            "requester_name": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "requester_contact": generate_phone(),
            "hospital_name": f"{random.choice(['General', 'University', 'Central', 'City'])} Hospital",
            "hospital_address": f"{random.randint(1, 100)} Jalan Hospital",
            "patient_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "patient_diagnosis": random.choice(['Surgery', 'Trauma', 'Anemia', 'Cancer Treatment', 'Childbirth']),
            "blood_group": random.choice(BLOOD_GROUPS),
            "product_type": random.choice(COMPONENT_TYPES),
            "quantity": random.randint(1, 4),
            "urgency": random.choice(['normal', 'urgent', 'emergency']),
            "status": status,
            "requested_date": random_date_between(1, 7),
            "required_by_date": (datetime.now(timezone.utc) + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d"),
            "notes": "Please process urgently" if status != 'pending' else "",
            "org_id": org_id,
            "created_at": random_date_between(1, 10),
            "created_by": admin_id,
        }
        requests.append(request)
    
    await db.blood_requests.insert_many(requests)
    print(f"   ✓ Created {len(requests)} blood requests")
    
    # ========================================
    # 7. REQUESTORS (3 hospital requestors)
    # ========================================
    print("\n🏥 Creating Requestors...")
    requestors = []
    requestor_statuses = ['approved', 'approved', 'pending']
    hospitals = ['City General Hospital', 'University Medical Center', 'Metro Clinic']
    
    for i, (status, hospital) in enumerate(zip(requestor_statuses, hospitals)):
        city_info = random.choice(CITIES)
        email = f"admin@{hospital.lower().replace(' ', '')}.com"
        
        requestor = {
            "id": str(uuid.uuid4()),
            "organization_name": hospital,
            "organization_type": random.choice(['hospital', 'clinic']),
            "registration_number": f"REG-{random.randint(10000, 99999)}",
            "contact_person": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "designation": random.choice(['Medical Director', 'Chief Medical Officer', 'Administrator']),
            "email": email,
            "phone": generate_phone(),
            "address": f"{random.randint(1, 200)} Jalan {random.choice(['Kesihatan', 'Hospital', 'Medik'])}",
            "city": city_info['city'],
            "state": city_info['state'],
            "pincode": f"{random.randint(10000, 99999)}",
            "latitude": city_info['lat'] + random.uniform(-0.05, 0.05),
            "longitude": city_info['lng'] + random.uniform(-0.05, 0.05),
            "status": status,
            "password_hash": pwd_context.hash("Hospital@123"),
            "approved_by": admin_id if status == 'approved' else None,
            "approved_at": random_date_between(1, 30) if status == 'approved' else None,
            "created_at": random_date_between(5, 60),
        }
        requestors.append(requestor)
    
    await db.requestors.insert_many(requestors)
    print(f"   ✓ Created {len(requestors)} requestors")
    
    # ========================================
    # 8. BROADCASTS (Network alerts)
    # ========================================
    print("\n📢 Creating Broadcasts...")
    broadcasts = []
    broadcast_types = ['urgent_need', 'surplus_alert', 'urgent_need']
    
    for i, btype in enumerate(broadcast_types):
        broadcast = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "org_name": test_org['org_name'],
            "broadcast_type": btype,
            "blood_group": random.choice(BLOOD_GROUPS),
            "component_type": random.choice(COMPONENT_TYPES),
            "units_needed": random.randint(2, 10) if btype == 'urgent_need' else None,
            "units_available": random.randint(5, 20) if btype == 'surplus_alert' else None,
            "priority": random.choice(['normal', 'high', 'critical']),
            "title": f"{'Urgent: Blood Needed' if btype == 'urgent_need' else 'Surplus Available'} - {random.choice(BLOOD_GROUPS)}",
            "description": f"{'We urgently need blood units for critical patients.' if btype == 'urgent_need' else 'We have surplus units available for transfer.'}",
            "contact_name": f"Dr. {random.choice(FIRST_NAMES)}",
            "contact_phone": generate_phone(),
            "visibility": "network_wide",
            "status": "active",
            "response_count": random.randint(0, 3),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
            "created_by": admin_id,
            "created_at": random_date_between(0, 2),
        }
        broadcasts.append(broadcast)
    
    await db.broadcasts.insert_many(broadcasts)
    print(f"   ✓ Created {len(broadcasts)} broadcasts")
    
    # ========================================
    # 9. INTER-ORG REQUESTS
    # ========================================
    print("\n🔄 Creating Inter-Org Requests...")
    inter_org_requests = []
    
    for i in range(3):
        req = {
            "id": str(uuid.uuid4()),
            "request_type": "internal",
            "requesting_org_id": org_id,
            "fulfilling_org_id": org_id,  # Self-request for demo
            "component_type": random.choice(COMPONENT_TYPES),
            "blood_group": random.choice(BLOOD_GROUPS),
            "quantity": random.randint(1, 5),
            "urgency_level": random.choice(['routine', 'urgent', 'emergency']),
            "clinical_indication": f"Patient: {random.choice(FIRST_NAMES)} - {random.choice(['Surgery', 'Trauma', 'Transfusion'])}",
            "status": random.choice(['pending', 'approved', 'dispatched']),
            "created_by": admin_id,
            "created_at": random_date_between(0, 5),
            "updated_at": random_date_between(0, 3),
        }
        inter_org_requests.append(req)
    
    await db.inter_org_requests.insert_many(inter_org_requests)
    print(f"   ✓ Created {len(inter_org_requests)} inter-org requests")
    
    # ========================================
    # 10. STORAGE LOCATIONS
    # ========================================
    print("\n🗄️ Creating Storage Locations...")
    storage_locations = [
        {"id": str(uuid.uuid4()), "name": "Main Refrigerator", "type": "refrigerator", "temperature_min": 2, "temperature_max": 6, "capacity": 500, "current_count": len([c for c in components if c['status'] == 'ready_to_use']), "status": "active", "org_id": org_id},
        {"id": str(uuid.uuid4()), "name": "Freezer Unit A", "type": "freezer", "temperature_min": -30, "temperature_max": -18, "capacity": 200, "current_count": 45, "status": "active", "org_id": org_id},
        {"id": str(uuid.uuid4()), "name": "Platelet Incubator", "type": "incubator", "temperature_min": 20, "temperature_max": 24, "capacity": 50, "current_count": 12, "status": "active", "org_id": org_id},
    ]
    
    await db.storage_locations.insert_many(storage_locations)
    print(f"   ✓ Created {len(storage_locations)} storage locations")
    
    # ========================================
    # 11. AUDIT LOGS (Sample entries)
    # ========================================
    print("\n📋 Creating Audit Logs...")
    audit_actions = [
        ("login", "auth", "User logged in successfully"),
        ("create", "donors", "New donor registered"),
        ("create", "donations", "Blood donation recorded"),
        ("update", "components", "Component status updated"),
        ("create", "requests", "Blood request created"),
        ("approve", "requests", "Blood request approved"),
    ]
    
    audit_logs = []
    for i in range(20):
        action, module, desc = random.choice(audit_actions)
        log = {
            "id": str(uuid.uuid4()),
            "user_id": admin_id,
            "user_email": "admin@testorg.com",
            "user_type": "super_admin",
            "action": action,
            "module": module,
            "description": desc,
            "ip_address": f"192.168.1.{random.randint(1, 255)}",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "org_id": org_id,
            "created_at": random_date_between(0, 30),
        }
        audit_logs.append(log)
    
    await db.audit_logs.insert_many(audit_logs)
    print(f"   ✓ Created {len(audit_logs)} audit logs")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("✅ DEMO DATA SEEDING COMPLETE!")
    print("=" * 60)
    print(f"""
Summary of created data:
------------------------
• Donors:            {len(donors)}
• Donations:         {len(donations)}
• Screenings:        {len(screenings)}
• Lab Tests:         {len(lab_tests)}
• Blood Units:       {len(blood_units)}
• Components:        {len(components)}
• Blood Requests:    {len(requests)}
• Requestors:        {len(requestors)}
• Broadcasts:        {len(broadcasts)}
• Inter-Org Requests: {len(inter_org_requests)}
• Storage Locations: {len(storage_locations)}
• Audit Logs:        {len(audit_logs)}

Test Credentials:
-----------------
Staff Login:
  Email: admin@testorg.com
  Password: Test@123

Requestor Login (after approval):
  Email: admin@citygeneralhospital.com
  Password: Hospital@123
  
Demo workflow ready for:
  1. Donor Registration → Screening → Lab Testing → Processing
  2. Blood Inventory Management (Components ready for use)
  3. Blood Requests → Approval → Fulfillment
  4. Network Broadcasts (Urgent needs & Surplus alerts)
  5. Inter-Organization Blood Transfers
  6. Requestor Portal (Hospital blood ordering)
""")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
