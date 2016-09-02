# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import re
import random
import time
import logging
from datetime import datetime
from dateutil.parser import parse as parse_datetime


logger = logging.getLogger('dvoznak')


class UnbufferedStreamWrapper(object):
    __setstate__ = None

    def __init__(self, stream):
        self.__stream = stream

    def write(self, data):
        self.__stream.write(data)
        self.__stream.flush()

    def __getattr__(self, attr):
        return getattr(self.__stream, attr)


def get_project_dir():
    return os.path.join(os.path.expanduser('~'), '.vanko')


def setup_logging(service):
    if service:
        log_dir = os.path.join(get_project_dir(), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, 'dvoznak.log')
        log_file = open(log_path, mode='w', buffering=1)

        os.dup2(log_file.fileno(), sys.stderr.fileno())
        os.dup2(log_file.fileno(), sys.stdout.fileno())
        sys.stdout = UnbufferedStreamWrapper(sys.stdout)

        stream = logging.StreamHandler(stream=log_file)
    else:
        stream = logging.StreamHandler(stream=sys.stderr)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    stream.setFormatter(formatter)
    stream.setLevel(logging.DEBUG)
    logger.addHandler(stream)
    logger.setLevel(logging.DEBUG)

    logging.getLogger('requests.packages.urllib3').setLevel(logging.WARN)


def getopt(optname, env=None):
    for arg in sys.argv:
        mo = re.match(r'^--%s(?:=(.*))?$' % optname, arg)
        if mo:
            val = mo.group(1) or ''
            if env:
                os.environ[env] = val
            return val
    return None


def first_text(sel, css):
    return (sel.css(css + ' ::text').extract_first() or '').strip()


def poll_sleep(end_time, poll_sec=10):
    time.sleep(min(poll_sec, max(end_time - time.time(), 0)))


def randsleep(delay):
    time.sleep(delay * random.uniform(0.5, 1.5))


_date_trans = [
    (r'(\d{1,2}:\d\d)\s?\D+$', r'\1'),
]


def extract_datetime(text):
    text = (text or '').strip().lower()
    orig = ''
    while orig != text:
        orig = text
        for src, dst in _date_trans:
            text = re.sub(src, dst, text)

    mo = re.match(r'^(\d\d\.\d\d)[.]\s+(\d\d:\d\d)$', text)
    if mo:
        year = datetime.now().year
        text = '{}.{} {}'.format(mo.group(1), year, mo.group(2))

    if text.strip():
        return parse_datetime(text.strip(), dayfirst=True)
