from django.utils.translation import ugettext_lazy as _


ARCHIVED_CHOICES = [
    ('archived', _('Archived')),
    ('fresh', _('Fresh')),
]


def as_choices(seq):
    return [(x, x) for x in seq]


def cut_str(text, length):
    text = text or ''
    if len(text) > length:
        text = text[:length] + '...'
    return text
