from django.db import models

class ScanResult(models.Model):
    target = models.CharField(max_length=100)
    os = models.CharField(max_length=200, blank=True, null=True)
    results = models.JSONField()  # stores open ports, services, etc.
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan of {self.target} at {self.timestamp}"
