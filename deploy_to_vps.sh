#!/bin/bash

##############################################################################
# RAPTOR C2 VPS Deployment Script
# 
# This script automates the deployment of RAPTOR C2 Server to a cloud VPS
# Run this ON YOUR VPS after SSH login
#
# Usage: 
#   wget https://raw.githubusercontent.com/yourusername/raptor/main/deploy_to_vps.sh
#   chmod +x deploy_to_vps.sh
#   sudo ./deploy_to_vps.sh
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
╦═╗╔═╗╔═╗╔╦╗╔═╗╦═╗  ╔═╗┌─┐  ╔╦╗┌─┐┌─┐┬  ┌─┐┬ ┬┌─┐┬─┐
╠╦╝╠═╣╠═╝ ║ ║ ║╠╦╝  ║  ┌─┘   ║║├┤ ├─┘│  │ │└┬┘├┤ ├┬┘
╩╚═╩ ╩╩   ╩ ╚═╝╩╚═  ╚═╝└─┘  ═╩╝└─┘┴  ┴─┘└─┘ ┴ └─┘┴└─
            VPS Deployment Automation Script
EOF
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Please run as root (use sudo)"
    exit 1
fi

# Collect configuration
log_info "Starting RAPTOR deployment configuration..."
echo ""

read -p "Enter your domain name (or VPS IP): " DOMAIN_NAME
read -p "Enter your GitHub username: " GITHUB_USER
read -p "Enter your GitHub repository name [default: raptor]: " REPO_NAME
REPO_NAME=${REPO_NAME:-raptor}
read -p "Enter application user [default: raptor]: " APP_USER
APP_USER=${APP_USER:-raptor}
read -p "Install SSL certificate? (requires domain, not IP) [y/N]: " INSTALL_SSL

echo ""
log_info "Configuration Summary:"
echo "  Domain/IP: $DOMAIN_NAME"
echo "  GitHub: $GITHUB_USER/$REPO_NAME"
echo "  App User: $APP_USER"
echo "  SSL: ${INSTALL_SSL:-N}"
echo ""
read -p "Proceed with deployment? [Y/n]: " PROCEED
PROCEED=${PROCEED:-Y}

if [[ ! $PROCEED =~ ^[Yy]$ ]]; then
    log_warning "Deployment cancelled"
    exit 0
fi

# Step 1: Update system
log_info "Updating system packages..."
apt update && apt upgrade -y
log_success "System updated"

# Step 2: Install dependencies
log_info "Installing dependencies..."
apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    curl \
    ufw \
    fail2ban
log_success "Dependencies installed"

# Step 3: Create application user
if id "$APP_USER" &>/dev/null; then
    log_warning "User $APP_USER already exists, skipping creation"
else
    log_info "Creating application user: $APP_USER"
    adduser $APP_USER --disabled-password --gecos ""
    log_success "User created"
fi

# Step 4: Clone repository
log_info "Cloning RAPTOR repository..."
APP_DIR="/home/$APP_USER/$REPO_NAME"

if [ -d "$APP_DIR" ]; then
    log_warning "Directory $APP_DIR already exists"
    read -p "Remove and re-clone? [y/N]: " RECLONE
    if [[ $RECLONE =~ ^[Yy]$ ]]; then
        rm -rf "$APP_DIR"
    else
        log_info "Using existing directory"
    fi
fi

if [ ! -d "$APP_DIR" ]; then
    sudo -u $APP_USER git clone "https://github.com/$GITHUB_USER/$REPO_NAME.git" "$APP_DIR"
    log_success "Repository cloned"
fi

# Step 5: Setup virtual environment
log_info "Setting up Python virtual environment..."
cd "$APP_DIR"
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER venv/bin/pip install --upgrade pip
sudo -u $APP_USER venv/bin/pip install -r requirements.txt
sudo -u $APP_USER venv/bin/pip install gunicorn
log_success "Virtual environment ready"

# Step 6: Generate Django secret key
log_info "Generating Django secret key..."
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
log_success "Secret key generated"

# Step 7: Create production settings
log_info "Creating production settings..."
SETTINGS_FILE="$APP_DIR/src/c2/c2/settings_production.py"

cat > "$SETTINGS_FILE" << EOF
from .settings import *
import os

# SECURITY SETTINGS
DEBUG = False
ALLOWED_HOSTS = [
    '$DOMAIN_NAME',
    'localhost',
    '127.0.0.1',
]

SECRET_KEY = '$SECRET_KEY'

# Static files
STATIC_ROOT = '$APP_DIR/src/c2/staticfiles/'
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = '$APP_DIR/src/c2/media/'
MEDIA_URL = '/media/'

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '$APP_DIR/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
EOF

chown $APP_USER:$APP_USER "$SETTINGS_FILE"
log_success "Production settings created"

# Step 8: Prepare Django
log_info "Running Django migrations..."
mkdir -p "$APP_DIR/logs"
chown -R $APP_USER:$APP_USER "$APP_DIR/logs"

cd "$APP_DIR/src/c2"
sudo -u $APP_USER bash -c "
    source $APP_DIR/venv/bin/activate
    export DJANGO_SETTINGS_MODULE=c2.settings_production
    python manage.py migrate
    python manage.py collectstatic --noinput
"
log_success "Django prepared"

# Step 9: Create Gunicorn config
log_info "Creating Gunicorn configuration..."
cat > "$APP_DIR/gunicorn_config.py" << 'EOF'
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5

accesslog = "$APP_DIR/logs/gunicorn_access.log"
errorlog = "$APP_DIR/logs/gunicorn_error.log"
loglevel = "info"

proc_name = "raptor_c2"
daemon = False
EOF

sed -i "s|\$APP_DIR|$APP_DIR|g" "$APP_DIR/gunicorn_config.py"
chown $APP_USER:$APP_USER "$APP_DIR/gunicorn_config.py"
log_success "Gunicorn configured"

# Step 10: Create systemd service
log_info "Creating systemd service..."
cat > /etc/systemd/system/raptor.service << EOF
[Unit]
Description=RAPTOR C2 Server (Gunicorn)
After=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/src/c2
Environment="PATH=$APP_DIR/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=c2.settings_production"
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --config $APP_DIR/gunicorn_config.py \\
    c2.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable raptor
log_success "Systemd service created"

# Step 11: Configure Nginx
log_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/raptor << EOF
upstream raptor_server {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name $DOMAIN_NAME;

    client_max_body_size 50M;

    access_log /var/log/nginx/raptor_access.log;
    error_log /var/log/nginx/raptor_error.log;

    location /static/ {
        alias $APP_DIR/src/c2/staticfiles/;
    }

    location /media/ {
        alias $APP_DIR/src/c2/media/;
    }

    location / {
        proxy_pass http://raptor_server;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/raptor /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx
log_success "Nginx configured"

# Step 12: Configure firewall
log_info "Configuring firewall..."
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
log_success "Firewall configured"

# Step 13: Start RAPTOR
log_info "Starting RAPTOR C2 server..."
systemctl start raptor
sleep 3

if systemctl is-active --quiet raptor; then
    log_success "RAPTOR C2 server started successfully"
else
    log_error "Failed to start RAPTOR C2 server"
    journalctl -u raptor -n 20
    exit 1
fi

# Step 14: Install SSL (optional)
if [[ $INSTALL_SSL =~ ^[Yy]$ ]]; then
    log_info "Installing SSL certificate..."
    certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --register-unsafely-without-email
    
    # Enable HTTPS in Django settings
    cat >> "$SETTINGS_FILE" << EOF

# HTTPS Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
EOF
    
    systemctl restart raptor
    log_success "SSL certificate installed"
fi

# Step 15: Create admin user
log_info "Creating Django superuser..."
echo ""
log_warning "Please create an admin user for the Django admin panel:"
cd "$APP_DIR/src/c2"
sudo -u $APP_USER bash -c "
    source $APP_DIR/venv/bin/activate
    export DJANGO_SETTINGS_MODULE=c2.settings_production
    python manage.py createsuperuser
"

# Final summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                        ║${NC}"
echo -e "${GREEN}║   🎉  RAPTOR C2 DEPLOYMENT SUCCESSFUL!  🎉            ║${NC}"
echo -e "${GREEN}║                                                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
log_info "Deployment Summary:"
echo "  ✅ C2 Server URL: http${INSTALL_SSL:+s}://$DOMAIN_NAME"
echo "  ✅ Admin Panel: http${INSTALL_SSL:+s}://$DOMAIN_NAME/admin/"
echo "  ✅ API Endpoint: http${INSTALL_SSL:+s}://$DOMAIN_NAME/api/submit_scan/"
echo "  ✅ Status Endpoint: http${INSTALL_SSL:+s}://$DOMAIN_NAME/api/session/<session_id>/"
echo ""
log_info "Next Steps:"
echo "  1. Test the API endpoint:"
echo "     curl -X POST http${INSTALL_SSL:+s}://$DOMAIN_NAME/api/submit_scan/ \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"recon_data\":{\"hostname\":\"test\"}}'"
echo ""
echo "  2. Update payload_v2.py with your C2 URL:"
echo "     c2_url = \"http${INSTALL_SSL:+s}://$DOMAIN_NAME/api/submit_scan/\""
echo ""
echo "  3. Monitor logs:"
echo "     sudo journalctl -u raptor -f"
echo ""
echo "  4. Manage service:"
echo "     sudo systemctl status raptor"
echo "     sudo systemctl restart raptor"
echo ""
log_success "Deployment complete! 🚀"
