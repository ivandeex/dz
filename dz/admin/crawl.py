from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from .common import DzModelAdmin


class DzCrawlTypeFilter(admin.BooleanFieldListFilter):
    def choices(self, changelist):
        # Translators: don't translate this, use translation from Django
        text_yes = force_text(_('Yes'))
        # Translators: don't translate this, use translation from Django
        text_no = force_text(_('No'))

        for choice in super(DzCrawlTypeFilter, self).choices(changelist):
            text = force_text(choice['display'])
            if text == text_yes:
                choice['display'] = force_text(_('manual crawl')).title()
            elif text == text_no:
                choice['display'] = force_text(_('auto crawl')).title()
            yield choice


class CrawlAdmin(DzModelAdmin):
    list_display = ['id', 'target', 'type_str', 'status',
                    'started', 'ended', 'count', 'host', 'pid']
    list_filter = [('manual', DzCrawlTypeFilter),
                   'target',
                   'status'
                   ]
    date_hierarchy = 'started'
    radio_fields = {'target': admin.HORIZONTAL}
    ordering = ['-id']

    def type_str(self, obj):
        return _('manual crawl') if obj.manual else _('auto crawl')
    type_str.short_description = _('crawl type')
    type_str.admin_order_field = 'manual'
