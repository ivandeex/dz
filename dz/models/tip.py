from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from .common import CutStr


@python_2_unicode_compatible
class Tip(models.Model):
    id = models.IntegerField(_('tip id'), db_column='pk', primary_key=True)
    league = models.CharField(_('league'), max_length=40, db_index=True)
    parties = models.CharField(_('parties'), max_length=150, db_index=True)
    title = models.CharField(_('tip title'), max_length=60)
    # Translators: Betting (Kladionica)
    betting = models.CharField(_('betting'), max_length=32)
    # Translators: Coeff. (Koeficijent)
    rate = models.CharField(_('tip rate'), max_length=6)
    minrate = models.CharField(_('minimum tip rate'), max_length=6)
    # Translators: Result (Rezultat)
    result = models.CharField(_('tip result'), max_length=15)
    # Translators: Earnings Due (Zarada)
    earnings = models.CharField(_('earnings'), max_length=8)
    # Translators: Spread (Is. Margina)
    spread = models.CharField(_('spread'), max_length=8)
    # Translators: Stake (Ulog)
    stake = models.CharField(_('stake'), max_length=8)
    # Translators: Success (Uspje\u0161nost)
    success = models.CharField(_('tip success'), max_length=12, null=True)
    tipster = models.CharField(_('tipster'), max_length=12, db_index=True)
    # Translators: Published (Objavleno)
    published = models.DateTimeField(_('published'), null=True, db_index=True)
    updated = models.DateTimeField(_('updated'))
    crawled = models.DateTimeField(_('fetched'))
    link = models.URLField(_('tip link'))
    archived = models.BooleanField(_('archived'))

    # large text fields
    text = models.TextField('tip text', null=True)

    def __str__(self):
        return u'{} ({})'.format(self.tip, self.id)

    class Meta:
        verbose_name = _('tip')
        verbose_name_plural = _('tips')
        index_together = [
            ['published', 'archived']
        ]
        permissions = [
            ('crawl_tips', _('Can crawl tips')),
            ('view_tips', _('Can only view tips')),
        ]

    class Manager(models.Manager):
        use_for_related_fields = True

        def get_queryset(self, *args, **kw):
            qs = super(Tip.Manager, self).get_queryset(*args, **kw)
            qs = qs.defer('text').annotate(text_cut=CutStr('text', 80))
            return qs

    objects = Manager()
