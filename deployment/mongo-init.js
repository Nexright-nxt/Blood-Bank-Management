// MongoDB Initialization Script
// Creates database user for Blood Link

db = db.getSiblingDB('bloodlink_production');

db.createUser({
  user: 'bloodlink_user',
  pwd: 'bloodlink_password',  // Change this in production!
  roles: [
    { role: 'readWrite', db: 'bloodlink_production' }
  ]
});

// Create initial indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.organizations.createIndex({ "org_code": 1 }, { unique: true, sparse: true });
db.donors.createIndex({ "donor_code": 1 }, { unique: true, sparse: true });
db.blood_units.createIndex({ "unit_id": 1 }, { unique: true, sparse: true });
db.components.createIndex({ "component_id": 1 }, { unique: true, sparse: true });
db.audit_logs.createIndex({ "timestamp": -1 });

print('Blood Link database initialized successfully');
