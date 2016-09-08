#!/usr/bin/env python
import os
import sys


_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.append(_parent_dir)
if not __package__:
    __package__ = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    __import__(__package__)


def main():
    from .service import Service
    from .utils import getopt, setup_logging

    target = getopt('target')
    service = getopt('service')
    debug = getopt('debug', 'DEBUG')

    setup_logging(service, debug)

    getopt('server', 'WEB_SERVER')
    getopt('secret', 'SECRET_KEY')
    getopt('pollsec', 'POLL_SECONDS')
    getopt('delay', 'PAGE_DELAY')
    getopt('userpass', 'USERPASS')
    getopt('images', 'LOAD_IMAGES')
    getopt('newsid', 'NEWS_ID')

    if service:
        Service().run()
    elif target:
        Service.action(target)


if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    main()
