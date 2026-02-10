from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Device, Reading # تأكد من استيراد الموديلات الصحيحة
from django.utils import timezone # تأكد من استيراد timezone

@csrf_exempt
def receive_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            d_id = data.get('device_id')
            volt = data.get('voltage')

            # 1. البحث عن الجهاز في قاعدة البيانات
            # إذا لم يجد الجهاز سيعطي خطأ 404 أو يمكنك التعامل معه
            try:
                device = Device.objects.get(device_id=d_id)
            except Device.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Device not found'}, status=404)

            # 2. الحصول على البطارية المرتبطة بالجهاز
            battery = device.batteries.first()
            if not battery:
                return JsonResponse({'status': 'error', 'message': 'No battery linked to this device'}, status=400)

            # 3. تسجيل القراءة
            Reading.objects.create(
                battery=battery,
                avg_voltage=volt,
                avg_current=0.0,
                avg_temp=25.0,
                min_voltage=volt,
                max_temp=25.0,
                power_avg=0.0,
                energy_wh=0.0,
                samples_count=1,
                period_seconds=60,
                timestamp=timezone.now() # تأكد من عمل import timezone
            )

            return JsonResponse({'status': 'success', 'device': device.device_id}, status=201)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'invalid_method'}, status=405)