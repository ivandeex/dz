#!/usr/bin/env python
import os
import sys
import re
import logging

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.append(_parent_dir)
if not __package__:
    __package__ = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    __import__(__package__)


def getopt(optname, env=None):
    for arg in sys.argv:
        mo = re.match(r'^--%s(?:=(.*))?$' % optname, arg)
        if mo:
            val = mo.group(1) or ''
            if env:
                os.environ[env] = val
            return val
    return None


def main():
    from .service import Service
    from .news import NewsSpider
    from .tips import TipsSpider
    from vanko.scrapy import setup_stderr, run_spider

    logging.getLogger('requests.packages.urllib3').setLevel(logging.WARN)

    action = getopt('action')
    if action:
        spider_cls = dict(news=NewsSpider, tips=TipsSpider)[action]
        return run_spider(spider_cls, argv=True)

    userpass = getopt('userpass')
    if userpass or getopt('service') is not None:
        os.environ['USERPASS'] = userpass or ''
        setup_stderr(__name__, pid_in_name=False)
        return Service().run()


if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    main()
