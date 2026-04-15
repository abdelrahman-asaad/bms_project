import os
from pathlib import Path

# بناء المسارات
BASE_DIR = Path(__file__).resolve().parent.parent

# كود ذكي لمعرفة هل نحن على سيرفر PythonAnywhere أم لا
ON_PYTHONANYWHERE = 'PYTHONANYWHERE_DOMAIN' in os.environ

# --- إعدادات الأمان ---
SECRET_KEY = 'django-insecure-8vv-5f53mvusf8c$#o%l58x3)-x2e2k2j*cmhj+d*-!zcw-_2!'

# يكون True في اللوكل و False على السيرفر لزيادة الأمان
DEBUG = not ON_PYTHONANYWHERE

if ON_PYTHONANYWHERE:
    # استبدل 'yourusername' باسم حسابك الحقيقي على الموقع
    ALLOWED_HOSTS = ['asaad77.pythonanywhere.com'] 
else:
    ALLOWED_HOSTS = ['*']

# --- التطبيقات ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'monitoring',
]

AUTH_USER_MODEL = 'monitoring.User'

# --- الميدل وير (تم إضافة WhiteNoise للـ Static Files) ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # ضروري جداً للسيرفر
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bms_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bms_project.wsgi.application'

# --- قاعدة البيانات (SQLite كما طلبت) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- التحقق من كلمة المرور ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- الإعدادات الإقليمية ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Cairo' # خليتها توقيت القاهرة عشان قراءات البطارية تكون دقيقة
USE_I18N = True
USE_TZ = True

# --- الملفات الثابتة (Static Files) ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # الفولدر اللي هيتجمع فيه الملفات على السيرفر

# إعداد WhiteNoise لضغط الملفات وتسريع الموقع
if ON_PYTHONANYWHERE:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGIN_REDIRECT_URL = 'dashboard'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'