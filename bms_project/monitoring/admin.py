from django.contrib import admin
from .models import User, Device, Battery, Reading, Alert, PulseTest

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


# -------- PulseTest --------
@admin.register(PulseTest)
class PulseTestAdmin(admin.ModelAdmin):
    # الأعمدة اللي هتظهر في الجدول الرئيسي
    list_display = (
        'battery', 
        'v_before', 
        'v_after', 
        'current_ma', 
        'internal_resistance_display', # هنعرفها تحت عشان نظهر الوحدة
        'calculated_soc_display',
        'calculated_soh_display',
        'timestamp'
    )
    
    # إضافة فلاتر على الجنب لسهولة البحث
    list_filter = ('battery', 'timestamp')
    
    # إضافة إمكانية البحث بمعرف البطارية
    search_fields = ('battery__battery_id',)
    
    # جعل الحقول الحسابية "للقراءة فقط" في صفحة التعديل
    readonly_fields = ('timestamp', 'internal_resistance', 'calculated_soh', 'calculated_soc')

    # تحسين شكل عرض المقاومة الداخلية في الجدول
    def internal_resistance_display(self, obj):
        if obj.internal_resistance:
            return f"{obj.internal_resistance:.3f} Ω"
        return "N/A"
    internal_resistance_display.short_description = "Resistance (Ω)"

    # تحسين شكل عرض نسبة الشحن
    def calculated_soc_display(self, obj):
        if obj.calculated_soc is not None:
            return f"{obj.calculated_soc}%"
        return "N/A"
    calculated_soc_display.short_description = "SoC"

    # تحسين شكل عرض حالة البطارية
    def calculated_soh_display(self, obj):
        if obj.calculated_soh is not None:
            return f"{obj.calculated_soh}%"
        return "N/A"
    calculated_soh_display.short_description = "SoH"