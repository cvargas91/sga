"""
Django settings for uaysenOnline project.

Generated by 'django-admin startproject' using Django 3.0.9.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

from datetime import timedelta

from django.conf.locale.en import formats as en_formats

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'supersecretkey')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost;127.0.0.1;testserver').split(';')

# chequear si es que la app está detrás de un proxy (si tiene X-Forwarded-Host en el header)
USE_X_FORWARDED_HOST = True


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',
    'rest_framework',
    'corsheaders',

    'academica',
    'certificados',
    'curso',
    'inscripcion',
    'general',
    'persona',
    'mails',
    'matricula',
    'pagos',
    'pagare',
    'ucampus',
    'uaysenOnline',
    'solicitudes',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'persona.permisos.TodosSoloLeer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'uaysen-online-backend - SGA',
    'DESCRIPTION': 'APIs del Sistema de Gestión Académica',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'SIGNING_KEY': SECRET_KEY,
}

ROOT_URLCONF = 'uaysenOnline.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [f'{BASE_DIR}/uaysenOnline/templates'],
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

WSGI_APPLICATION = 'uaysenOnline.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
# si no se encuentran las variables de ambiente utilizar sqlite  (desarrollo)

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DJANGO_DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('POSTGRES_DB', os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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

# configuracion de logs
log_level = os.getenv('DJANGO_LOG_LEVEL', 'ERROR')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': log_level,
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': log_level,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': log_level,
            'propagate': True,
        },
        'rest_framework': {
            'handlers': ['console', 'file'],
            'level': log_level,
            'propagate': False,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_L10N = True

USE_TZ = True

en_formats.DATETIME_FORMAT = "d/m/y H:i"


# CORS configuration
CORS_ORIGIN_ALLOW_ALL = False

# url host para redirección de webpay
URL_BACKEND = os.getenv('DJANGO_URL_BACKEND', 'http://localhost:8000')

# url matricula para redirecciones luego de confirmación pago matricula
URL_FRONTEND_MATRICULA = os.getenv('DJANGO_URL_MATRICULA', 'http://localhost:8080')

# url matricula para redirecciones luego de confirmación pago matricula
URL_FRONTEND_SGA = os.getenv('DJANGO_URL_SGA', 'http://localhost:8080')

URL_FRONTEND_SGA_NUEVO = os.getenv('DJANGO_URL_SGA_NUEVO', 'http://localhost:8080')

URL_FRONTEND_SGA_LOCAL = os.getenv('DJANGO_URL_SGA_LOCAL', 'http://localhost:3000')

CORS_ORIGIN_WHITELIST = [URL_FRONTEND_MATRICULA, URL_FRONTEND_SGA, URL_FRONTEND_SGA_NUEVO, URL_FRONTEND_SGA_LOCAL]

# permitir tokens CSRf desde el backend (django admin)
CSRF_TRUSTED_ORIGINS = [URL_BACKEND]


# configuración webpay (en desarrollo se conecta a la API de prueba)
WEBPAY_CODIGO_COMERCIO = os.getenv('DJANGO_WEBPAY_CODIGO_COMERCIO', '597055555532')
WEBPAY_API_KEY = os.getenv(
    'DJANGO_WEBPAY_API_KEY', '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C')
WEBPAY_TIPO_INTEGRACION = os.getenv('DJANGO_WEBPAY_TIPO_INTEGRACION', 'TEST')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


# configuración de mails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv('DJANGO_MAIL_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('DJANGO_MAIL_PASSWORD', '')


# configuración google cloud platform
GOOGLE_ADMIN_ACCOUNT = os.getenv('DJANGO_GOOGLE_ADMIN_ACCOUNT', 'sga@uaysen.cl')
SPREADSHEET_ENCUESTA_ID = os.getenv('DJANGO_SPREADSHEET_ENCUESTA_ID', '')

# configuración API ucampus
UCAMPUS_API = os.getenv('DJANGO_UCAMPUS_API', 'https://ucampus.uaysen.cl/api/0/mufasa')
UCAMPUS_USER = os.getenv('DJANGO_UCAMPUS_USER', '')
UCAMPUS_PASS = os.getenv('DJANGO_UCAMPUS_PASS', '')

QUESTIONPRO_APIKEY = os.getenv('DJANGO_QUESTIONPRO_APIKEY', '')