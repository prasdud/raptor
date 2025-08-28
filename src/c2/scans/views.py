import json

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from scans.models import ScanResult

@csrf_exempt
def submit_scan(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # parse JSON payload

            # Extract fields matching your payload
            target_ip = data.get("recon_data", {}).get("hostname") or "unknown"
            os_name = data.get("recon_data", {}).get("os_name") or "unknown"
            recon_data = data.get("recon_data") or {}

            # Save to DB
            ScanResult.objects.create(
                target=target_ip,
                os=os_name,
                results=recon_data
            )

            return JsonResponse({"status": "success"})
        except Exception as e:
            print("Error saving scan result:", e)
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "POST request required"}, status=400)
