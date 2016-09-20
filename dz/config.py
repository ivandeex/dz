from constance import config
from constance.signals import config_updated
from django.dispatch import receiver

# cache here, becouse every access of constance.config will query database
_config_cache = {}


@receiver(config_updated)
def _constance_updated(sender, updated_key, new_value, **kwargs):
    _config_cache[updated_key] = new_value


def spider_config(parameter):
    parameter = 'SPIDER_' + parameter
    if parameter not in _config_cache:
        _config_cache[parameter] = getattr(config, parameter)
    return _config_cache[parameter]
