from django.urls import path
from . import views

urlpatterns = [
    # هذا الرابط سيكون: your-ip:8000/monitoring/api/data/
    path('api/data/', views.receive_data, name='receive_data'),
    path('dashboard/', views.dashboard, name='dashboard'),
]