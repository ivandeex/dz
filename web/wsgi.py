import os
import logging
import dz
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")
application = get_wsgi_application()

logging.getLogger('dz').info('DZ server started, v%s', dz.version)
