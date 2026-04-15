from django.urls import path
from . import views

urlpatterns = [
    # هذا الرابط سيكون: your-ip:8000/monitoring/api/data/
    path('api/data/', views.receive_data, name='receive_data'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-battery/<int:battery_id>/', views.update_battery, name='update_battery'),
    path('add-battery/', views.add_battery, name='add_battery'),
    path('delete-battery/<int:battery_id>/', views.delete_battery, name='delete_battery'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]