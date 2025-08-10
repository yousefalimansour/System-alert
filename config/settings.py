import os
from pathlib import Path
import environ
from datetime import timedelta


BASE_DIR = Path(__file__).resolve().parent.parent

# read env
env = environ.Env(DEBUG=(bool, False))
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = '@mdobo_fu=9r(v)!$ts%j0tc4sqnqiu4(v&nl$h*zzu_vt&r&w'
DEBUG = env('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=["localhost", "127.0.0.1"])

# apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_celery_beat',

    # local apps
    'apps.alerts',
    'apps.stocks',
    'apps.users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# TEMPLATES configuration - KEEP THIS ONE, REMOVE THE DUPLICATE
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database: uses DATABASE_URL env if provided, otherwise fallback to sqlite
DATABASES = {
    'default': env.db(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Password validation (default)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery (Redis)
REDIS_URL = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# REST framework + JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Email settings (for SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='moradyousef954@gmail.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='moradyousef954@gmail.com')

AUTH_USER_MODEL = 'users.User'

# Celery configuration
from celery.schedules import crontab

# Note: CELERY_BROKER_URL and CELERY_RESULT_BACKEND are already defined above
CELERY_TIMEZONE = 'Africa/Cairo'
CELERY_ENABLE_UTC = False

CELERY_BEAT_SCHEDULE = {
    'fetch-stock-prices-every-minute': {
        'task': 'apps.stocks.tasks.fetch_stock_prices',
        'schedule': crontab(minute='*/1'),
    },
    'send-price-digest-every-3-minutes': {
        'task': 'apps.stocks.tasks.send_price_digest',
        'schedule': crontab(minute='*/3'),
    },
}

# REMOVED: Duplicate TEMPLATES configuration that was causing the error