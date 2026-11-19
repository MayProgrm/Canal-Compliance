from pathlib import Path
import secrets
import dj_database_url
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = secrets.token_urlsafe(50)
    else:
        raise ImproperlyConfigured('Define SECRET_KEY en el entorno antes de iniciar Django.')
if not DEBUG and len(SECRET_KEY) < 50:
    raise ImproperlyConfigured('SECRET_KEY debe tener al menos 50 caracteres en producción.')

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,0.0.0.0',
    cast=Csv(),
)
if not DEBUG and '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured('ALLOWED_HOSTS no puede incluir * fuera de DEBUG.')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict' if not DEBUG else 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict' if not DEBUG else 'Lax'
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000,http://0.0.0.0:8000',
    cast=Csv(),
)
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'rest_framework', 'corsheaders', 'denuncias']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware', 'denuncias.middleware.SecurityHeadersMiddleware', 'corsheaders.middleware.CorsMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'denuncias.middleware.LocalCsrfOriginMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'canal_denuncias.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages', 'denuncias.middleware.csp_nonce']}}]
WSGI_APPLICATION = 'canal_denuncias.wsgi.application'
DATABASES = {'default': dj_database_url.parse(config('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"), conn_max_age=600, conn_health_checks=True)}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True
LOGGING = {'version': 1, 'disable_existing_loggers': False, 'formatters': {'verbose': {'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}', 'style': '{'}, 'simple': {'format': '{levelname} {message}', 'style': '{'}}, 'handlers': {'file': {'level': 'INFO', 'class': 'logging.FileHandler', 'filename': str(BASE_DIR / 'canal_denuncias.log'), 'formatter': 'verbose'}, 'console': {'level': 'DEBUG', 'class': 'logging.StreamHandler', 'formatter': 'simple'}}, 'root': {'handlers': ['console', 'file'], 'level': 'INFO'}, 'loggers': {'django': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False}, 'denuncias': {'handlers': ['console', 'file'], 'level': 'DEBUG', 'propagate': False}}}
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='no-reply@localhost')
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-snowflake'}}
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 5
FILE_UPLOAD_PERMISSIONS = 420
ALLOWED_UPLOAD_EXTENSIONS = [
    extension if extension.startswith('.') else f'.{extension}'
    for extension in config(
        'ALLOWED_UPLOAD_EXTENSIONS',
        default='.pdf,.doc,.docx,.txt,.rtf,.odt,.jpg,.jpeg,.png,.gif,.bmp,.webp,.mp4,.avi,.mov,.wmv,.flv,.webm,.mp3,.wav,.ogg,.m4a,.aac,.zip,.rar,.7z,.tar,.gz',
        cast=Csv(),
    )
]
MAX_UPLOAD_SIZE = config('MAX_UPLOAD_SIZE', default=10 * 1024 * 1024, cast=int)
USE_X_FORWARDED_FOR = config('USE_X_FORWARDED_FOR', default=False, cast=bool)
TRUSTED_PROXY_COUNT = config('TRUSTED_PROXY_COUNT', default=1, cast=int)
DATA_UPLOAD_MAX_NUMBER_FIELDS = config('DATA_UPLOAD_MAX_NUMBER_FIELDS', default=500, cast=int)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ADMIN_LOGIN_TOKEN = config('ADMIN_LOGIN_TOKEN', default='')
AUTH_USER_MODEL = 'denuncias.CustomUser'
ADMIN_INVITE_CODE = config('ADMIN_INVITE_CODE', default='')
ADMIN_INVITE_SECRET = config('ADMIN_INVITE_SECRET', default='')
ADMIN_DEV_BYPASS = config('ADMIN_DEV_BYPASS', default=False, cast=bool)
SECURE_REFERRER_POLICY = 'no-referrer'

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'anon': '60/min'},
}
CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())
