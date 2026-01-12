#!/bin/bash
# BBMS Installation Script
# Run with: sudo bash install.sh

set -e

echo "================================================"
echo "BBMS - Blood Bank Management System Installer"
echo "================================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo bash install.sh)"
    exit 1
fi

# Configuration
INSTALL_DIR="/var/www/bbms"
BACKEND_PORT=8001
FRONTEND_PORT=3000
DOMAIN=""
MONGO_USER="bbms_user"
MONGO_PASS=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 32)

echo ""
echo "Installation Configuration:"
echo "  Install Directory: $INSTALL_DIR"
echo "  Backend Port: $BACKEND_PORT"
echo "  MongoDB User: $MONGO_USER"
echo ""

read -p "Enter your domain name (e.g., bbms.example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    DOMAIN="localhost"
fi

echo ""
echo "Starting installation..."
echo ""

# 1. Update system
echo "1. Updating system packages..."
apt-get update -y
apt-get upgrade -y

# 2. Install dependencies
echo "2. Installing dependencies..."
apt-get install -y curl wget git nginx python3 python3-pip python3-venv

# 3. Install Node.js 18.x
echo "3. Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Install yarn
npm install -g yarn

# 4. Install MongoDB 6.0
echo "4. Installing MongoDB..."
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
apt-get update
apt-get install -y mongodb-org

# Start MongoDB
systemctl start mongod
systemctl enable mongod

# Wait for MongoDB to start
sleep 5

# Create MongoDB user
mongosh << EOF
use bbms_production
db.createUser({
  user: "$MONGO_USER",
  pwd: "$MONGO_PASS",
  roles: [{ role: "readWrite", db: "bbms_production" }]
})
EOF

echo "MongoDB user created."

# 5. Create installation directory
echo "5. Setting up application directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Copy application files (assuming they're in current directory)
echo "Please copy your application files to $INSTALL_DIR"
echo "Expected structure:"
echo "  $INSTALL_DIR/backend/"
echo "  $INSTALL_DIR/frontend/"
echo "  $INSTALL_DIR/deployment/"

# 6. Setup Backend
echo "6. Setting up backend..."
cd $INSTALL_DIR/backend

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create backend .env
cat > .env << EOF
MONGO_URL=mongodb://$MONGO_USER:$MONGO_PASS@localhost:27017/bbms_production
DB_NAME=bbms_production
JWT_SECRET=$JWT_SECRET
EOF

# Initialize database
python deployment/init_database.py --init

deactivate

# 7. Setup Frontend
echo "7. Setting up frontend..."
cd $INSTALL_DIR/frontend

# Create frontend .env
cat > .env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN/api
EOF

yarn install
yarn build

# 8. Create systemd service for backend
echo "8. Creating systemd services..."

cat > /etc/systemd/system/bbms-backend.service << EOF
[Unit]
Description=BBMS Backend API
After=network.target mongod.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/venv/bin"
EnvironmentFile=$INSTALL_DIR/backend/.env
ExecStart=$INSTALL_DIR/backend/venv/bin/gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:$BACKEND_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bbms-backend
systemctl start bbms-backend

# 9. Configure Nginx
echo "9. Configuring Nginx..."

cat > /etc/nginx/sites-available/bbms << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Frontend (React build)
    location / {
        root $INSTALL_DIR/frontend/build;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        
        # File upload limit
        client_max_body_size 50M;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/bbms /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
nginx -t
systemctl reload nginx

# 10. Set permissions
echo "10. Setting permissions..."
chown -R www-data:www-data $INSTALL_DIR
chmod -R 755 $INSTALL_DIR

# 11. Summary
echo ""
echo "================================================"
echo "INSTALLATION COMPLETE"
echo "================================================"
echo ""
echo "Application URL: http://$DOMAIN"
echo ""
echo "System Admin Credentials:"
echo "  Email:    admin@bbms.local"
echo "  Password: Admin@123456"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "  1. Change the admin password immediately"
echo "  2. Setup SSL/HTTPS (recommended: certbot)"
echo "  3. Configure firewall"
echo "  4. Setup regular backups"
echo ""
echo "MongoDB Credentials (save these):"
echo "  User: $MONGO_USER"
echo "  Pass: $MONGO_PASS"
echo ""
echo "JWT Secret: $JWT_SECRET"
echo ""
echo "Service Commands:"
echo "  sudo systemctl status bbms-backend"
echo "  sudo systemctl restart bbms-backend"
echo "  sudo journalctl -u bbms-backend -f"
echo ""
echo "================================================"
