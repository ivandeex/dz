import os
import sys
import json
import logging

from datetime import datetime, timedelta
from functools import wraps
from urllib2 import urlopen
from flask import current_app, request, make_response, Response
from time import time, sleep
from zlib import adler32
from urlparse import urljoin
from mimetypes import guess_type
from flask._compat import text_type
from werkzeug.datastructures import Headers
from werkzeug.wsgi import wrap_file

from ..utils import decode_userpass, result_as_list


DEFAULT_FORMAT = '%(asctime)s [%(levelname)s]: %(message)s'
BASIC_AUTH_PARAM = 'BASIC_AUTH_SIMPLE'


def result_as_choices(result):
    return [(x, x) for x in result_as_list(result)]


def setup_flask_logger(app, format=DEFAULT_FORMAT):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(format))
    app.logger.addHandler(handler)
    debug = app.config.get('DEBUG', False)
    app.logger.setLevel(logging.DEBUG if debug else logging.INFO)


def requires_basic_auth(func):
    # Based on flask snippet http://flask.pocoo.org/snippets/8/
    username, passwd = decode_userpass(current_app.config[BASIC_AUTH_PARAM])
    if username and passwd:
        @wraps(func)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if auth and auth.username == username and auth.password == passwd:
                return func(*args, **kwargs)
            return Response(
                'Please login with proper credentials', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return decorated
    return func


def nocache(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        resp = make_response(func(*args, **kwargs))
        resp.cache_control.no_cache = True
        return resp
    return decorated


def data_caching(name, value_func, timeout_sec=3600,
                 app_prefix=None, app=None, prefix_param='APP_PREFIX',
                 mem_cache={}, redis=None):
    stamp_key = '%s:updated' % name
    value_key = '%s:value' % name
    utc = datetime.utcnow()
    timeout_at = (utc + timedelta(timeout_sec)).strftime('%Y-%m-%d %H:%M:%S')
    if redis:
        assert app or app_prefix, 'Please provide app or app_prefix'
        app_prefix = app_prefix or app.config[prefix_param]
        cache_set = '%s:cache' % app_prefix
        value_stamp = redis.hget(cache_set, stamp_key)
        if value_stamp is not None and value_stamp < timeout_at:
            value = json.loads(redis.hget(cache_set, value_key))
        else:
            value = value_func()
            redis.hset(cache_set, stamp_key, utc.strftime('%Y-%m-%d %H:%M:%S'))
            redis.hset(cache_set, value_key, json.dumps(value))
    else:
        if value_key in mem_cache:
            value = mem_cache[value_key]
        else:
            value = value_func()
            mem_cache[value_key] = value
    return value


def probe_url(url, timeout=0):
    endtime = time() + timeout
    timeleft = 0.0001
    while timeleft > 0:
        try:
            urlopen(url).close()
            return True
        except IOError:
            pass
        timeleft = endtime - time()
        if timeleft > 0:
            sleep(min(timeleft, 0.2))
    return False


def send_file2(filename_or_fp, mimetype=None, as_attachment=False,
               attachment_filename=None, add_etags=True,
               cache_timeout=None, conditional=False):
    assert isinstance(filename_or_fp, basestring), \
        'Please provide file path as a string'
    filename = filename_or_fp

    if filename is not None and not os.path.isabs(filename):
        filename = os.path.join(current_app.root_path, filename)
    if mimetype is None and (filename or attachment_filename):
        mimetype = guess_type(filename or attachment_filename)[0]
    if mimetype is None:
        mimetype = 'application/octet-stream'

    headers = Headers()

    if as_attachment:
        if attachment_filename is None:
            attachment_filename = os.path.basename(filename)
        headers.add('Content-Disposition', 'attachment',
                    filename=attachment_filename)

    x_accel_mapping = getattr(current_app, 'x_accel_mapping', '')
    if not x_accel_mapping:
        x_accel_mapping = current_app.config.get('X_ACCEL_MAPPING', '')
    if not x_accel_mapping:
        x_accel_mapping = request.headers.get('x-flask-accel-mapping', '')
    if not x_accel_mapping:
        x_accel_mapping = request.headers.get('x-accel-mapping', '')

    assert isinstance(x_accel_mapping, (tuple, list, dict, basestring)), \
        'X_ACCEL_MAPPING must be tuple, list, dict, or str'
    if isinstance(x_accel_mapping, basestring):
        x_accel_mapping = [
            it.strip() for it in x_accel_mapping.split(',') if it.strip()]
    elif isinstance(x_accel_mapping, dict):
        x_accel_mapping = sorted(x_accel_mapping.items())
    elif isinstance(x_accel_mapping, tuple):
        x_accel_mapping = [x_accel_mapping]

    headers['Content-Length'] = os.path.getsize(filename)
    mtime = None
    data = None

    for map_item in x_accel_mapping:
        assert isinstance(map_item, (basestring, tuple)), \
            'X_ACCEL_MAPPING items must be 2-tuples or strings'
        if isinstance(map_item, basestring):
            map_path, map_loc = map_item.split('=')
        else:
            map_path, map_loc = map_item

        if not os.path.isabs(map_path):
            map_path = os.path.join(current_app.root_path, map_path)
        if filename.startswith(map_path):
            file_loc = urljoin(map_loc, filename[len(map_path):])
            headers['X-Accel-Redirect'] = file_loc
            break
    else:
        if current_app.use_x_sendfile:
            headers['X-Sendfile'] = filename
        else:
            fp = open(filename, 'rb')
            mtime = os.path.getmtime(filename)
            data = wrap_file(request.environ, fp)

    rv = current_app.response_class(data, mimetype=mimetype, headers=headers,
                                    direct_passthrough=True)
    if mtime is not None:
        rv.last_modified = int(mtime)

    rv.cache_control.public = True
    if cache_timeout is None:
        cache_timeout = current_app.get_send_file_max_age(filename)
    if cache_timeout is not None:
        rv.cache_control.max_age = cache_timeout
        rv.expires = int(time() + cache_timeout)

    if add_etags and filename is not None:
        rv.set_etag('flask-%s-%s-%s' % (
            os.path.getmtime(filename),
            os.path.getsize(filename),
            adler32(
                filename.encode('utf-8') if isinstance(filename, text_type)
                else filename
            ) & 0xffffffff
        ))
        if conditional:
            rv = rv.make_conditional(request)
            # don't send x-sendfile for servers that ignore 304 for x-sendfile
            if rv.status_code == 304:
                rv.headers.pop('x-sendfile', None)
                rv.headers.pop('x-accel-redirect', None)
    return rv
