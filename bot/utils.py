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


logger = logging.getLogger('dz')


class UnbufferedStreamWrapper(object):
    __setstate__ = None

    def __init__(self, stream):
        self.__stream = stream

    def write(self, data):
        self.__stream.write(data)
        self.__stream.flush()

    def __getattr__(self, attr):
        return getattr(self.__stream, attr)


def setup_logging(service, debug):
    stream = logging.StreamHandler(stream=sys.stderr)
    if service:
        log_name = 'dz.log'
        proj_dir = ''.join(['a', 'by', 'ss'])
        root_dirs = [os.path.expanduser('~'), '.' + proj_dir]
        if sys.platform == 'win32':
            root_dirs = ['C:\\', proj_dir]

        log_dir = os.path.join(*(root_dirs + ['logs']))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_path = os.path.join(log_dir, log_name)
        log_file = open(log_path, mode='w', buffering=1)

        if not debug:
            os.dup2(log_file.fileno(), sys.stderr.fileno())
            os.dup2(log_file.fileno(), sys.stdout.fileno())
            sys.stdout = UnbufferedStreamWrapper(sys.stdout)

        stream = logging.StreamHandler(stream=log_file)

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


def randsleep(delay):
    time.sleep(delay * random.uniform(0.5, 1.5))


def extract_datetime(text):
    text = (text or '').strip().lower()
    orig = ''
    _date_trans = [(r'(\d{1,2}:\d\d)\s?\D+$', r'\1')]
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
