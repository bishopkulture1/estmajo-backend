import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', '')
if len(SECRET_KEY) < 32:
    raise ImproperlyConfigured('Set SECRET_KEY to a random value of at least 32 characters.')
ALLOWED_HOSTS = [v.strip() for v in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if v.strip()]
# Render supplies its own exact hostname; never enable wildcard hosts.
if os.getenv('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
CSRF_TRUSTED_ORIGINS = list(filter(None, os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')))
INSTALLED_APPS = ['django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.staticfiles','rest_framework','core']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','core.middleware.ApiBoundaryMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
from .database import postgres_database
if os.getenv('DATABASE_URL'):
    DATABASES = {'default':postgres_database(os.environ['DATABASE_URL'], DEBUG)}
elif os.getenv('RENDER') == 'true':
    raise ImproperlyConfigured('Render requires external PostgreSQL DATABASE_URL; ephemeral SQLite is disabled.')
else:
    # SQLite remains available for local development and the legacy disk-based deployment.
    DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':os.getenv('SQLITE_PATH', str(BASE_DIR/'data/db.sqlite3')), 'OPTIONS': {'timeout':30}}}
    Path(DATABASES['default']['NAME']).parent.mkdir(parents=True, exist_ok=True)
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.'+n} for n in ['UserAttributeSimilarityValidator','MinimumLengthValidator','CommonPasswordValidator','NumericPasswordValidator']]
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES':['rest_framework.authentication.SessionAuthentication'], 'DEFAULT_PERMISSION_CLASSES':['core.permissions.IsOwner'], 'UNAUTHENTICATED_USER':None}
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 28800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SECURE_SSL_REDIRECT = not DEBUG
# Render health checks must read the database, not succeed on an HTTPS redirect.
SECURE_REDIRECT_EXEMPT = [r'^_health/$']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO','https')
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
TIME_ZONE = 'UTC'
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR/'staticfiles'
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND','django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST','')
EMAIL_PORT = int(os.getenv('EMAIL_PORT','587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER','')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD','')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS','true').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL','false').lower() == 'true'
EMAIL_TIMEOUT = 20
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL','')
IMAGEKIT_PRIVATE_KEY = os.getenv('IMAGEKIT_PRIVATE_KEY','')
IMAGEKIT_URL_ENDPOINT = os.getenv('IMAGEKIT_URL_ENDPOINT','').rstrip('/')
MAX_IMAGE_BYTES = int(os.getenv('MAX_IMAGE_BYTES','10485760'))
MAX_VIDEO_BYTES = int(os.getenv('MAX_VIDEO_BYTES','104857600'))
MAX_DOCUMENT_BYTES = int(os.getenv('MAX_DOCUMENT_BYTES','20971520'))
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_VIDEO_BYTES + 1048576
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440

# Optional Netlify deployment boundary. Leave empty for the original direct Caddy deployment.
NETLIFY_PROXY_SECRET = os.getenv('NETLIFY_PROXY_SECRET','')

# Resend HTTPS transport for Render Free (standard SMTP ports are blocked).
RESEND_API_KEY = os.getenv('RESEND_API_KEY','')
