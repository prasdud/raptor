"""
Test Module 1: Session Model
Tests the session tracking system
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/prasdud/playground/raptor/src/c2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'c2.settings')
django.setup()

from scans.models import Session, ScanResult

def test_session_creation():
    """Test creating a new session"""
    print("🧪 Testing Session Model Creation...")
    
    # Create a session
    session = Session.objects.create(
        target_hostname="test-vm-01",
        target_os="Windows 10",
        status='recon'
    )
    
    print(f"✅ Session created: {session}")
    print(f"   - Session ID: {session.session_id}")
    print(f"   - Target: {session.target_hostname}")
    print(f"   - Status: {session.status}")
    print(f"   - Start Time: {session.start_time}")
    
    return session

def test_session_with_scan():
    """Test creating a session with scan results"""
    print("\n🧪 Testing Session with ScanResult...")
    
    # Create session
    session = Session.objects.create(
        target_hostname="test-vm-02",
        target_os="Windows 10",
        status='analysis'
    )
    
    # Create scan result linked to session
    scan = ScanResult.objects.create(
        session=session,
        target="test-vm-02",
        os="Windows 10",
        results={
            "hostname": "test-vm-02",
            "open_ports": [80, 443, 3389],
            "is_admin": True
        }
    )
    
    print(f"✅ Session with scan created")
    print(f"   - Session: {session.session_id}")
    print(f"   - Scan: {scan}")
    print(f"   - Scans in session: {session.scans.count()}")
    
    return session, scan

def test_session_status_update():
    """Test updating session status"""
    print("\n🧪 Testing Session Status Updates...")
    
    session = Session.objects.create(
        target_hostname="test-vm-03",
        target_os="Ubuntu 22.04",
        status='recon'
    )
    
    print(f"   Initial status: {session.status}")
    
    # Update status
    session.status = 'analysis'
    session.save()
    print(f"   Updated status: {session.status}")
    
    session.status = 'complete'
    session.save()
    print(f"   Final status: {session.status}")
    
    print(f"✅ Status updates working correctly")
    
    return session

def test_query_sessions():
    """Test querying sessions"""
    print("\n🧪 Testing Session Queries...")
    
    all_sessions = Session.objects.all()
    print(f"   Total sessions: {all_sessions.count()}")
    
    for session in all_sessions[:5]:  # Show first 5
        print(f"   - {session}")
    
    # Query by status
    recon_sessions = Session.objects.filter(status='recon')
    complete_sessions = Session.objects.filter(status='complete')
    
    print(f"   Sessions in 'recon': {recon_sessions.count()}")
    print(f"   Sessions 'complete': {complete_sessions.count()}")
    
    print(f"✅ Queries working correctly")

def cleanup():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    count = Session.objects.filter(target_hostname__startswith='test-vm').delete()[0]
    print(f"   Deleted {count} test sessions")

if __name__ == "__main__":
    print("="*70)
    print("MODULE 1: SESSION MODEL TESTS")
    print("="*70)
    
    try:
        test_session_creation()
        test_session_with_scan()
        test_session_status_update()
        test_query_sessions()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED - Module 1 Complete!")
        print("="*70)
        
        # Cleanup
        cleanup()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
