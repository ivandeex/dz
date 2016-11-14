from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.conf.urls import url
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from import_export.admin import ExportMixin
from import_export.formats import base_formats
from import_export.resources import ModelResource
from .. import models


class DzSelectFieldListFilter(admin.AllValuesFieldListFilter):

    def __init__(self, *args, **kwargs):
        if settings.DZ_SKIN == 'plus':
            self.template = 'admin/dz-plus/list_filter.html'
        super(DzSelectFieldListFilter, self).__init__(*args, **kwargs)


class DzArchivedListFilter(admin.SimpleListFilter):
    title = _('archive (filter)')
    parameter_name = 'arch'

    def lookups(self, request, model_admin):
        return [
            ('-', _('All')),        # The "All" choice is not default (None)
            ('a', _('Archived')),
            ('f', _('Fresh')),
        ]

    def choices(self, changelist):
        choices = super(DzArchivedListFilter, self).choices(changelist)
        return list(choices)[1:]   # Skip the All (None) choice

    def queryset(self, request, queryset):
        if self.value() is None or self.value() == 'f':
            return queryset.filter(archived=False)  # Filter by "fresh" if default (None)
        if self.value() == 'a':
            return queryset.filter(archived=True)


class DzModelAdmin(admin.ModelAdmin):
    list_per_page = 50
    # actions = None
    can_export = False

    crawl_action = None

    def user_can_crawl(self, auth_user):
        return False

    def user_is_readonly(self, auth_user):
        return False

    def user_can_follow_links(self, auth_user):
        return False

    def get_list_display_links(self, request, list_display):
        if self.user_is_readonly(request.user):
            return None
        return super(DzModelAdmin, self).get_list_display_links(request, list_display)

    def get_readonly_fields(self, request, obj=None):
        '''
        Django does not support read-only model permissions out of the box.
        We override standard get_readonly_fields() to simulate read-only views.
        Overridden method will simply return all fields from get_fields().
        Since get_fields() will call back to get_readonly_fields() we use the
        `get_readonly_fields__is_running` instance flag to avoid infinite recursion.
        '''
        if self.get_readonly_fields__is_running:
            # avoid infinite recursion
            return super(DzModelAdmin, self).get_readonly_fields(request, obj)

        if not self.user_is_readonly(request.user):
            # user is not read-only - just normal behaviour
            return super(DzModelAdmin, self).get_readonly_fields(request, obj)

        try:
            self.get_readonly_fields__is_running = True
            return self.get_fields(request, obj)
        finally:
            self.get_readonly_fields__is_running = False
    get_readonly_fields__is_running = False

    def changelist_view(self, request, extra_context=None):
        # FIXME: request.current_app is not needed anymore
        # request.current_app = self.admin_site.name

        # Many field rendering methods in derived classes require `request`,
        # for example to check requesting user permissions or to render
        # template partials, but django does not provide request to them.
        # As a workararound, here we save a reference to request object
        # on the admin view instance.
        self._request = request

        # We change template name lazily here, not in the class constructor
        # because of unit tests, which use to change skins on the fly.
        skin = settings.DZ_SKIN
        if skin in ('plus', 'grappelli', 'bootstrap'):
            self.change_list_template = 'admin/dz-%s/change_list.html' % skin

        template_response = super(DzModelAdmin, self).changelist_view(request, extra_context)
        # FIXME: explain when context_data can be missing
        if hasattr(template_response, 'context_data'):
            template_response.context_data.update({
                'title': _(self.opts.verbose_name_plural.title()),  # override title
                'can_crawl': self.user_can_crawl(request.user),
                'can_export': self.can_export,
                'can_follow_links': self.user_can_follow_links(request.user),
                'server_time': timezone.now(),

                # Language selector will use HTTP_REFERRER or "redirect_to" to determine
                # the URL to internationalize. We might disable HTTP_REFERRER for users
                # without link-clicking permission, so we set the fallback here.
                'redirect_to': request.get_full_path(),

                # grappelli does not provide model name class on the body element,
                # so we do it ourselves.
                'model_name': self.model._meta.model_name,
            })
        return template_response


class DzSimpleCrawlModelAdmin(DzModelAdmin):
    formats = [base_formats.XLSX]

    def get_urls(self):
        urls = super(DzSimpleCrawlModelAdmin, self).get_urls()
        wrap = self.admin_site.admin_view
        rev_fmt = self.opts.app_label, self.opts.model_name
        crawl_url = url(r'^crawl/$', wrap(self.crawl_view), name='%s_%s_crawl' % rev_fmt)
        return [crawl_url] + urls

    def crawl_view(self, request, extra_context=None):
        if self.crawl_action and self.user_can_crawl(request.user):
            status = models.Crawl.add_manual_crawl(self.crawl_action)
            message = models.Crawl.get_status_message(status)
            self.message_user(request, message)

        # Restore query string from original request.
        # Alas, Django does not provide a simple method to do that.
        rev_fmt = (self.opts.app_label, self.opts.model_name)
        url = reverse('admin:%s_%s_changelist' % rev_fmt, current_app=self.admin_site.name)
        preserved_filters = self.get_preserved_filters(request)
        filter_kwargs = dict(preserved_filters=preserved_filters, opts=self.opts)
        return_url = add_preserved_filters(filter_kwargs, url)
        return HttpResponseRedirect(return_url)


class DzCrawlModelAdmin(ExportMixin, DzSimpleCrawlModelAdmin):
    can_export = True


class DzExportResource(ModelResource):
    @classmethod
    def field_from_django_field(cls, field_name, django_field, readonly):
        '''
        Replace default field names by localized verbose column names.
        '''
        field = super(DzExportResource, cls)\
            .field_from_django_field(field_name, django_field, readonly)
        field.column_name = django_field.verbose_name
        return field
