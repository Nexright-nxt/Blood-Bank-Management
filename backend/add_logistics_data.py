"""
Add Logistics demo data - Shipments, Issuances, and Vehicles
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

HOSPITALS = [
    {"name": "City General Hospital", "address": "123 Healthcare Ave, Medical District", "contact": "Dr. Rajiv Sharma", "phone": "+91 98765 12345"},
    {"name": "Apollo Medical Center", "address": "456 Wellness Road, Health City", "contact": "Dr. Priya Mehta", "phone": "+91 98765 23456"},
    {"name": "Max Super Specialty", "address": "789 Care Street, Medicity", "contact": "Dr. Arun Kumar", "phone": "+91 98765 34567"},
    {"name": "Fortis Hospital", "address": "321 Life Blvd, Hospital Zone", "contact": "Dr. Sunita Gupta", "phone": "+91 98765 45678"},
    {"name": "AIIMS Emergency Ward", "address": "555 Emergency Lane, Critical Care", "contact": "Dr. Vikram Singh", "phone": "+91 98765 56789"},
]

VEHICLE_TYPES = [
    {"type": "ambulance", "model": "Force Traveller Ambulance", "reg": "MH-01-AB-1234", "temp_range": "2-8°C"},
    {"type": "refrigerated_van", "model": "Tata Ace Reefer", "reg": "MH-01-CD-5678", "temp_range": "2-6°C"},
    {"type": "bike", "model": "Honda Activa (Cold Box)", "reg": "MH-01-EF-9012", "temp_range": "2-10°C"},
]

COURIER_COMPANIES = [
    {"name": "BlueDart Medical", "contact": "+91 1800 123 4567", "tracking_prefix": "BD"},
    {"name": "DHL Healthcare", "contact": "+91 1800 234 5678", "tracking_prefix": "DHL"},
    {"name": "FedEx Medical Express", "contact": "+91 1800 345 6789", "tracking_prefix": "FX"},
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

async def add_logistics_data():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Fetching existing data...")
    
    # Get org_id
    org = await db.organizations.find_one({"org_code": "TEST001"}, {"_id": 0})
    if not org:
        print("ERROR: Test organization not found!")
        return
    
    org_id = org["id"]
    print(f"Organization ID: {org_id}")
    
    # Get users
    admin = await db.users.find_one({"email": "admin@testorg.com"}, {"_id": 0})
    inventory = await db.users.find_one({"email": "inventory@testorg.com"}, {"_id": 0})
    dispatcher = inventory if inventory else admin
    
    # Get available components for issuances
    available_components = await db.components.find({
        "org_id": org_id,
        "status": {"$in": ["available", "ready_to_use"]}
    }, {"_id": 0}).to_list(50)
    
    print(f"Found {len(available_components)} available components")
    
    # ========================================
    # 1. Create Vehicles
    # ========================================
    print("\n=== Creating Vehicles ===")
    
    new_vehicles = []
    for i, v in enumerate(VEHICLE_TYPES):
        vehicle = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "vehicle_id": f"VEH-{i+1:03d}",
            "vehicle_type": v["type"],
            "vehicle_model": v["model"],
            "registration_number": v["reg"],
            "temperature_range": v["temp_range"],
            "capacity": random.choice(["10 units", "20 units", "5 units"]),
            "driver_name": random.choice(["Ramesh Kumar", "Sunil Sharma", "Deepak Singh"]),
            "driver_phone": f"+91 98765 {random.randint(10000, 99999)}",
            "driver_license": f"MH-{random.randint(1000000000, 9999999999)}",
            "is_active": True,
            "status": "available",
            "last_maintenance": (datetime.now(timezone.utc) - timedelta(days=random.randint(10, 60))).strftime("%Y-%m-%d"),
            "next_maintenance": (datetime.now(timezone.utc) + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        new_vehicles.append(vehicle)
        print(f"  Created vehicle: {v['model']} ({v['reg']})")
    
    # ========================================
    # 2. Create Couriers
    # ========================================
    print("\n=== Creating Courier Companies ===")
    
    new_couriers = []
    for c in COURIER_COMPANIES:
        courier = {
            "id": str(uuid.uuid4()),
            "org_id": org_id,
            "name": c["name"],
            "contact_number": c["contact"],
            "tracking_url_template": f"https://{c['name'].lower().replace(' ', '')}.com/track/{{tracking_number}}",
            "is_active": True,
            "service_types": ["same_day", "next_day", "express"],
            "coverage_areas": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        new_couriers.append(courier)
        print(f"  Created courier: {c['name']}")
    
    # ========================================
    # 3. Create Blood Requests (for issuances)
    # ========================================
    print("\n=== Creating Blood Requests ===")
    
    new_requests = []
    new_issuances = []
    new_shipments = []
    
    request_count = await db.blood_requests.count_documents({"org_id": org_id})
    issuance_count = await db.issuances.count_documents({"org_id": org_id})
    shipment_count = await db.shipments.count_documents({})
    
    # Scenario 1: Shipments preparing (need to dispatch)
    # Scenario 2: Shipments in transit
    # Scenario 3: Shipments delivered
    # Scenario 4: Approved issuances ready to ship
    
    scenarios = [
        {"shipment_status": "preparing", "issuance_status": "dispatching"},
        {"shipment_status": "preparing", "issuance_status": "dispatching"},
        {"shipment_status": "in_transit", "issuance_status": "dispatching"},
        {"shipment_status": "in_transit", "issuance_status": "dispatching"},
        {"shipment_status": "delivered", "issuance_status": "completed"},
        {"shipment_status": None, "issuance_status": "approved"},  # Ready to ship
        {"shipment_status": None, "issuance_status": "approved"},  # Ready to ship
    ]
    
    for idx, scenario in enumerate(scenarios):
        hospital = HOSPITALS[idx % len(HOSPITALS)]
        blood_group = BLOOD_GROUPS[idx % len(BLOOD_GROUPS)]
        
        request_num = request_count + idx + 1
        issuance_num = issuance_count + idx + 1
        
        request_id = str(uuid.uuid4())
        issuance_id = str(uuid.uuid4())
        
        base_date = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5), hours=random.randint(0, 12))
        
        # Create blood request
        request = {
            "id": request_id,
            "org_id": org_id,
            "request_id": f"REQ-2026-{request_num:06d}",
            "request_number": f"REQ-2026-{request_num:06d}",
            "patient_name": f"Patient {idx + 1}",
            "patient_id": f"PAT-{random.randint(1000, 9999)}",
            "blood_group": blood_group,
            "component_type": random.choice(["prbc", "ffp", "platelets"]),
            "units_required": random.randint(1, 3),
            "priority": random.choice(["routine", "urgent", "emergency"]),
            "hospital_name": hospital["name"],
            "hospital_address": hospital["address"],
            "doctor_name": hospital["contact"],
            "doctor_phone": hospital["phone"],
            "diagnosis": random.choice(["Anemia", "Surgery", "Trauma", "Chemotherapy", "Delivery"]),
            "status": "fulfilled" if scenario["issuance_status"] in ["dispatching", "completed"] else "approved",
            "requested_by": admin["email"],
            "requested_at": base_date.isoformat(),
            "created_at": base_date.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        new_requests.append(request)
        
        # Create issuance
        issuance = {
            "id": issuance_id,
            "org_id": org_id,
            "issue_id": f"ISS-2026-{issuance_num:06d}",
            "issuance_number": f"ISS-2026-{issuance_num:06d}",
            "request_id": request_id,
            "request_number": request["request_number"],
            "patient_name": request["patient_name"],
            "patient_id": request["patient_id"],
            "blood_group": blood_group,
            "hospital_name": hospital["name"],
            "hospital_address": hospital["address"],
            "contact_person": hospital["contact"],
            "contact_phone": hospital["phone"],
            "units_issued": random.randint(1, 2),
            "status": scenario["issuance_status"],
            "issued_by": dispatcher["email"],
            "issued_by_name": dispatcher["full_name"],
            "issued_at": (base_date + timedelta(hours=1)).isoformat(),
            "approved_by": admin["email"],
            "approved_at": (base_date + timedelta(hours=2)).isoformat(),
            "created_at": base_date.isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        new_issuances.append(issuance)
        
        # Create shipment if applicable
        if scenario["shipment_status"]:
            shipment_num = shipment_count + len(new_shipments) + 1
            shipment_date = base_date + timedelta(hours=3)
            
            is_self_vehicle = random.choice([True, False])
            vehicle = random.choice(new_vehicles) if is_self_vehicle else None
            courier = random.choice(COURIER_COMPANIES) if not is_self_vehicle else None
            
            tracking_updates = [
                {
                    "timestamp": shipment_date.isoformat(),
                    "location": "Blood Bank - Dispatch Center",
                    "status": "preparing",
                    "updated_by": dispatcher["id"],
                    "notes": "Shipment created and being prepared"
                }
            ]
            
            if scenario["shipment_status"] in ["in_transit", "delivered"]:
                tracking_updates.append({
                    "timestamp": (shipment_date + timedelta(hours=1)).isoformat(),
                    "location": "Blood Bank - Exit Gate",
                    "status": "picked_up",
                    "updated_by": dispatcher["id"],
                    "notes": "Shipment picked up by driver"
                })
                tracking_updates.append({
                    "timestamp": (shipment_date + timedelta(hours=2)).isoformat(),
                    "location": "En route to " + hospital["name"],
                    "status": "in_transit",
                    "updated_by": dispatcher["id"],
                    "notes": "Temperature: 4°C, Conditions: Stable"
                })
            
            if scenario["shipment_status"] == "delivered":
                tracking_updates.append({
                    "timestamp": (shipment_date + timedelta(hours=4)).isoformat(),
                    "location": hospital["name"],
                    "status": "delivered",
                    "updated_by": dispatcher["id"],
                    "notes": "Delivered to blood bank reception. Received by: " + hospital["contact"]
                })
            
            shipment = {
                "id": str(uuid.uuid4()),
                "org_id": org_id,
                "shipment_id": f"SHP-{datetime.now().strftime('%Y%m%d')}-{shipment_num:04d}",
                "tracking_number": f"TRK{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(10000000, 99999999)}",
                "issuance_id": issuance_id,
                "request_id": request_id,
                "destination": hospital["name"],
                "destination_address": hospital["address"],
                "contact_person": hospital["contact"],
                "contact_phone": hospital["phone"],
                "transport_method": "self_vehicle" if is_self_vehicle else "third_party",
                "vehicle_id": vehicle["id"] if vehicle else None,
                "vehicle_details": {
                    "vehicle_type": vehicle["vehicle_type"],
                    "vehicle_model": vehicle["vehicle_model"],
                    "registration_number": vehicle["registration_number"]
                } if vehicle else None,
                "driver_name": vehicle["driver_name"] if vehicle else None,
                "driver_phone": vehicle["driver_phone"] if vehicle else None,
                "driver_license": vehicle["driver_license"] if vehicle else None,
                "courier_company": courier["name"] if courier else None,
                "courier_contact": courier["contact"] if courier else None,
                "courier_tracking_number": f"{courier['tracking_prefix']}{random.randint(1000000000, 9999999999)}" if courier else None,
                "status": scenario["shipment_status"],
                "current_location": tracking_updates[-1]["location"],
                "estimated_arrival": (shipment_date + timedelta(hours=5)).isoformat(),
                "actual_arrival": (shipment_date + timedelta(hours=4)).isoformat() if scenario["shipment_status"] == "delivered" else None,
                "special_instructions": "Maintain cold chain. Handle with care.",
                "tracking_updates": tracking_updates,
                "temperature_log": [
                    {"timestamp": (shipment_date + timedelta(minutes=m)).isoformat(), "temperature": round(random.uniform(2.5, 5.5), 1)}
                    for m in range(0, 240, 30)
                ] if scenario["shipment_status"] != "preparing" else [],
                "created_by": dispatcher["id"],
                "created_by_name": dispatcher["full_name"],
                "created_at": shipment_date.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            new_shipments.append(shipment)
            
            # Update issuance with shipment ID
            issuance["shipment_id"] = shipment["id"]
            
            status_label = scenario["shipment_status"].replace("_", " ").title()
            print(f"  Created shipment {shipment['shipment_id']} -> {hospital['name']} [{status_label}]")
        else:
            print(f"  Created issuance {issuance['issue_id']} -> {hospital['name']} [Ready to Ship]")
    
    # ========================================
    # Insert all data
    # ========================================
    print("\n=== Inserting data into database ===")
    
    if new_vehicles:
        # Check if vehicles collection exists and clear old test vehicles
        await db.vehicles.delete_many({"org_id": org_id})
        await db.vehicles.insert_many(new_vehicles)
        print(f"  Inserted {len(new_vehicles)} vehicles")
    
    if new_couriers:
        await db.couriers.delete_many({"org_id": org_id})
        await db.couriers.insert_many(new_couriers)
        print(f"  Inserted {len(new_couriers)} courier companies")
    
    if new_requests:
        await db.blood_requests.insert_many(new_requests)
        print(f"  Inserted {len(new_requests)} blood requests")
    
    if new_issuances:
        await db.issuances.insert_many(new_issuances)
        print(f"  Inserted {len(new_issuances)} issuances")
    
    if new_shipments:
        await db.shipments.insert_many(new_shipments)
        print(f"  Inserted {len(new_shipments)} shipments")
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "="*60)
    print("SUMMARY - LOGISTICS DATA")
    print("="*60)
    
    preparing = await db.shipments.count_documents({"status": "preparing"})
    in_transit = await db.shipments.count_documents({"status": "in_transit"})
    delivered = await db.shipments.count_documents({"status": "delivered"})
    ready_to_ship = await db.issuances.count_documents({"org_id": org_id, "status": "approved"})
    
    print(f"\nLOGISTICS DASHBOARD:")
    print(f"  Preparing: {preparing} shipments")
    print(f"  In Transit: {in_transit} shipments")
    print(f"  Delivered: {delivered} shipments")
    print(f"  Ready to Ship: {ready_to_ship} issuances")
    print(f"\nVehicles: {len(new_vehicles)}")
    print(f"Courier Companies: {len(new_couriers)}")
    
    print("\n" + "="*60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_logistics_data())
