# -------- User --------
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    # التوكن الفريد لكل مستخدم
    api_token = models.CharField(max_length=100, unique=True, default=uuid.uuid4, editable=False)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} (Token: {self.api_token[:8]}...)"

# -------- Device (ESP32) --------
class Device(models.Model):
    device_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=100, blank=True, null=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device_id} ({self.user.email})"

# -------- Battery --------
class Battery(models.Model):
    battery_id = models.CharField(max_length=100, unique=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='batteries')
    capacity_mah = models.FloatField(default=0.0)
    chemistry = models.CharField(max_length=50, default='Li-ion')
    installed_at = models.DateTimeField(default=timezone.now)
    soh = models.FloatField(default=100.0)  # State of Health %
    cycle_count = models.IntegerField(default=0)
    class Meta:
        verbose_name = "Battery"
        verbose_name_plural = "Batteries"  # <-- هنا اسم الجمع الصحيح
    def __str__(self):
        return f"{self.battery_id} ({self.device.device_id})"

# -------- Reading (Aggregated) --------
class Reading(models.Model):
    battery = models.ForeignKey(Battery, on_delete=models.CASCADE, related_name='readings')
    avg_voltage = models.FloatField()
    avg_current = models.FloatField()
    avg_temp = models.FloatField()
    min_voltage = models.FloatField()
    max_temp = models.FloatField(null=True, blank=True)  # تعديل
    power_avg = models.FloatField(null=True, blank=True) # تعديل
    energy_wh = models.FloatField(null=True, blank=True) # تعديل
    samples_count = models.IntegerField(default=1)       # تعديل (قيمة افتراضية)
    period_seconds = models.IntegerField(default=5)      # تعديل (قيمة افتراضية)
    timestamp = models.DateTimeField(auto_now_add=True)  # تعديل (ليأخذ الوقت الحالي تلقائياً)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['battery', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.battery.name} - {self.timestamp}"
# -------- Alert --------
class Alert(models.Model):
    ALERT_TYPES = [
        ('over_voltage', 'Over Voltage'),
        ('over_temp', 'Over Temperature'),
        ('over_current', 'Over Current'),
        ('low_soc', 'Low SOC'),
    ]
    battery = models.ForeignKey(Battery, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    value = models.FloatField()
    threshold = models.FloatField()
    severity = models.CharField(max_length=20, default='medium')
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-triggered_at']

    def __str__(self):
        return f"{self.alert_type} - {self.battery.battery_id} - {self.triggered_at}"

class PulseTest(models.Model):
    battery = models.ForeignKey(Battery, on_delete=models.CASCADE, related_name='pulse_tests')
    v_before = models.FloatField()
    v_after = models.FloatField()
    current_ma = models.FloatField()
    temperature_c = models.FloatField()
    
    # حقول حسابية
    internal_resistance = models.FloatField(null=True, blank=True)
    calculated_soh = models.FloatField(null=True, blank=True)
    calculated_soc = models.FloatField(null=True, blank=True) # نسبة الشحن %
    
    timestamp = models.DateTimeField(auto_now_add=True)

class ActiveSession(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='active_session')
    selected_battery = models.ForeignKey(Battery, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} -> {self.selected_battery}"    