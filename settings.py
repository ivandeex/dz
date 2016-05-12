"""
The DZ project.
"""

import os
import dj_database_url

from vanko.utils import getenv


# Settings: https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

DEBUG = getenv('DEBUG', 0)

HEROKU = getenv('HEROKU', 0)

SECRET_KEY = getenv('SECRET_KEY', 'ahqua4zie{S[i*o#choCa(Th?oh6oonu')

ALLOWED_HOSTS = getenv('ALLOWED_HOSTS', 'localhost').split(',')

DATABASES = {'default': dj_database_url.config()}

ROOT_URLCONF = 'dz.urls'

# WSGI_APPLICATION = 'dz.wsgi.application'

# Static files: https://docs.djangoproject.com/en/1.9/howto/static-files/

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_URL = '/static/'

# I18n: https://docs.djangoproject.com/en/1.9/topics/i18n/

USE_I18N = True
USE_L10N = False
LANGUAGE_CODE = 'en-us'

USE_TZ = True
TIME_ZONE = 'Europe/Ljubljana'
DATETIME_FORMAT = 'Y-m-d H:i:s'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dz',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
