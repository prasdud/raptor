#!/bin/bash
# RAPTOR Project - Complete Test Suite Runner
# Runs all tests for Modules 1-4 to verify complete functionality

echo "======================================================================"
echo "🧪 RAPTOR PROJECT - COMPLETE TEST SUITE"
echo "======================================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0
PASSED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_file="$2"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Running: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if python3 "$test_file" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}: $test_name"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}: $test_name"
        echo "Output:"
        cat /tmp/test_output.log | tail -n 20
        ((FAILED++))
    fi
    echo ""
}

# Change to project root
cd "$(dirname "$0")/.."

# Module 1: Session Tracking
run_test "Module 1: Session Model Tests" "tests/test_models.py"

# Module 2: Pipeline Orchestrator  
run_test "Module 2: Orchestrator Tests" "tests/test_orchestrator.py"

# Module 3: API Integration
run_test "Module 3: Integration Tests" "tests/test_integration.py"

# Module 4: Enhanced Payload
run_test "Module 4: Payload Unit Tests" "tests/test_payload.py"

# Display summary
echo "======================================================================"
echo "📊 TEST SUMMARY"
echo "======================================================================"
echo ""
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo ""
    echo "The complete RAPTOR pipeline is operational:"
    echo "  1. ✓ Session tracking system"
    echo "  2. ✓ Pipeline orchestrator"
    echo "  3. ✓ API integration"
    echo "  4. ✓ Enhanced payload driver"
    echo ""
    echo "Total test count: $PASSED tests passed"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Please review the failed tests above."
    echo ""
    exit 1
fi
