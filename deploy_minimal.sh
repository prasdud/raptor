#!/bin/bash

##############################################################################
# RAPTOR - Minimal VPS Deployment
# Run this after: git clone && cd raptor
##############################################################################

set -e

echo "🚀 RAPTOR Minimal Deployment Starting..."
echo ""

# Get VPS IP/domain
read -p "Enter your VPS IP or domain: " VPS_ADDRESS

echo ""
echo "Installing dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx texlive-latex-base texlive-latex-extra

echo ""
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

echo ""
echo "Configuring Django..."
cd src/c2

# Update ALLOWED_HOSTS and STATIC_ROOT
python3 << EOF
import re
import os

with open('c2/settings.py', 'r') as f:
    content = f.read()

# Ensure 'import os' is at the top if not present
if 'import os' not in content:
    # Add after 'from pathlib import Path'
    content = re.sub(
        r"(from pathlib import Path)",
        r"\1\nimport os",
        content
    )

# Update ALLOWED_HOSTS
content = re.sub(
    r"ALLOWED_HOSTS = \[.*?\]",
    "ALLOWED_HOSTS = ['$VPS_ADDRESS', 'localhost', '127.0.0.1']",
    content,
    flags=re.DOTALL
)

# Add STATIC_ROOT if not present
if 'STATIC_ROOT' not in content:
    static_root_line = "\nSTATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')\n"
    # Add after STATIC_URL
    content = re.sub(
        r"(STATIC_URL = ['\"].*?['\"])",
        r"\1" + static_root_line,
        content
    )

with open('c2/settings.py', 'w') as f:
    f.write(content)
print("✓ Updated ALLOWED_HOSTS and STATIC_ROOT")
EOF

# Run migrations
python manage.py migrate
python manage.py collectstatic --noinput

echo ""
echo "Creating superuser..."
python manage.py createsuperuser

cd ../..

echo ""
echo "Setting up Gunicorn service..."
sudo tee /etc/systemd/system/raptor.service > /dev/null << EOF
[Unit]
Description=RAPTOR C2 Server
After=network.target

[Service]
Type=notify
User=$USER
Group=$USER
WorkingDirectory=$(pwd)/src/c2
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 3 c2.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Setting up Nginx..."
sudo tee /etc/nginx/sites-available/raptor > /dev/null << EOF
server {
    listen 80;
    server_name $VPS_ADDRESS;
    client_max_body_size 50M;

    location /static/ {
        alias $(pwd)/src/c2/staticfiles/;
    }

    location /media/ {
        alias $(pwd)/src/c2/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/raptor /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo ""
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable raptor
sudo systemctl start raptor
sudo systemctl restart nginx

echo ""
echo "Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw --force enable

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ RAPTOR is now running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 C2 URL: http://$VPS_ADDRESS"
echo "🔑 Admin: http://$VPS_ADDRESS/admin/"
echo "📡 API: http://$VPS_ADDRESS/api/submit_scan/"
echo ""
echo "Commands:"
echo "  Status:  sudo systemctl status raptor"
echo "  Logs:    sudo journalctl -u raptor -f"
echo "  Restart: sudo systemctl restart raptor"
echo ""
echo "Update payload_cloud.py with:"
echo "  C2_SERVER = \"http://$VPS_ADDRESS\""
echo ""
