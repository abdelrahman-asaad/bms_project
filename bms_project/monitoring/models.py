# -------- User --------

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
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'  # <-- هنا التسجيل هيبقى بالإيميل
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


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
    max_temp = models.FloatField()
    power_avg = models.FloatField()
    energy_wh = models.FloatField()
    samples_count = models.IntegerField()
    period_seconds = models.IntegerField()
    timestamp = models.DateTimeField()

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['battery', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.battery.battery_id} - {self.timestamp}"

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
