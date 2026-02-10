from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Device, Reading, Battery
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

@csrf_exempt
def receive_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            d_id = data.get('device_id')
            volt = data.get('voltage')

            if not d_id or volt is None:
                return JsonResponse({'error': 'Missing device_id or voltage'}, status=400)

            user = User.objects.first()
            if not user:
                return JsonResponse({'error': 'No user in DB'}, status=400)

            device, created = Device.objects.get_or_create(
                device_id=d_id,
                defaults={'user': user}
            )

            battery = device.batteries.first()
            if not battery:
                battery = Battery.objects.create(
                    device=device,
                    battery_id=f"BATT_{d_id}",
                    capacity_mah=5000.0
                )

            Reading.objects.create(
                battery=battery,
                avg_voltage=float(volt),
                avg_current=0.0,
                avg_temp=25.0,
                min_voltage=float(volt),
                max_temp=25.0,
                power_avg=0.0,
                energy_wh=0.0,
                samples_count=1,
                period_seconds=60,
                timestamp=timezone.now()
            )

            print(f"SUCCESS: Data saved for Device: {d_id}")
            return JsonResponse({'status': 'success'}, status=201)

        except Exception as e:
            # هنا حذفنا الإيموجي لتجنب UnicodeEncodeError
            print(f"ERROR: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'invalid_method'}, status=405)

from django.shortcuts import render
from .models import Reading

def dashboard(request):
    readings = Reading.objects.all().order_by('-timestamp')[:20]
    last_reading = readings[0] if readings else None
    
    context = {
        'readings': readings,
        'last_reading': last_reading,
    }
    return render(request, 'monitoring/dashboard.html', context)