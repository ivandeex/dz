# -*- coding: utf-8 -*-
import os
import dj_database_url
import django


_django_version = django.VERSION[0] * 100 + django.VERSION[1]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from honcho.environ import parse as parse_env
    with open(os.path.join(BASE_DIR, '.env')) as f:
        for name, value in parse_env(f.read()).items():
            os.environ.setdefault(name, value)
except IOError:
    pass

getenv = os.environ.get


DEBUG = bool(int(getenv('DEBUG', False)))
DEBUG_SQL = bool(int(getenv('DEBUG_SQL', DEBUG)))
DEBUG_API = bool(int(getenv('DEBUG_API', DEBUG)))
HEROKU = bool(int(getenv('HEROKU', not DEBUG)))

SECRET_KEY = getenv('SECRET_KEY', 'please change me')

ALLOWED_HOSTS = getenv('ALLOWED_HOSTS', 'localhost').split(',')

DATABASES = {'default': dj_database_url.config(conn_max_age=600)}

ROOT_URLCONF = 'web.urls'
WSGI_APPLICATION = 'web.wsgi.application'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'dist', 'static')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'assets')
]


_webpack_stats_static = os.path.join(BASE_DIR, 'webpack/stats.json')
_webpack_stats_hotserver = os.path.join(BASE_DIR, 'webpack/stats.hotserver.json')
if DEBUG and os.path.exists(_webpack_stats_hotserver):
    _webpack_stats_file = _webpack_stats_hotserver
else:
    _webpack_stats_file = _webpack_stats_static

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': '/',
        'STATS_FILE': _webpack_stats_file
    }
}


USE_I18N = True
LANGUAGE_CODE = 'en'
LANGUAGE_COOKIE_NAME = 'lang'
LANGUAGES = [
    ('en', u'English (US)'),
    ('sl', u'Slovenščina'),
    ('ru', u'Русский'),
]
LOCALE_PATHS = []


DEBUG_SESSIONS = bool(int(getenv('DEBUG_SESSIONS', False)))
if DEBUG_SESSIONS:
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'


INSTALLED_APPS = [
    'dz',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # same as manage.py runserver --nostatic
    'django.contrib.staticfiles',     # for manage.py collectstatic

    'import_export',
    'webpack_loader',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if _django_version < 110:
    MIDDLEWARE_CLASSES = MIDDLEWARE


if DEBUG and USE_I18N:
    INSTALLED_APPS += ['rosetta']
    # rosetta does not look into locale directories of installed apps
    LOCALE_PATHS += [os.path.join(BASE_DIR, 'dz', 'locale')]


DEBUG_TOOLBAR_ENABLED = bool(int(getenv('DEBUG_TOOLBAR', True)))

if DEBUG and DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS += ['debug_toolbar']
    INTERNAL_IPS = getenv('INTERNAL_IPS', '127.0.0.1').split(',')
    DEBUG_TOOLBAR_CONFIG = {'SHOW_COLLAPSED': True}
    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    if _django_version < 110:
        MIDDLEWARE_CLASSES.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    else:
        from django.utils.deprecation import MiddlewareMixin
        from debug_toolbar.middleware import DebugToolbarMiddleware

        class Django110DebugToolbarMiddleware(MiddlewareMixin, DebugToolbarMiddleware):
            pass

        MIDDLEWARE.insert(0, 'web.settings.Django110DebugToolbarMiddleware')


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


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 4}
    }
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
        'dz': {
            'handlers': ['debug_console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Time zone
USE_TZ = True
TIME_ZONE = 'CET'

USE_L10N = False
DATETIME_FORMAT = 'Y-m-d H:i'
TIME_FORMAT = 'H:i'
TIME_INPUT_FORMATS = ['%H:%M']


# Migration from MongoDB
MONGODB_URL = getenv('MONGODB_URL', '')


# Custom DZ settings
SPIDER_TIME_ZONE = getenv('SPIDER_TIME_ZONE', TIME_ZONE)
SPIDER_SECRET_KEY = getenv('SPIDER_SECRET_KEY', 'please change me')
SPIDER_PAGE_DELAY = int(getenv('SPIDER_PAGE_DELAY', 50))
SPIDER_LOAD_IMAGES = bool(int(getenv('SPIDER_LOAD_IMAGES', True)))
SPIDER_USERPASS = getenv('SPIDER_USERPASS', '')
SPIDER_LOG_LEVEL = getenv('SPIDER_LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO')
NARROW_GRIDS = bool(int(getenv('NARROW_GRIDS', False)))
