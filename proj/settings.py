# -*- coding: utf-8 -*-
import os
import dj_database_url
from vanko.utils import getenv


# Settings: https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

DEBUG = getenv('DEBUG', False)
DEBUG_SQL = getenv('DEBUG_SQL', DEBUG)
HEROKU = getenv('HEROKU', not DEBUG)

SECRET_KEY = getenv('SECRET_KEY', 'ahXeija:eth;ahyuagohheez3uok|eoXohNaiyaphaiJiyeeyi')

ALLOWED_HOSTS = getenv('ALLOWED_HOSTS', 'localhost').split(',')

DATABASES = {'default': dj_database_url.config(conn_max_age=600)}

ROOT_URLCONF = 'proj.urls'

WSGI_APPLICATION = 'proj.wsgi.application'

# Static files: https://docs.djangoproject.com/en/1.9/howto/static-files/

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_URL = '/static/'

# I18n: https://docs.djangoproject.com/en/1.9/topics/i18n/

USE_I18N = True
USE_L10N = False
LANGUAGE_CODE = 'en-us'
LANGUAGE_COOKIE_NAME = 'lang'

USE_TZ = True
TIME_ZONE = 'Europe/Ljubljana'
DATETIME_FORMAT = 'Y-m-d H:i:s'

LANGUAGES = [
    ('en', u'English (US)'),
    ('sl', u'Slovenščina'),
    ('ru', u'Русский'),
]

INSTALLED_APPS = [
    'dz',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'import_export',
]

if DEBUG:
    INTERNAL_IPS = getenv('INTERNAL_IPS', '127.0.0.1').split(',')

    INSTALLED_APPS += [
        'debug_toolbar',
    ]

    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_COLLAPSED': True,
    }

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [os.path.join(BASE_DIR, 'templates', 'jinja2')],
        'APP_DIRS': True,
        'OPTIONS': {
        },
    },
]

if DEBUG:
    TEMPLATES[0]['APP_DIRS'] = True
    del TEMPLATES[0]['OPTIONS']['loaders']

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s %(module)s] %(message)s',
        },
    },
    'handlers': {
        'debug_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.db': {
            'handlers': ['debug_console'],
            'level': 'DEBUG' if DEBUG_SQL else 'CRITICAL',
            'propagate': False,
        },
    },
}

# Custom DZ settings

NARROW_GRIDS = getenv('NARROW_GRIDS', False)