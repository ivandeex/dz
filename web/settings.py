# -*- coding: utf-8 -*-
import django
import environ
from django.utils.translation import ugettext_lazy as _


django_ver = django.VERSION[0] * 100 + django.VERSION[1]
root = environ.Path(__file__) - 2
env = environ.Env()
env.read_env(root('.env'))


DZ_SKIN = env.str('DZ_SKIN', 'grappelli')
assert DZ_SKIN in ('django', 'plus', 'grappelli', 'bootstrap')

DZ_COMPAT = env.bool('DZ_COMPAT', False)


BASE_DIR = root()

DEBUG = env.bool('DEBUG', False)
DEBUG_SQL = env.bool('DEBUG_SQL', DEBUG)
DEBUG_API = env.bool('DEBUG_API', DEBUG)

# ALLOWED_HOSTS is required by production mode
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])

# INTERNAL_IPS is required by debug toolbar and debug context processor
INTERNAL_IPS = env.list('INTERNAL_IPS', default=['127.0.0.1'])


SECRET_KEY = env.str('SECRET_KEY', 'please change me')

DATABASES = {'default': env.db()}

ROOT_URLCONF = 'web.urls'
WSGI_APPLICATION = 'web.wsgi.application'

STATIC_URL = '/static/'
STATIC_ROOT = root('static')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [
    root('public')
]


WEBPACK_SUBDIR = 'devel' if DEBUG else 'prod'
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': '/' + WEBPACK_SUBDIR,
        'STATS_FILE': root('stats-%s.json' % WEBPACK_SUBDIR)
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


DEBUG_SESSIONS = env.bool('DEBUG_SESSIONS', False)
if DEBUG_SESSIONS:
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'


INSTALLED_APPS = [
    'dz',  # override django admin templates, most importantly base_site.html

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # same as manage.py runserver --nostatic
    'django.contrib.staticfiles',     # for manage.py collectstatic

    'django_tables2',
    'bootstrap3',
    'import_export',
    'webpack_loader',
    'constance',
    'constance.backends.database',
]

if DZ_SKIN == 'grappelli':
    # override dz's admin templates, in particular base_site.html
    INSTALLED_APPS.insert(0, 'grappelli')
    GRAPPELLI_ADMIN_TITLE = _('D.Z.')

if DZ_SKIN == 'bootstrap':
    INSTALLED_APPS.insert(0, 'django_admin_bootstrapped')
    DAB_FIELD_RENDERER = 'django_admin_bootstrapped.renderers.BootstrapFieldRenderer'

    from django.contrib import messages
    MESSAGE_TAGS = {
        messages.INFO: 'alert-info info',
        messages.SUCCESS: 'alert-success success',
        messages.WARNING: 'alert-warning warning',
        messages.ERROR: 'alert-danger error'
    }


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

if django_ver < 110:
    MIDDLEWARE_CLASSES = MIDDLEWARE


DEBUG_TOOLBAR_ENABLED = env.bool('DEBUG_TOOLBAR', True)

if DEBUG and DEBUG_TOOLBAR_ENABLED:
    INSTALLED_APPS += ['debug_toolbar']
    DEBUG_TOOLBAR_CONFIG = {'SHOW_COLLAPSED': True}
    DEBUG_TOOLBAR_PATCH_SETTINGS = False

    if django_ver < 110:
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
        'DIRS': [root('templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dz.admin.context_processors.dz_skin',
                'dz.admin.context_processors.dz_compat',
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
        'DIRS': [root('templates', 'jinja2')],
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
            'format': '%(asctime)s [%(process)d] [%(levelname)s %(module)s] %(message)s',
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


# DZ - Migration from MongoDB
MONGODB_URL = env.str('MONGODB_URL', '')

# DZ - Custom settings
FIELD_CUT_LENGTH = 120

# DZ - Spider settings
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_SUPERUSER_ONLY = False

CONSTANCE_CONFIG = {
    'SPIDER_TIME_ZONE': (
        env.str('SPIDER_TIME_ZONE', TIME_ZONE),
        'spider time zone'
    ),
    'SPIDER_SECRET_KEY': (
        env.str('SPIDER_SECRET_KEY', 'please change me'),
        'spider secret key'
    ),
    'SPIDER_PAGE_DELAY': (
        env.int('SPIDER_PAGE_DELAY', 50),
        'random delay betweeb news pages'
    ),
    'SPIDER_LOAD_IMAGES': (
        env.bool('SPIDER_LOAD_IMAGES', True),
        'enable loading images with pages'
    ),
    'SPIDER_USERPASS': (
        env.str('SPIDER_USERPASS', ''),
        'site user:password'
    ),
    'SPIDER_LOG_LEVEL': (
        env.str('SPIDER_LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO'),
        'spider log level (DEBUG, INFO, etc)'
    ),
}
