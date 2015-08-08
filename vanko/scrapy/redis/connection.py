"""
This source code is based on the scrapy_redis project located at
  https://github.com/rolando/scrapy-redis
Copyright (c) Rolando Espinoza La fuente
All rights reserved.
"""

# Default values.
REDIS_URL = None
REDIS_HOST = 'localhost'
REDIS_PORT = 6379


def from_settings(settings):
    from redis import Redis, from_url

    url = settings.get('REDIS_URL',  REDIS_URL)
    if url:
        return from_url(url)
    else:
        host = settings.get('REDIS_HOST', REDIS_HOST)
        port = settings.get('REDIS_PORT', REDIS_PORT)
        return Redis(host=host, port=port)
