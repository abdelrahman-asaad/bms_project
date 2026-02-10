from django.contrib import admin
from .models import User, Device, Battery, Reading, Alert

# -------- User --------
#@admin.register(User)
#class UserAdmin(admin.ModelAdmin):
#    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
#    search_fields = ('email', 'first_name', 'last_name')
#    list_filter = ('is_staff', 'is_active')
#    ordering = ('email',)


# -------- Device --------
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'user', 'name', 'firmware_version', 'last_seen', 'is_active', 'created_at')
    search_fields = ('device_id', 'name', 'user__email')
    list_filter = ('is_active', 'firmware_version')
    ordering = ('device_id',)


# -------- Battery --------
@admin.register(Battery)
class BatteryAdmin(admin.ModelAdmin):
    list_display = ('battery_id', 'device', 'capacity_mah', 'chemistry', 'soh', 'cycle_count', 'installed_at')
    search_fields = ('battery_id', 'device__device_id', 'device__user__email')
    list_filter = ('chemistry',)
    ordering = ('battery_id',)


# -------- Reading --------
@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = (
        'battery', 'timestamp', 'avg_voltage', 'avg_current', 'avg_temp',
        'min_voltage', 'max_temp', 'power_avg', 'energy_wh', 'samples_count', 'period_seconds'
    )
    list_filter = ('battery__device', 'battery', 'timestamp')
    search_fields = ('battery__battery_id', 'battery__device__device_id')
    ordering = ('-timestamp',)


# -------- Alert --------
@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('battery', 'alert_type', 'value', 'threshold', 'severity', 'triggered_at', 'is_resolved', 'resolved_at')
    list_filter = ('alert_type', 'severity', 'is_resolved')
    search_fields = ('battery__battery_id', 'battery__device__device_id')
    ordering = ('-triggered_at',)
