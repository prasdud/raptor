from django.urls import path
from .views import attack_decision

urlpatterns = [
    path("", attack_decision, name="attack_decision"),  # serve at the include(...) base path
]
