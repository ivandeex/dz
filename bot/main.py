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

    action = getopt('action')
    service = getopt('service')

    setup_logging(service)

    getopt('server', 'WEB_SERVER')
    getopt('secret', 'SECRET_KEY')
    getopt('pollsec', 'POLL_SECONDS')
    getopt('userpass', 'USERPASS')
    getopt('images', 'LOAD_IMAGES')
    getopt('debug', 'DEBUG')

    if service:
        Service().run()
    elif action:
        Service.action(action)


if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    main()
