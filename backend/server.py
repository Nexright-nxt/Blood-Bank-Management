"""
Blood Link - Blood Bank Management System API
Modular FastAPI application with separate routers for each module.
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import db, client
from services import hash_password
from routers import (
    auth_router, users_router, donors_router, screening_router,
    donations_router, blood_units_router, custody_router, laboratory_router,
    components_router, quarantine_router, qc_validation_router, inventory_router,
    requests_router, issuance_router, return_router, discard_router,
    reports_router, dashboard_router, alerts_router,
    storage_router, pre_lab_qc_router, notifications_router,
    logistics_router, labels_router, inventory_enhanced_router,
    relationships_router, donors_enhanced_router,
    configuration_router, logistics_enhanced_router,
    organizations_router, inter_org_requests_router,
    audit_logs_router, sessions_router, documents_router,
    compliance_router, training_router, security_router, sensitive_actions_router,
    backups_router, roles_router, requestors_router, blood_link_router,
    broadcasts_router
)
from routers.roles import seed_system_roles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_default_admin()
    await seed_system_roles()  # Seed system roles
    await seed_demo_data_if_empty()  # Seed demo data if database is empty
    yield
    # Shutdown
    client.close()

# Create FastAPI app
app = FastAPI(
    title="Blood Link - Blood Bank Management System",
    description="Comprehensive API for blood bank operations management",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": "Blood Link API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Include all routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(donors_router, prefix="/api")
app.include_router(screening_router, prefix="/api")
app.include_router(donations_router, prefix="/api")
app.include_router(blood_units_router, prefix="/api")
app.include_router(custody_router, prefix="/api")
app.include_router(laboratory_router, prefix="/api")
app.include_router(components_router, prefix="/api")
app.include_router(quarantine_router, prefix="/api")
app.include_router(qc_validation_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(requests_router, prefix="/api")
app.include_router(issuance_router, prefix="/api")
app.include_router(return_router, prefix="/api")
app.include_router(discard_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(storage_router, prefix="/api")
app.include_router(pre_lab_qc_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(logistics_router, prefix="/api")
app.include_router(labels_router, prefix="/api")
app.include_router(inventory_enhanced_router, prefix="/api")
app.include_router(relationships_router, prefix="/api")
app.include_router(donors_enhanced_router, prefix="/api")
app.include_router(configuration_router, prefix="/api")
app.include_router(logistics_enhanced_router, prefix="/api")
app.include_router(organizations_router, prefix="/api")
app.include_router(inter_org_requests_router, prefix="/api")
app.include_router(audit_logs_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(compliance_router, prefix="/api")
app.include_router(training_router, prefix="/api")
app.include_router(security_router, prefix="/api")
app.include_router(sensitive_actions_router, prefix="/api")
app.include_router(backups_router, prefix="/api")
app.include_router(roles_router, prefix="/api")
app.include_router(requestors_router, prefix="/api")
app.include_router(blood_link_router, prefix="/api")
app.include_router(broadcasts_router, prefix="/api")


async def create_default_admin():
    """Create default organization and admin user if none exists"""
    # Create default organization if none exists
    default_org = await db.organizations.find_one({"org_name": "BloodLink Central"})
    if not default_org:
        default_org_id = str(uuid.uuid4())
        default_org = {
            "id": default_org_id,
            "org_name": "BloodLink Central",
            "org_type": "standalone",
            "parent_org_id": None,
            "is_parent": True,
            "address": "Central Blood Bank",
            "city": "Main City",
            "state": "State",
            "country": "Country",
            "contact_person": "Admin",
            "contact_email": "admin@bloodbank.com",
            "license_number": "LIC-001",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.organizations.insert_one(default_org)
        logger.info(f"Default organization created: BloodLink Central (ID: {default_org_id})")
    else:
        default_org_id = default_org["id"]
    
    # Create or update default admin user
    admin_exists = await db.users.find_one({"email": "admin@bloodbank.com"})
    if not admin_exists:
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": "admin@bloodbank.com",
            "password_hash": hash_password("adminpassword"),
            "full_name": "System Admin",
            "role": "admin",
            "org_id": None,  # System admin has no specific org
            "user_type": "system_admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_user)
        logger.info("Default system admin user created: admin@bloodbank.com")
    else:
        # Update existing admin to be system admin
        if admin_exists.get("user_type") != "system_admin":
            await db.users.update_one(
                {"email": "admin@bloodbank.com"},
                {"$set": {
                    "user_type": "system_admin",
                    "org_id": None,
                    "full_name": "System Admin",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info("Upgraded admin to system_admin")
    
    # Migrate existing data - add org_id to collections that don't have it
    collections_to_migrate = [
        "donors", "donations", "screenings", "blood_units", "components",
        "lab_tests", "storage_locations", "blood_requests", "issuances",
        "discards", "returns", "logistics", "notifications", "quarantine",
        "qc_validations", "pre_lab_qc", "chain_custody"
    ]
    
    for collection_name in collections_to_migrate:
        collection = db[collection_name]
        # Update documents that don't have org_id
        result = await collection.update_many(
            {"org_id": {"$exists": False}},
            {"$set": {"org_id": default_org_id}}
        )
        if result.modified_count > 0:
            logger.info(f"Migrated {result.modified_count} documents in {collection_name} to org_id: {default_org_id}")


async def seed_demo_data_if_empty():
    """Seed demo data if the database is empty (for demo purposes)"""
    import bcrypt
    import random
    
    # Check if demo data already exists
    donor_count = await db.donors.count_documents({})
    if donor_count > 0:
        logger.info(f"Demo data already exists ({donor_count} donors). Skipping seeding.")
        return
    
    logger.info("Database is empty. Seeding demo data...")
    
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
    HOSPITALS = ['Hospital Kuala Lumpur', 'Hospital Selayang', 'Hospital Sungai Buloh', 'Pusat Perubatan Universiti Malaya']
    
    def hash_pw(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def gen_phone():
        return f"+60-{random.choice(['11', '12', '13', '14', '16', '17', '18', '19'])}-{random.randint(1000000, 9999999)}"
    
    def gen_mykad():
        return f"{random.randint(70, 99):02d}{random.randint(1, 12):02d}{random.randint(1, 28):02d}-{random.randint(1, 14):02d}-{random.randint(1000, 9999)}"
    
    def rand_date(days_min, days_max):
        from datetime import timedelta
        days = random.randint(days_min, days_max)
        return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    try:
        # 1. Create Organization
        org_id = str(uuid.uuid4())
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
            "latitude": city['lat'],
            "longitude": city['lng'],
            "location": {"type": "Point", "coordinates": [city['lng'], city['lat']]},
            "contact_person": "Dr. Ahmad bin Hassan",
            "contact_phone": "+60-3-26132688",
            "contact_email": "admin@pdn.gov.my",
            "license_number": "PDN-001-2024",
            "is_active": True,
            "blood_link_visible": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.organizations.insert_one(org)
        await db.organizations.create_index([("location", "2dsphere")])
        
        # 2. Create Admin User
        admin_id = str(uuid.uuid4())
        admin = {
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
        }
        await db.users.insert_one(admin)
        
        # Create staff users
        staff_ids = []
        for email, name, role in [("labtech@pdn.gov.my", "Siti Aminah", "lab_technician"), 
                                   ("nurse@pdn.gov.my", "Nurse Fatimah", "registration")]:
            sid = str(uuid.uuid4())
            staff_ids.append(sid)
            await db.users.insert_one({
                "id": sid, "email": email, "password_hash": hash_pw("Staff@123"),
                "full_name": name, "phone": gen_phone(), "role": role, "user_type": "staff",
                "org_id": org_id, "org_name": org['org_name'], "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        
        logger.info(f"Created organization: {org['org_name']}")
        logger.info(f"Created admin: admin@pdn.gov.my / Admin@123")
        
        # 3. Create Donors
        donors = []
        for i in range(20):
            city = random.choice(CITIES)
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            donor = {
                "id": str(uuid.uuid4()),
                "donor_id": f"PDN-D-{2024001 + i}",
                "id_type": random.choice(['mykad', 'mykas', 'passport']),
                "id_number": gen_mykad(),
                "first_name": first, "last_name": last, "full_name": f"{first} {last}",
                "date_of_birth": f"{random.randint(1965, 2000)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "gender": random.choice(['male', 'female']),
                "blood_group": random.choice(BLOOD_GROUPS),
                "phone": gen_phone(),
                "email": f"{first.lower()}.{last.lower()}{random.randint(10,99)}@email.com.my",
                "address": f"No. {random.randint(1, 200)}, Jalan {random.choice(['Merdeka', 'Ampang', 'Cheras'])}",
                "city": city['city'], "state": city['state'], "country": "Malaysia",
                "latitude": city['lat'] + random.uniform(-0.02, 0.02),
                "longitude": city['lng'] + random.uniform(-0.02, 0.02),
                "status": "eligible", "eligibility_status": "eligible",
                "donation_count": random.randint(0, 15),
                "org_id": org_id,
                "created_at": rand_date(30, 180),
                "created_by": admin_id,
            }
            donors.append(donor)
        await db.donors.insert_many(donors)
        logger.info(f"Created {len(donors)} donors")
        
        # 4. Create Screenings & Donations
        screenings, donations, lab_tests, blood_units, components = [], [], [], [], []
        for i, donor in enumerate(donors[:12]):
            scr_id, don_id, lab_id, unit_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
            scr_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
            
            screenings.append({
                "id": scr_id, "screening_id": f"PDN-SCR-{2024001+i}",
                "donor_id": donor['id'], "donor_name": donor['full_name'],
                "screening_date": scr_date.strftime("%Y-%m-%d"),
                "hemoglobin": round(random.uniform(12.5, 16.5), 1),
                "blood_pressure_systolic": random.randint(100, 140),
                "blood_pressure_diastolic": random.randint(60, 90),
                "pulse": random.randint(60, 100),
                "temperature": round(random.uniform(36.0, 37.5), 1),
                "weight_kg": round(random.uniform(50, 90), 1),
                "preliminary_blood_group": donor['blood_group'],
                "eligibility_status": "eligible",
                "screened_by": random.choice(staff_ids),
                "org_id": org_id, "created_at": scr_date.isoformat(),
            })
            
            don_date = scr_date + timedelta(minutes=30)
            donations.append({
                "id": don_id, "donation_id": f"PDN-DON-{2024001+i}",
                "donor_id": donor['id'], "donor_name": donor['full_name'],
                "screening_id": scr_id, "blood_group": donor['blood_group'],
                "donation_type": random.choice(['whole_blood', 'apheresis_platelet']),
                "donation_date": don_date.strftime("%Y-%m-%d"),
                "collection_start_time": don_date.isoformat(),
                "collection_end_time": (don_date + timedelta(minutes=12)).isoformat(),
                "volume_collected": random.choice([350, 450, 500]),
                "status": "completed",
                "phlebotomist_id": random.choice(staff_ids),
                "org_id": org_id, "created_at": don_date.isoformat(),
            })
            
            lab_tests.append({
                "id": lab_id, "test_id": f"PDN-LAB-{2024001+i}",
                "donation_id": don_id, "donor_id": donor['id'],
                "blood_group_confirmed": donor['blood_group'],
                "hiv_elisa": "negative", "hiv_nat": "negative",
                "hbsag": "negative", "anti_hcv": "negative",
                "syphilis_rpr": "negative", "malaria_antigen": "negative",
                "overall_result": "pass", "status": "completed",
                "tested_by": random.choice(staff_ids),
                "org_id": org_id, "created_at": (don_date + timedelta(hours=2)).isoformat(),
            })
            
            blood_units.append({
                "id": unit_id, "unit_id": f"PDN-BU-{2024001+i}",
                "donation_id": don_id, "donor_id": donor['id'],
                "blood_group": donor['blood_group'],
                "volume": donations[-1]['volume_collected'],
                "collection_date": don_date.strftime("%Y-%m-%d"),
                "expiry_date": (don_date + timedelta(days=42)).strftime("%Y-%m-%d"),
                "status": "processed",
                "org_id": org_id, "created_at": don_date.isoformat(),
            })
            
            for j, ct in enumerate(random.sample(COMPONENT_TYPES, 3)):
                components.append({
                    "id": str(uuid.uuid4()), "component_id": f"PDN-CMP-{2024001+i}-{j+1}",
                    "blood_unit_id": unit_id, "donation_id": don_id, "donor_id": donor['id'],
                    "component_type": ct, "blood_group": donor['blood_group'],
                    "volume_ml": random.randint(150, 300),
                    "collection_date": don_date.strftime("%Y-%m-%d"),
                    "expiry_date": (don_date + timedelta(days=42 if ct == 'prc' else 5 if ct == 'platelets' else 365)).strftime("%Y-%m-%d"),
                    "status": random.choice(['available', 'reserved', 'issued']),
                    "qc_status": "passed",
                    "org_id": org_id, "created_at": don_date.isoformat(),
                })
        
        await db.screenings.insert_many(screenings)
        await db.donations.insert_many(donations)
        await db.lab_tests.insert_many(lab_tests)
        await db.blood_units.insert_many(blood_units)
        await db.components.insert_many(components)
        logger.info(f"Created {len(screenings)} screenings, {len(donations)} donations, {len(components)} components")
        
        # 5. Create Blood Requests
        requests = []
        for i in range(8):
            requests.append({
                "id": str(uuid.uuid4()), "request_id": f"PDN-REQ-{2024001+i}",
                "request_type": random.choice(['routine', 'urgent', 'emergency']),
                "requester_name": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "requester_contact": gen_phone(),
                "hospital_name": random.choice(HOSPITALS),
                "patient_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "blood_group": random.choice(BLOOD_GROUPS),
                "product_type": random.choice(COMPONENT_TYPES),
                "quantity": random.randint(1, 5),
                "urgency": random.choice(['routine', 'urgent', 'stat']),
                "status": random.choice(['pending', 'approved', 'fulfilled']),
                "requested_date": rand_date(0, 7),
                "org_id": org_id, "created_at": rand_date(0, 10),
            })
        await db.blood_requests.insert_many(requests)
        logger.info(f"Created {len(requests)} blood requests")
        
        # 6. Create Requestors (Hospitals)
        requestors = []
        for i, hospital in enumerate(HOSPITALS[:4]):
            city = random.choice(CITIES)
            requestors.append({
                "id": str(uuid.uuid4()),
                "organization_name": hospital,
                "organization_type": "hospital",
                "contact_person": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "email": f"bloodbank@{hospital.lower().replace(' ', '')}.gov.my",
                "phone": gen_phone(),
                "address": f"Jalan Hospital {random.randint(1, 20)}",
                "city": city['city'], "state": city['state'], "country": "Malaysia",
                "latitude": city['lat'], "longitude": city['lng'],
                "status": "approved" if i < 3 else "pending",
                "password_hash": hash_pw("Hospital@123"),
                "created_at": rand_date(30, 180),
            })
        await db.requestors.insert_many(requestors)
        logger.info(f"Created {len(requestors)} requestors")
        
        # 7. Create Storage Locations
        storage = [
            {"id": str(uuid.uuid4()), "name": "Refrigerator A", "type": "refrigerator", "temperature_min": 2, "temperature_max": 6, "capacity": 500, "current_count": 120, "status": "active", "org_id": org_id},
            {"id": str(uuid.uuid4()), "name": "Freezer Unit 1", "type": "freezer", "temperature_min": -30, "temperature_max": -18, "capacity": 300, "current_count": 80, "status": "active", "org_id": org_id},
            {"id": str(uuid.uuid4()), "name": "Platelet Incubator", "type": "incubator", "temperature_min": 20, "temperature_max": 24, "capacity": 100, "current_count": 25, "status": "active", "org_id": org_id},
        ]
        await db.storage_locations.insert_many(storage)
        logger.info(f"Created {len(storage)} storage locations")
        
        # 8. Create Broadcasts
        broadcasts = []
        for btype in ['urgent_need', 'surplus_alert', 'urgent_need']:
            broadcasts.append({
                "id": str(uuid.uuid4()),
                "org_id": org_id, "org_name": org['org_name'],
                "broadcast_type": btype,
                "blood_group": random.choice(BLOOD_GROUPS),
                "component_type": random.choice(COMPONENT_TYPES),
                "units_needed": random.randint(5, 15) if btype == 'urgent_need' else None,
                "units_available": random.randint(10, 30) if btype == 'surplus_alert' else None,
                "priority": random.choice(['normal', 'high', 'critical']),
                "title": "URGENT: Blood Needed" if btype == 'urgent_need' else "Surplus Available",
                "status": "active",
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
                "created_by": admin_id, "created_at": rand_date(0, 3),
            })
        await db.broadcasts.insert_many(broadcasts)
        logger.info(f"Created {len(broadcasts)} broadcasts")
        
        # 9. Create Audit Logs
        audit_logs = []
        actions = [("login", "auth"), ("create", "donors"), ("create", "donations"), ("update", "components"), ("approve", "requests")]
        for _ in range(20):
            action, module = random.choice(actions)
            audit_logs.append({
                "id": str(uuid.uuid4()),
                "user_id": random.choice([admin_id] + staff_ids),
                "user_email": random.choice(["admin@pdn.gov.my", "labtech@pdn.gov.my", "nurse@pdn.gov.my"]),
                "action": action, "module": module,
                "description": f"{action.title()} operation on {module}",
                "org_id": org_id, "created_at": rand_date(0, 30),
            })
        await db.audit_logs.insert_many(audit_logs)
        logger.info(f"Created {len(audit_logs)} audit logs")
        
        logger.info("=" * 50)
        logger.info("DEMO DATA SEEDING COMPLETE!")
        logger.info("=" * 50)
        logger.info("Login: admin@pdn.gov.my / Admin@123")
        logger.info("Staff: labtech@pdn.gov.my, nurse@pdn.gov.my / Staff@123")
        logger.info("Requestor: bloodbank@hospitalkualalumpur.gov.my / Hospital@123")
        
    except Exception as e:
        logger.error(f"Error seeding demo data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
