# Payload Documentation - RAPTOR

## Overview
`payload_cloud.py` is a reconnaissance agent that gathers system information and sends it to a remote C2 server for AI-driven analysis and attack planning.

---

## Configuration

**C2 Server Setup:**
```python
C2_SERVER = "http://127.0.0.1:8000"  # Change before building EXE
```

**Key Settings:**
- `MAX_FILES`: 1000 - Maximum files to enumerate
- `MAX_DEPTH`: 5 - Directory traversal depth
- `TIMEOUT_SECONDS`: 30 - C2 communication timeout
- `SAVE_LOCAL_COPY`: True - Backup data locally

---

## Data Collection

### 1. **System Information**
- Hostname, OS, Architecture, CPU, RAM, Disk
- Current user, admin privileges, boot time
- Environment variables

**Windows Collection Method:**
- `socket.gethostname()` - Hostname
- `platform.system()`, `platform.version()` - OS details
- `psutil.cpu_count()`, `psutil.virtual_memory()` - Hardware
- `os.environ` - Environment variables

### 2. **File Enumeration**
- Target Directories:
  - **Windows:** Documents, Desktop, Downloads, AppData, ProgramData
  - **Linux:** Documents, Desktop, Downloads, .config, /etc, /var/log
  - **macOS:** Documents, Desktop, Downloads, Library
- File metadata: name, path, size, timestamps, extension

**Windows Collection Method:**
- `os.walk()` - Recursive directory traversal
- `Path.stat()` - File metadata (size, timestamps)
- Depth-limited to MAX_DEPTH (default: 5)

### 3. **Network**
- Network interfaces, IP addresses, subnets
- Listening ports with process info
- Active network connections
- Firewall status

**Windows Collection Method:**
- `psutil.net_if_addrs()` - Network interfaces and IPs
- `psutil.net_connections(kind='inet')` - All connections
- Filter `status == 'LISTEN'` for listening ports
- `netsh advfirewall show allprofiles` - Firewall status

### 4. **Security**
- User accounts (regular + privileged)
- Active user sessions
- Antivirus detection (Windows Defender, Norton, McAfee, etc.)
- Firewall detection (Windows Defender, ufw, iptables, pfctl)

**Windows Collection Method:**
- `net user` - List all local users
- `net localgroup Administrators` - Admin group members
- `psutil.users()` - Active sessions
- `Get-MpComputerStatus` (PowerShell) - Windows Defender status
- Check common AV processes: avgnt.exe, mcshield.exe, nortonsecurity.exe

### 5. **Processes & Software**
- Running processes with PID, owner, CPU/memory usage
- Installed software (Windows registry, apt, rpm, pacman, .app)
- Connected devices (webcams, printers, network storage)

**Windows Collection Method:**
- `psutil.process_iter()` - All running processes with details
- `winreg` module - Read Windows Registry for installed software
  - `HKEY_LOCAL_MACHINE\SOFTWARE\...\Uninstall`
  - Extracts DisplayName and DisplayVersion
- `Get-PnpDevice -Class Camera` (PowerShell) - Webcams
- `Get-Printer` (PowerShell) - Printers
- `net use` - Network shares/storage

---

## Data Transmission

**Endpoint:** `{C2_SERVER}/api/submit_scan/`  
**Method:** HTTP POST (JSON)  
**Fallback:** Local storage in `~/.cache/syslog/` if C2 unreachable

**Payload Structure:**
```json
{
  "recon_data": {
    "hostname": "...",
    "os_name": "...",
    "files": [...],
    "open_ports": [...],
    "network_info": {...},
    "firewall": {...},
    "user_accounts": {...},
    "processes": [...],
    "installed_software": [...],
    "antivirus": [...],
    "connected_devices": [...]
  }
}
```

---

## Execution Flow

1. **System Info** → Gather OS/hardware details
2. **File Enumeration** → Scan target directories
3. **Network** → Ports, connections, interfaces, firewall
4. **Users** → Accounts, privileges, active sessions
5. **Processes** → Running processes with details
6. **Software** → Installed applications
7. **Antivirus** → Detect security products
8. **Connected Devices** → Webcams, printers, network storage
9. **Send to C2** → Transmit all data for AI analysis
10. **Poll Status** → Monitor server-side processing
11. **Display Results** → Show risk level and report path

---

## Building Windows EXE

### Silent Mode (No Console):
```cmd
pyinstaller --onefile --noconsole --name raptor_payload payload_cloud.py
```

### Debug Mode (With Console):
```cmd
pyinstaller --onefile --name raptor_payload_debug payload_cloud.py
```

**Output:** `dist/raptor_payload.exe` (~10-15 MB)

---

## Dependencies

**Required:**
- `psutil` - System utilities
- `requests` - HTTP client

**Install:**
```bash
pip install psutil requests
```

---

## OPSEC Features

✅ Hidden local storage (`~/.cache/syslog/`)  
✅ Silent mode option (no console output)  
✅ Graceful error handling (no crashes)  
✅ Read-only operations (non-destructive)  
✅ Timeout controls (avoids hanging)  
✅ Permission-aware (skips access denied)

---

**For deployment:** See `BUILD_PAYLOAD_EXE.md` and `HARDCODED_C2_SETUP.md`

