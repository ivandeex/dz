from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
import django_tables2 as tables
from .. import models, helpers


@login_required
def list_view(request, Table, crawl_target=None):
    Model = Table.Meta.model
    table = Table(Model.objects.all())
    tables.RequestConfig(request).configure(table)

    allowed_models = [models.News, models.Tip]
    if request.user.dz_user.is_admin:
        allowed_models += [models.Crawl, models.User]
        if not settings.DZ_COMPAT:
            allowed_models.append(models.Schedule)
    top_nav_links = [(m._meta.verbose_name_plural.title(),
                      reverse('dz:%s-list' % m._meta.model_name))
                     for m in allowed_models]

    if helpers.user_is_admin(request):
        # Translators: crawl label is one of "Crawl news now", "Crawl tips now"
        crawl_label = _('Crawl %s now' % crawl_target)
        if None:
            _('Crawl news now')
            _('Crawl tips now')
    else:
        crawl_target = crawl_label = None

    context = {
        'table': table,
        # wrap _meta because django templates prohibits underscored property names
        'model_name': Model._meta.model_name,
        'verbose_name_plural': Model._meta.verbose_name_plural,
        'top_nav_links': top_nav_links,
        'crawl_target': crawl_target,
        'crawl_label': crawl_label,
        'preserved_query': request.META['QUERY_STRING'],
    }

    return render(request, 'dz/tables/list.html', context)


@login_required
def crawl_action_view(request):
    model_name = request.POST.get('model_name')
    crawl_target = request.POST.get('crawl_target')
    preserved_query = request.POST.get('preserved_query')

    if not (helpers.user_is_admin(request) and
            model_name in ('news', 'tip') and
            # crawl_target in models.Crawl.CRAWL_TARGETS and
            request.method == 'POST'):
        return HttpResponseForbidden()

    status = models.Crawl.add_manual_crawl(crawl_target)
    message = models.Crawl.get_status_message(status)
    level = messages.ERROR if status in ('refused',) else messages.INFO
    messages.add_message(request, level, message)

    back_url = reverse('dz:%s-list' % model_name)
    if preserved_query:
        back_url += '?' + preserved_query
    return HttpResponseRedirect(back_url)
