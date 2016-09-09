import re
from django import template

register = template.Library()


@register.filter
def strip_cut_tags(text):
    """Strip partial tags that might been left after cutting"""
    return re.sub(r'<[^>]+?(\.*)$', ' \1', text)
