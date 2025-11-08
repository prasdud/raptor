from django.urls import path
from .views import submit_scan, get_session_status

urlpatterns = [
    path('submit_scan/', submit_scan, name='submit_scan'),
    path('session/<uuid:session_id>/', get_session_status, name='session_status'),
]
