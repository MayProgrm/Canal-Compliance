from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-(0mnaf(jehjmj)9zk9oo9syi6vl9%*ohx0kr$6j0#^3x)i@6u4')
DEBUG = True
ALLOWED_HOSTS = ['*']
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict' if not DEBUG else 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict' if not DEBUG else 'Lax'
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000', 'http://0.0.0.0:8000']
if not DEBUG:
    _csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS')
    if _csrf_origins:
        CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'denuncias']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'denuncias.middleware.SecurityHeadersMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'denuncias.middleware.DevDisableCSRFMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'canal_denuncias.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'canal_denuncias.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True
LOGGING = {'version': 1, 'disable_existing_loggers': False, 'formatters': {'verbose': {'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}', 'style': '{'}, 'simple': {'format': '{levelname} {message}', 'style': '{'}}, 'handlers': {'file': {'level': 'INFO', 'class': 'logging.FileHandler', 'filename': str(BASE_DIR / 'canal_denuncias.log'), 'formatter': 'verbose'}, 'console': {'level': 'DEBUG', 'class': 'logging.StreamHandler', 'formatter': 'simple'}}, 'root': {'handlers': ['console', 'file'], 'level': 'INFO'}, 'loggers': {'django': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False}, 'denuncias': {'handlers': ['console', 'file'], 'level': 'DEBUG', 'propagate': False}}}
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-snowflake'}}
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 420
ALLOWED_UPLOAD_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mp3', '.wav', '.ogg', '.m4a', '.aac', '.zip', '.rar', '.7z', '.tar', '.gz']
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ADMIN_LOGIN_TOKEN = os.environ.get('ADMIN_LOGIN_TOKEN', '')
if DEBUG and (not ADMIN_LOGIN_TOKEN):
    ADMIN_LOGIN_TOKEN = 'admin-login-dev'
AUTH_USER_MODEL = 'denuncias.CustomUser'
ADMIN_INVITE_CODE = os.environ.get('ADMIN_INVITE_CODE', 'admin-invite-dev')
if DEBUG:
    ADMIN_INVITE_CODE = 'admin-invite-dev'
ADMIN_INVITE_SECRET = os.environ.get('ADMIN_INVITE_SECRET', '')
if DEBUG:
    ADMIN_INVITE_SECRET = ''
ADMIN_DEV_BYPASS = os.environ.get('ADMIN_DEV_BYPASS', 'true').lower() in ('1', 'true', 'yes')
SECURE_REFERRER_POLICY = 'no-referrer'
