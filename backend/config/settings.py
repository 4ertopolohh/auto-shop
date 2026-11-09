import os
import secrets
from pathlib import Path
from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent.parent
DEMO_SITE = True  # This distribution never accepts real customer data or payments.
LOCAL_ENVIRONMENT = os.environ.get('SHOP_ENV', 'local') == 'local'
DEBUG = LOCAL_ENVIRONMENT
PRIVATE_DIR = BASE_DIR / '.local'
PRIVATE_DIR.mkdir(mode=0o700, exist_ok=True)
def local_secret(name, factory):
    path = PRIVATE_DIR / name
    if not path.exists():
        path.write_text(factory(), encoding='utf-8')
        path.chmod(0o600)
    return path.read_text(encoding='utf-8').strip()
if LOCAL_ENVIRONMENT:
    SECRET_KEY = local_secret('django.key', lambda: secrets.token_urlsafe(64))
    FIELD_KEY = local_secret('fields.key', lambda: Fernet.generate_key().decode())
else:
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
    FIELD_KEY = os.environ['FIELD_ENCRYPTION_KEY']
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver'] if DEBUG else os.environ.get('ALLOWED_HOSTS', '').split(',')
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'shop.apps.ShopConfig']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'shop' / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3', 'OPTIONS': {'timeout': 20}}}
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CSRF_TRUSTED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173'] if DEBUG else []
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = not DEBUG
X_FRAME_OPTIONS = 'DENY'
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
# Access logs contain paths and status only. Checkout never accepts contact fields.
LOGGING = {'version': 1, 'disable_existing_loggers': False, 'handlers': {'null': {'class': 'logging.NullHandler'}}, 'loggers': {'django.request': {'handlers': ['null'], 'propagate': False}}}
