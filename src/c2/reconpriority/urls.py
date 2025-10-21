from django.urls import path
from .views import predict_file_sensitivity

urlpatterns = [
    path('predict/', predict_file_sensitivity, name='predict_file_sensitivity'),
]
