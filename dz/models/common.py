from django.utils.translation import ugettext_lazy as _
from django.db.models import CharField, TextField
from django.db.models.functions import Length, Substr, Concat
from django.db.models import Case, When, Value


ARCHIVED_CHOICES = [
    # TODO: make boolean
    ('archived', _('Archived')),
    ('fresh', _('Fresh')),
]

TYPE_CHOICES = [
    # TODO make boolean, name 'manual'
    ('manual', _('manual crawl')),
    ('auto', _('auto crawl')),
]

ACTION_CHOICES = [
    ('news', _('news crawl')),
    ('tips', _('tips crawl')),
]

CharField.register_lookup(Length, 'length')
TextField.register_lookup(Length, 'length')


def CutStr(field, length):
    when = {('%s__length__gt' % field): length, 'then': Value('...')}
    return Concat(Substr(field, 1, length),
                  Case(When(**when), default_value=Value('')),
                  output_field=CharField(max_length=length+3))
