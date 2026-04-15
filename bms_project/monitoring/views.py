import json
import os
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.urls import reverse # إضافة دي عشان الـ Redirect بـ parameters

from .models import Device, Reading, Battery, PulseTest, User, ActiveSession
from .forms import SignUpForm

# --- وظائف المساعدة ---

def load_battery_specs(chemistry):
    default_specs = {"v_max": 4.2, "v_min": 3.0, "r_new_base": 0.05, "r_dead": 0.50}
    try:
        path = os.path.join(settings.BASE_DIR, 'battery_specs.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                specs = json.load(f)
            return specs.get(chemistry.lower(), default_specs)
    except Exception:
        pass
    return default_specs

def calculate_dynamic_soh(resistance, capacity_mah, specs):
    adjusted_r_new = specs['r_new_base'] * (2500 / float(capacity_mah))
    r_range = specs['r_dead'] - adjusted_r_new
    if r_range <= 0: return 0
    soh = ((specs['r_dead'] - resistance) / r_range) * 100
    return max(0, min(100, round(soh, 1)))

def calculate_dynamic_soc(voltage, specs):
    v_range = specs['v_max'] - specs['v_min']
    if v_range <= 0: return 0
    soc = ((voltage - specs['v_min']) / v_range) * 100
    return max(0, min(100, int(soc)))

# --- API استلام البيانات ---

@csrf_exempt
def receive_data(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'invalid_method'}, status=405)
    
    try:
        data = json.loads(request.body)
        token_sent = data.get('api_token')
        user = User.objects.filter(api_token=token_sent).first()
        if not user:
            return JsonResponse({'status': 'error', 'message': 'Invalid Token.'}, status=403)

        session_active = ActiveSession.objects.filter(user=user).select_related('selected_battery').first()
        
        if not session_active or not session_active.selected_battery:
            battery = Battery.objects.filter(device__user=user).first()
            if not battery:
                return JsonResponse({'status': 'error', 'message': 'No batteries found.'}, status=404)
        else:
            battery = session_active.selected_battery

        try:
            v_before = float(data.get('v_before', 0))
            v_after = float(data.get('v_after', 0))
            curr_ma = abs(float(data.get('current', 0)))
            temp = float(data.get('temp', 0))
        except (ValueError, TypeError):
            return JsonResponse({'status': 'error', 'message': 'Invalid numeric data'}, status=400)

        with transaction.atomic():
            i_amps = curr_ma / 1000.0
            delta_v = max(0, v_before - v_after)
            resistance = delta_v / i_amps if i_amps > 0.01 else 0.05
            
            specs = load_battery_specs(battery.chemistry)
            soh = calculate_dynamic_soh(resistance, battery.capacity_mah, specs)
            current_soc = calculate_dynamic_soc(v_before, specs)

            last_pulse = PulseTest.objects.filter(battery=battery).order_by('-timestamp').first()
            increment_cycles = 0
            calculated_energy = 0
            
            if last_pulse:
                soc_diff = float(last_pulse.calculated_soc) - float(current_soc)
                if soc_diff > 0:
                    increment_cycles = soc_diff / 100.0
                    nominal_v = 3.2 if battery.chemistry == 'lifepo4' else 3.7
                    capacity_ah = battery.capacity_mah / 1000.0
                    calculated_energy = (soc_diff / 100.0) * nominal_v * capacity_ah

            battery.cycle_count = float(battery.cycle_count or 0) + increment_cycles
            battery.soh = soh
            battery.save()

            PulseTest.objects.create(
                battery=battery, v_before=v_before, v_after=v_after,
                current_ma=curr_ma, temperature_c=temp,
                internal_resistance=round(resistance, 3),
                calculated_soh=soh, calculated_soc=current_soc
            )

            Reading.objects.create(
                battery=battery, avg_voltage=v_after, avg_current=curr_ma,
                avg_temp=temp, min_voltage=v_after, energy_wh=round(calculated_energy, 4)
            )

            return JsonResponse({'status': 'success', 'battery_id': battery.battery_id}, status=201)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# --- Dashboard ---

@login_required(login_url='login')
def dashboard(request):
    user_batteries = Battery.objects.filter(device__user=request.user).order_by('-id')
    requested_id = request.GET.get('battery_id')
    
    session_active, _ = ActiveSession.objects.get_or_create(user=request.user)

    if requested_id:
        current_battery = get_object_or_404(Battery, id=requested_id, device__user=request.user)
        session_active.selected_battery = current_battery
        session_active.save()
    elif session_active.selected_battery:
        current_battery = session_active.selected_battery
    else:
        current_battery = user_batteries.first()
        if current_battery:
            session_active.selected_battery = current_battery
            session_active.save()

    pulse_tests = []
    last_pulse, last_soc, total_energy = None, 0, 0
    if current_battery:
        pulse_tests = current_battery.pulse_tests.all().order_by('-timestamp')[:20]
        last_pulse = pulse_tests[0] if pulse_tests else None
        last_soc = last_pulse.calculated_soc if last_pulse else 0
        energy_data = Reading.objects.filter(battery=current_battery).aggregate(Sum('energy_wh'))
        total_energy = energy_data['energy_wh__sum'] or 0.0

    context = {
        'current_battery': current_battery,
        'pulse_tests': pulse_tests,
        'last_pulse': last_pulse,
        'user_batteries': user_batteries,
        'last_soc': last_soc,
        'total_energy': round(total_energy, 2),
        'display_name': request.user.email.split('@')[0],
        'api_token': request.user.api_token,
    }
    return render(request, 'monitoring/dashboard.html', context)

# --- التعديل الجوهري هنا ---
@login_required
def add_battery(request):
    if request.method == "POST":
        existing_id = request.POST.get('existing_battery')
        new_label = request.POST.get('battery_id')
        capacity = request.POST.get('capacity_mah') or 2500
        chemistry = request.POST.get('chemistry', 'li-ion').lower()

        device = Device.objects.filter(user=request.user).first()
        if not device:
            device = Device.objects.create(user=request.user, device_id=f"DEV_{uuid.uuid4().hex[:4]}")

        try:
            if existing_id:
                battery = get_object_or_404(Battery, id=existing_id, device__user=request.user)
                battery.capacity_mah = capacity
                battery.chemistry = chemistry
                battery.save()
            elif new_label:
                battery, created = Battery.objects.update_or_create(
                    battery_id=new_label, device=device,
                    defaults={'capacity_mah': capacity, 'chemistry': chemistry}
                )
            else:
                return redirect('dashboard')

            # تحديث الجلسة النشطة بالبطارية الجديدة
            session_active, _ = ActiveSession.objects.get_or_create(user=request.user)
            session_active.selected_battery = battery
            session_active.save()
            
            messages.success(request, f"Battery {battery.battery_id} is now active.")
            
            # الحل: توجيه المستخدم للرابط شاملاً الـ ID الجديد
            return redirect(f"{reverse('dashboard')}?battery_id={battery.id}")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('dashboard')
            
    return redirect('dashboard')

@login_required
def delete_battery(request, battery_id):
    battery = get_object_or_404(Battery, id=battery_id, device__user=request.user)
    session_active = ActiveSession.objects.filter(user=request.user).first()
    if session_active and session_active.selected_battery == battery:
        session_active.selected_battery = None
        session_active.save()
    battery.delete()
    messages.success(request, "Battery deleted.")
    return redirect('dashboard')

@login_required
def update_battery(request, battery_id):
    if request.method == "POST":
        battery = get_object_or_404(Battery, id=battery_id, device__user=request.user)
        battery.capacity_mah = request.POST.get('capacity_mah')
        battery.chemistry = request.POST.get('chemistry').lower()
        battery.save()
        messages.success(request, "Battery updated.")
    return redirect('dashboard')

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'monitoring/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'monitoring/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')