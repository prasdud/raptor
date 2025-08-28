import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import ScanResult

@csrf_exempt
def submit_scan(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        scan = ScanResult.objects.create(
            target=data.get('target'),
            os=data.get('os'),
            results=data.get('open_ports', [])
        )
        return JsonResponse({'status': 'ok', 'id': scan.id})
    return JsonResponse({'error': 'POST request required'}, status=400)
