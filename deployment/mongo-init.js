// MongoDB Initialization Script
// Creates database user for BBMS

db = db.getSiblingDB('bbms_production');

db.createUser({
  user: 'bbms_user',
  pwd: 'bbms_password',  // Change this in production!
  roles: [
    { role: 'readWrite', db: 'bbms_production' }
  ]
});

// Create initial indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.organizations.createIndex({ "org_code": 1 }, { unique: true, sparse: true });
db.donors.createIndex({ "donor_code": 1 }, { unique: true, sparse: true });
db.blood_units.createIndex({ "unit_id": 1 }, { unique: true, sparse: true });
db.components.createIndex({ "component_id": 1 }, { unique: true, sparse: true });
db.audit_logs.createIndex({ "timestamp": -1 });

print('BBMS database initialized successfully');
