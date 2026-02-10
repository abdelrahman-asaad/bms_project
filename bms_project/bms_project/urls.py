from django.contrib import admin
from django.urls import path, include # تأكد من استيراد include

urlpatterns = [
    path('admin/', admin.site.urls),
    # ربط روابط تطبيق monitoring بالمشروع
    path('monitoring/', include('monitoring.urls')), 
    
]