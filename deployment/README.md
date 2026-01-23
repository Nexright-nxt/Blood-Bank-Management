# Blood Link - Blood Bank Management System
## Deployment Guide

### Overview
Blood Link is a comprehensive multi-tenant blood bank management system designed for hospital networks, blood banks, and healthcare organizations.

### System Requirements

#### Hardware (Minimum)
- CPU: 2 cores
- RAM: 4 GB
- Storage: 20 GB SSD

#### Hardware (Recommended for Production)
- CPU: 4+ cores
- RAM: 8+ GB
- Storage: 100+ GB SSD

#### Software Requirements
- Node.js 18.x or higher
- Python 3.10 or higher
- MongoDB 6.0 or higher
- Nginx (for production reverse proxy)

---

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        NGINX                                 │
│                   (Reverse Proxy)                           │
│                    Port: 80/443                             │
└─────────────────────┬───────────────────┬───────────────────┘
                      │                   │
         ┌────────────▼────────┐ ┌────────▼────────┐
         │   React Frontend   │ │  FastAPI Backend │
         │     Port: 3000     │ │    Port: 8001    │
         └────────────────────┘ └────────┬─────────┘
                                         │
                               ┌─────────▼─────────┐
                               │     MongoDB       │
                               │    Port: 27017    │
                               └───────────────────┘
```

---

### Quick Start (Development)

```bash
# 1. Clone repository
git clone <repository-url>
cd bloodlink

# 2. Setup Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=bloodlink_production
JWT_SECRET=your-secure-jwt-secret-change-this
EOF

# Start backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# 3. Setup Frontend (new terminal)
cd frontend
yarn install

# Create .env file
cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
EOF

# Start frontend
yarn start
```

---

### Production Deployment

#### 1. MongoDB Setup

```bash
# Install MongoDB 6.0+
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create database and user
mongosh << EOF
use bbms_production
db.createUser({
  user: "bbms_user",
  pwd: "your-secure-password",
  roles: [{ role: "readWrite", db: "bbms_production" }]
})
EOF
```

#### 2. Backend Deployment

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cat > .env << EOF
MONGO_URL=mongodb://bbms_user:your-secure-password@localhost:27017/bbms_production
DB_NAME=bbms_production
JWT_SECRET=$(openssl rand -hex 32)
EOF

# Run with gunicorn for production
pip install gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

#### 3. Frontend Deployment

```bash
cd frontend

# Install dependencies
yarn install

# Configure environment for production
cat > .env << EOF
REACT_APP_BACKEND_URL=https://your-domain.com/api
EOF

# Build production bundle
yarn build

# The build folder contains static files to serve
```

#### 4. Nginx Configuration

```nginx
# /etc/nginx/sites-available/bbms
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    # Frontend (React)
    location / {
        root /var/www/bbms/frontend/build;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### 5. Systemd Services

**Backend Service** (`/etc/systemd/system/bbms-backend.service`):
```ini
[Unit]
Description=Blood Link Backend API
After=network.target mongod.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/bbms/backend
Environment="PATH=/var/www/bbms/backend/venv/bin"
EnvironmentFile=/var/www/bbms/backend/.env
ExecStart=/var/www/bbms/backend/venv/bin/gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8001
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable bbms-backend
sudo systemctl start bbms-backend
```

---

### Initial Setup

After deployment, run the initialization script to create the system admin:

```bash
cd backend
source venv/bin/activate
python deployment/init_database.py
```

This creates:
- System Admin account (change password immediately)
- Default password policy
- Default session configuration

---

### Environment Variables

#### Backend (.env)
| Variable | Description | Required |
|----------|-------------|----------|
| MONGO_URL | MongoDB connection string | Yes |
| DB_NAME | Database name | Yes |
| JWT_SECRET | Secret key for JWT tokens | Yes |

#### Frontend (.env)
| Variable | Description | Required |
|----------|-------------|----------|
| REACT_APP_BACKEND_URL | Backend API URL | Yes |

---

### Security Checklist

- [ ] Change default admin password
- [ ] Use strong JWT_SECRET (32+ characters)
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure MongoDB authentication
- [ ] Set up firewall rules (only expose ports 80/443)
- [ ] Enable MongoDB access only from localhost
- [ ] Regular database backups
- [ ] Monitor audit logs

---

### Backup & Recovery

#### Manual Backup
```bash
mongodump --uri="mongodb://localhost:27017/bbms_production" --out=/backup/$(date +%Y%m%d)
```

#### Restore
```bash
mongorestore --uri="mongodb://localhost:27017/bbms_production" /backup/20260112
```

---

### Support

For issues and support, contact your system administrator or refer to the documentation.

**Version:** 1.0.0
**Last Updated:** January 2026
