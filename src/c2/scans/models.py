from django.db import models
import uuid


class Session(models.Model):
    """Tracks a complete pentest session from start to finish"""
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    target_hostname = models.CharField(max_length=200)
    target_os = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[
            ('recon', 'Reconnaissance'),
            ('analysis', 'AI Analysis'),
            ('attack', 'Attack Simulation'),
            ('reporting', 'Generating Report'),
            ('complete', 'Complete'),
            ('error', 'Error')
        ],
        default='recon'
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    master_json = models.JSONField(null=True, blank=True)  # Full data for report
    report_path = models.CharField(max_length=500, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Session {self.session_id} - {self.target_hostname} ({self.status})"


class ScanResult(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='scans', null=True, blank=True)
    target = models.CharField(max_length=100)
    os = models.CharField(max_length=200, blank=True, null=True)
    results = models.JSONField()  # stores open ports, services, etc.
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Scan of {self.target} at {self.timestamp}"
