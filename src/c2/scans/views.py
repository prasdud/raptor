import json
import threading

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from scans.models import ScanResult, Session
from scans.orchestrator import PipelineOrchestrator


@csrf_exempt
def submit_scan(request):
    """
    Endpoint to receive reconnaissance data from payload.
    Creates a session, stores the data, and triggers the pipeline orchestrator.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # parse JSON payload

            # Extract fields matching your payload
            target_ip = data.get("recon_data", {}).get("hostname") or "unknown"
            os_name = data.get("recon_data", {}).get("os_name") or "unknown"
            recon_data = data.get("recon_data") or {}
            
            print(f"📨 Received scan data from {target_ip} ({os_name})")

            # Create a new session for this pentest run
            session = Session.objects.create(
                target_hostname=target_ip,
                target_os=os_name,
                status='recon'
            )
            print(f"   ✓ Created session: {session.session_id}")

            # Save scan result linked to session
            scan = ScanResult.objects.create(
                session=session,
                target=target_ip,
                os=os_name,
                results=recon_data
            )
            print(f"   ✓ Stored recon data (scan ID: {scan.id})")

            # Run orchestrator pipeline
            # Option 1: Run synchronously (blocks until complete)
            # Option 2: Run in background thread (non-blocking)
            # We'll use Option 2 for better UX
            
            print(f"   🚀 Triggering pipeline orchestrator...")
            
            def run_pipeline():
                """Background task to run the pipeline"""
                try:
                    orchestrator = PipelineOrchestrator(session)
                    report_path = orchestrator.run()
                    print(f"   ✅ Pipeline complete! Report: {report_path}")
                except Exception as e:
                    print(f"   ❌ Pipeline failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Start pipeline in background thread
            pipeline_thread = threading.Thread(target=run_pipeline, daemon=True)
            pipeline_thread.start()

            return JsonResponse({
                "status": "success",
                "message": "Scan received and pipeline started",
                "session_id": str(session.session_id),
                "note": "Pipeline is running in background. Check session status for progress."
            })
            
        except Exception as e:
            print(f"❌ Error in submit_scan: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "status": "error", 
                "message": str(e)
            }, status=500)
    else:
        return JsonResponse({
            "status": "error", 
            "message": "POST request required"
        }, status=400)


@csrf_exempt
def get_session_status(request, session_id):
    """
    Endpoint to check the status of a pentest session.
    
    Usage: GET /api/session/<session_id>/
    """
    try:
        session = Session.objects.get(session_id=session_id)
        
        response_data = {
            "session_id": str(session.session_id),
            "target": session.target_hostname,
            "os": session.target_os,
            "status": session.status,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "report_path": session.report_path,
            "error_message": session.error_message
        }
        
        # If complete, include summary from master_json
        if session.status == 'complete' and session.master_json:
            response_data['summary'] = {
                "risk_level": session.master_json.get('exec_summary', {}).get('overall_risk'),
                "findings_count": len(session.master_json.get('findings', [])),
                "sensitive_files": session.master_json.get('exec_summary', {}).get('sensitive_data_list', [])
            }
        
        return JsonResponse(response_data)
        
    except Session.DoesNotExist:
        return JsonResponse({
            "error": "Session not found"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)
