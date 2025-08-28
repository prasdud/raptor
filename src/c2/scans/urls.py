from django.urls import path
from .views import submit_scan

urlpatterns = [
    path('submit_scan/', submit_scan),
]
