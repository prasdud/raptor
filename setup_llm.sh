#!/bin/bash
# Setup script for LLM-powered mitigations

set -e

echo "🚀 Setting up LLM Mitigations for RAPTOR"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the RAPTOR root directory"
    exit 1
fi

# Install Cohere SDK
echo "📦 Installing Cohere SDK..."
pip install cohere==5.13.5
echo "   ✓ Cohere installed"
echo ""

# Check for API key
if [ -z "$COHERE_API_KEY" ]; then
    echo "⚠️  COHERE_API_KEY not set"
    echo ""
    echo "To get an API key:"
    echo "1. Visit https://dashboard.cohere.com/"
    echo "2. Sign up or log in"
    echo "3. Navigate to API Keys section"
    echo "4. Create a new API key"
    echo ""
    read -p "Enter your Cohere API key (or press Enter to skip): " api_key
    
    if [ ! -z "$api_key" ]; then
        export COHERE_API_KEY="$api_key"
        echo ""
        echo "✓ API key set for this session"
        echo ""
        echo "To persist the key, add this to your ~/.bashrc:"
        echo "export COHERE_API_KEY=\"$api_key\""
        echo ""
    else
        echo ""
        echo "⚠️  Skipping API key setup. You can set it later:"
        echo "export COHERE_API_KEY=\"your-key-here\""
        echo ""
    fi
else
    echo "✓ COHERE_API_KEY already set"
    echo ""
fi

# Test the installation
echo "🧪 Testing LLM service..."
cd src/c2

python3 << 'EOF'
import sys
try:
    from scans.llm_service import LLMMitigationService
    print("   ✓ LLM service imported successfully")
    
    # Try to initialize (will fail gracefully if no API key)
    try:
        llm = LLMMitigationService()
        print("   ✓ LLM service initialized with API key")
        
        # Quick test
        test_data = {
            "target_name": "test-server",
            "exec_summary": {"overall_risk": "Medium"},
            "recon_data": {"os_name": "Ubuntu", "is_admin": False, "open_ports": [22, 80]},
            "findings": [{"name": "SSH Open", "severity": "Low", "evidence": "Port 22"}],
        }
        
        print("   🔄 Testing mitigation generation...")
        mitigations = llm.generate_mitigations(test_data, max_tokens=500)
        print(f"   ✓ Generated {len(mitigations)} test mitigations")
        
    except ValueError as e:
        print(f"   ⚠️  API key not configured: {e}")
        print("   ℹ️  Service will use fallback mitigations")
        
except Exception as e:
    print(f"   ❌ Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF

test_result=$?

cd ../..

if [ $test_result -eq 0 ]; then
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Run a test scan: python3 tests/test_payload.py"
    echo "2. Check for LLM mitigations in the generated report"
    echo "3. Read docs/LLM_MITIGATIONS.md for more details"
    echo ""
else
    echo ""
    echo "⚠️  Setup completed with warnings"
    echo "Check the error messages above and refer to docs/LLM_MITIGATIONS.md"
    echo ""
fi
