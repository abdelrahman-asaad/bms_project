from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
import json

# استيراد الموديلز الخاصة بك
from .models import Device, Reading, Battery, PulseTest

User = get_user_model()

def calculate_soc(v):
    """حساب نسبة الشحن بناءً على الجهد"""
    if v >= 4.2: return 100.0
    if v <= 3.4: return 0.0
    return round((v - 3.4) / (4.2 - 3.4) * 100, 1)

@csrf_exempt
def receive_data(request):
    """استقبال البيانات من ESP32 ومعالجتها"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email_from_esp = data.get('email')
            v_before = float(data.get('v_before', 0))
            v_after = float(data.get('v_after', 0))
            curr_raw = float(data.get('current', 0))
            temp = float(data.get('temp', 0))

            with transaction.atomic():
                # 1. البحث عن المستخدم أو السوبر يوزر
                user = User.objects.filter(email=email_from_esp).first()
                if not user:
                    user = User.objects.filter(is_superuser=True).first()
                
                if not user:
                    return JsonResponse({'status': 'error', 'message': 'No user found'}, status=400)

                # 2. التأكد من وجود بطارية (أو إنشاؤها تلقائياً)
                battery = Battery.objects.filter(device__user=user).first()
                if not battery:
                    device, _ = Device.objects.get_or_create(user=user, defaults={'name': 'Auto-Created Device'})
                    battery, _ = Battery.objects.get_or_create(device=device, defaults={'name': 'Main Battery'})

                # 3. الحسابات
                curr_ma = abs(curr_raw)
                i_amps = curr_ma / 1000.0
                delta_v = v_before - v_after
                resistance = delta_v / i_amps if i_amps > 0.01 else 0
                soh = max(0, min(100, (1 - (resistance - 0.05) / 1.15) * 100))
                soc = calculate_soc(v_before)
                power_w = v_after * i_amps

                # 4. حفظ البيانات في PulseTest
                PulseTest.objects.create(
                    battery=battery,
                    v_before=v_before,
                    v_after=v_after,
                    current_ma=curr_ma, 
                    temperature_c=temp,
                    internal_resistance=resistance,
                    calculated_soh=soh,
                    calculated_soc=soc
                )

                # 5. حفظ البيانات في Reading للجدول
                Reading.objects.create(
                    battery=battery,
                    avg_voltage=v_before,
                    min_voltage=v_after,
                    avg_current=curr_ma,
                    avg_temp=temp,
                    power_avg=power_w,
                    timestamp=timezone.now()
                )

                # 6. تحديث البطارية
                battery.soh = round(soh, 1)
                battery.save()

                return JsonResponse({'status': 'success'}, status=201)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'invalid_method'}, status=405)

def dashboard(request):
    """عرض صفحة لوحة التحكم"""
    readings = Reading.objects.select_related('battery').all().order_by('-timestamp')[:20]
    last_reading = readings[0] if readings else None
    last_pulse = None
    last_soc = 0

    if last_reading:
        last_pulse = PulseTest.objects.filter(battery=last_reading.battery).order_by('-timestamp').first()
        if last_pulse:
            last_soc = last_pulse.calculated_soc

    context = {
        'readings': readings,
        'last_reading': last_reading,
        'last_pulse': last_pulse,
        'last_soc': last_soc,
    }
    return render(request, 'monitoring/dashboard.html', context)