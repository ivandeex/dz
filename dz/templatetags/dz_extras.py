import re
from django import template

register = template.Library()


@register.filter
def strip_cut_tags(text):
    """Strip partial tags that might been left after cutting"""
    return re.sub(r'<[^>]+?(\.*)$', ' \1', text)


@register.filter
def msg_tag_to_bs_class(tag):
    """
    Converts django message tag to bootstrap 3 alert element class
    """
    if tag == 'error':
        return 'danger'
    if not tag:
        return 'info'
    return tag
