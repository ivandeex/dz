import re
from django import template

register = template.Library()


@register.filter
def strip_cut_tags(text):
    '''
    Strips partial tags that might have left at the end of cut html string
    after the `striptags` filter.
    '''
    return re.sub(r'<[^>]+?(\.*)$', ' \1', text)


@register.filter
def message_tag_to_bootstrap_class(tag):
    '''
    Maps django message tag into bootstrap3 alert element class.
    '''
    if tag == 'error':
        return 'danger'
    if not tag:
        return 'info'
    return tag
