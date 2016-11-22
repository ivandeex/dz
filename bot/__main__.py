#!/usr/bin/env python
import os
import sys


_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.append(_parent_dir)

if not __package__:
    __package__ = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    if getattr(sys, 'frozen', False):
        __package__ = 'bot'  # Workaround for incorrect package name in frozen exe.
    __import__(__package__)


def main():
    # Imports are postponed up here due to late package setup above.
    from .service import Service
    from .utils import getopt, setup_logging

    target = getopt('target')
    service = getopt('service')
    debug = getopt('debug', 'DEBUG')

    setup_logging(service, debug)

    getopt('server', 'SERVER_API_URL')
    getopt('secret', 'SPIDER_SECRET_KEY')
    getopt('pollsec', 'POLL_SECONDS')
    getopt('delay', 'PAGE_DELAY')
    getopt('userpass', 'USERPASS')
    getopt('images', 'LOAD_IMAGES')
    getopt('newsid', 'NEWS_ID')
    getopt('maxnews', 'LIMIT_NEWS')

    if service:
        try:
            Service().run()
        except KeyboardInterrupt:
            print '^C'
    elif target:
        Service.action(target)


if __name__ == '__main__':
    # We import freeze_support only in main module as per multiprocessing documentation.
    from multiprocessing import freeze_support
    freeze_support()
    main()
