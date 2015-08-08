import os
import sys
import subprocess
import time
import random
import threading


def _infer_type(default, type):
    if type is None:
        for type in (bool, int, float, dict):
            if isinstance(default, type):
                break
        else:
            type = str
    if default is None:
        default = type()
    return default, type


def getenv(name, default=None, type=None):
    default, type = _infer_type(default, type)
    val = os.environ.get(name, default)
    if type == bool:
        val = int(val)
    return type(val)


def launch_file(path):
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'linux2':
        subprocess.call(['xdg-open', path])
    elif sys.platform == 'darwin':
        subprocess.call(['open', path])
    else:
        raise AssertionError('Unsupported platform: %s' % sys.platform)


def result_as_list(result):
    if result is None:
        return []
    elif isinstance(result, (list, tuple)):
        return list(result)
    elif hasattr(result, 'next') and callable(result.next):
        return list(result)
    else:
        return [result]


def randsleep(delay, min_factor=0.5, max_factor=1.5):
    factor = random.random() * (max_factor - min_factor) + min_factor
    delay = factor * delay
    time.sleep(delay)
    return delay


def safe_unlink(path):
    try:
        os.unlink(path)
    except Exception:
        pass


def delayed_unlink(path, delay=0):
    def _unlink_thread(path, delay):
        if delay > 0:
            time.sleep(delay)
        safe_unlink(path)
    if delay > 0:
        threading.Thread(target=_unlink_thread, args=(path, delay)).start()
    else:
        safe_unlink(path)
