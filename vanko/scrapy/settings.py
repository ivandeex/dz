import os
import re
from scrapy.settings import Settings, SETTINGS_PRIORITIES
from .defaults import ACTION_PARAMETER, DEFAULT_ACTION
from .helpers import spider_data_dir
from ..utils.misc import _infer_type


class _LazyTemplateKeys(object):
    lazy_keys = {
        'project_dir': lambda spider: spider_data_dir(),
        'spider_dir': lambda spider: spider_data_dir(spider),
        'files_dir': lambda spider: spider_data_dir(spider, 'files'),
        'images_dir': lambda spider: spider_data_dir(spider, 'images'),
        'mirror_dir': lambda spider: spider_data_dir(spider, 'mirror'),
    }

    def __init__(self, spider_name):
        self.spider = spider_name
        self.cache = {'spider': self.spider}

    def __getitem__(self, key):
        return (key in self.cache and self.cache[key] or
                self.cache.setdefault(key, self.lazy_keys[key](self.spider)))

    def __setitem__(self, key, val):
        self.cache[key] = val


class CustomSettings(object):

    LOG_LEVEL_str = 'INFO'
    LOG_FORMAT_str = ('%(asctime)s.%(msecs)03d (%(process)d) [%(name)s] '
                      '%(levelname)s: %(message)s')

    STATS_DUMP_bool = 0
    AUTOTHROTTLE_ENABLED_bool = 0
    AUTOTHROTTLE_DEBUG_bool = 0

    DEBUG_bool = 0
    ACTION_str = DEFAULT_ACTION
    HEROKU_bool = 0
    STORAGE_str = 'redis'

    EXTENSIONS_dict = {
        'vanko.scrapy.FastExit': 0,
        'vanko.scrapy.RestartOn': 0,
        'vanko.scrapy.ShowIP': 0,
    }

    DOWNLOAD_HANDLERS_dict = {
        's3': None,  # fixes boto error "cannot read instance data"
    }

    DOWNLOADER_MIDDLEWARES_dict = {
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
        'vanko.scrapy.RedisUserAgentMiddleware': 400,
    }

    @classmethod
    def register(cls, name=None, default=None, type=None, **kwargs):
        if name is None and default is None and type is None:
            name = kwargs
        assert name is not None, 'Please provide a parameter'
        if isinstance(name, dict):
            assert name, 'Empty argument list!'
            for param_name, param_default in name.items():
                param_type = None
                mo = re.match('^(.*)_(tmpl.*)$', param_name)
                if mo:
                    param_name, param_type = mo.group(1, 2)
                cls.register(param_name, param_default, param_type)
        else:
            assert not kwargs, 'Dangling keywords!'
            default, type = _infer_type(default, type)
            if type == str and '%(spider)s' in (default or ''):
                type = 'tmpl'
            type_str = getattr(type, '__name__', str(type))
            attr = '%s_%s' % (name, type_str)
            val = default
            if type is dict:
                val = getattr(cls, attr, {})
                val.update(default)
            setattr(cls, attr, val)

    def __init__(self, spider_name='spider', base_settings=None,
                 priority='project'):
        attr_list = sorted(dir(self))
        self.base_settings = (base_settings or Settings()).copy()
        self.action = self.base_settings.get(ACTION_PARAMETER, DEFAULT_ACTION)
        if isinstance(priority, basestring):
            priority = SETTINGS_PRIORITIES[priority]
        self.priority = priority
        self.result_dict = {}
        self.template_keys = _LazyTemplateKeys(spider_name)

        for first_pass in (True, False):
            for attr_name in attr_list:
                self._process_attr(attr_name, first_pass=first_pass)

    def _process_attr(self, attr_name, first_pass):

        if not hasattr(self, attr_name):
            return

        mo = re.match(r'^([A-Z_]+?)_(any|str|tmpl|int|float|bool|dict)'
                      r'(?:_map_([a-z]+))?(?:_on_([a-z]+))?$',
                      attr_name)
        if not mo:
            return
        opt, opt_type, map_name, on_action = mo.groups()

        is_template_key = opt_type in ('str', 'int', 'bool')
        if first_pass != is_template_key:
            return
        if first_pass and on_action:
            return
        if on_action and on_action not in self.action.split(','):
            return

        if opt_type == 'dict':
            val = getattr(self, attr_name).copy()
            val.update(self.base_settings.getdict(opt))
        else:
            base = self.base_settings.attributes
            if opt in base and base[opt].priority >= self.priority:
                val = base[opt].value
            else:
                val = os.environ.get(opt, getattr(self, attr_name))

            try:
                if opt_type == 'str':
                    val = str(val)
                elif opt_type == 'tmpl':
                    val = re.sub(r'%{([\w_][\w\d_]*)}', r'%(\1)', str(val))
                    val = re.sub(r'%\[([\w_][\w\d_]*)\]', r'%(\1)', val)
                    try:
                        val = val % self.template_keys
                    except KeyError as err:
                        raise KeyError(
                            'formatter "%s" from option %s not found in: %s' %
                            (err, opt, ', '.join(sorted(self.template_keys))))
                elif opt_type == 'int':
                    val = int(val)
                elif opt_type == 'bool':
                    val = bool(int(val))
            except ValueError as err:
                raise ValueError('cannot convert option %s ("%s"): %s' %
                                 (opt, val, err))

            if map_name:
                class_map = getattr(self, map_name + '_map')
                if val in class_map:
                    val = class_map[val]
                elif re.match(r'^[a-z0-9_-]+$', val):
                    raise KeyError(
                        'mapping "%s" from option %s not found in: %s' %
                        (val, opt, ', '.join(sorted(class_map))))

        self.result_dict[opt] = val
        if is_template_key:
            self.template_keys[opt] = val

        return True

    def as_dict(self):
        return self.result_dict
