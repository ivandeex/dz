from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_safe, require_POST
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.utils.translation import ugettext_lazy as _
import django_tables2 as tables
from .actions import RowActionForm, CrawlActionForm
from .. import models, helpers

FILTER_QUERY_PREFIX = 'flt'


# The @require_safe decorator returns 405 if request is not of GET or HEAD type.
# It can go before @login_required, because if the latter decorator redirects
# to login view and back again, the last redirect is GET as required.
@require_safe
@login_required
def list_view(request, TableClass, FiltersClass, form_url,
              export_url=None, restricted=False, crawl_target=None):
    is_admin = helpers.user_is_admin(request)
    if restricted and not is_admin:
        return HttpResponseForbidden('Forbidden')

    Model = TableClass.Meta.model
    model_name = Model._meta.model_name
    qs_all = Model.objects.all()
    query_string = request.META['QUERY_STRING']

    if FiltersClass:
        filters = FiltersClass(request.GET, queryset=qs_all, prefix=FILTER_QUERY_PREFIX)
        queryset = filters.qs

        # Detect wether filters would really change queryset population:
        if model_name in ('news', 'tip'):
            qs_all = qs_all.filter(archived=False)
        sql_all = qs_all.query.get_compiler(qs_all.db).as_sql()
        sql_qs = queryset.query.get_compiler(queryset.db).as_sql()
        filters.is_effective = sql_all != sql_qs
    else:
        filters = None
        queryset = qs_all

    table = TableClass(queryset)
    table.on_request(request)  # hide selector/actions columns for non-admins
    tables.RequestConfig(request).configure(table)

    row_action_form = RowActionForm(
        initial={
            'model_name': model_name,
            'preserved_query': query_string,
        }
    )

    if crawl_target and is_admin:
        crawl_form = CrawlActionForm(
            initial={
                'model_name': model_name,
                'crawl_target': crawl_target,
                'preserved_query': query_string,
            }
        )
        # Translators: crawl label is one of "Crawl news now", "Crawl tips now"
        crawl_form.crawl_label = _('Crawl %s now' % crawl_target)
        if None:
            _('Crawl news now')
            _('Crawl tips now')
    else:
        crawl_form = None

    context = {
        'table': table,
        # wrap _meta because django templates prohibits underscored property names
        'model_name': model_name,
        'verbose_name_plural': Model._meta.verbose_name_plural,
        'top_nav_links': get_top_nav_links(request),
        'filters': filters,
        'form_url': 'dz:' + form_url,
        'export_url': 'dz:' + export_url if export_url else None,
        'crawl_form': crawl_form,
        'row_action_form': row_action_form,
        'preserved_query': query_string,
    }

    return render(request, 'dz/tables/list.html', context)


# The @require_POST decorator returns 405 for GET requests. It must go *after*
# @login_required because the latter decorator might redirect to login form and
# and back again. Having login form in response to POST would be confusing.
@login_required
@permission_required('dz.is_admin', raise_exception=True)
@require_POST
def crawl_action_view(request):
    crawl_form = CrawlActionForm(request.POST)
    if not crawl_form.is_valid():
        return HttpResponseBadRequest(crawl_form.errors.as_text(),
                                      content_type='text/plain')
    data = crawl_form.cleaned_data

    # add_manual_crawl() will validate crawl target
    status = models.Crawl.add_manual_crawl(data['crawl_target'])
    message = models.Crawl.get_status_message(status)
    level = messages.ERROR if status in ('refused',) else messages.INFO
    messages.add_message(request, level, message)

    return redirect(crawl_form.get_next_url())


@login_required
@permission_required('dz.is_admin', raise_exception=True)
@require_POST
def row_action_view(request):
    action_form = RowActionForm(request.POST)
    if not action_form.is_valid():
        return HttpResponseBadRequest(action_form.errors.as_text(),
                                      content_type='text/plain')
    data = action_form.cleaned_data

    # Perform actions
    try:
        count = 0
        ModelClass = getattr(models, data['model_name'].title())
        for record in ModelClass.objects.filter(pk__in=data['row_ids']):
            # Deleting records one by one to let signals emit.
            if data['action'] == 'delete':
                record.delete()
            else:
                pass  # reserved for future extensions...
            count += 1
        messages.info(request, _('%(count)d record(s) deleted.') % {'count': count})

    except Exception as err:
        messages.error(request, _('Error deleting records: %(err)r') % {'err': err})

    return redirect(action_form.get_next_url())


@login_required
def form_view(request, pk, form_class, next, admin_only):
    is_admin = request.user.has_perm('dz.is_admin')
    if (request.method == 'POST' or admin_only) and not is_admin:
        return HttpResponseForbidden('Not authorized')

    model_class = form_class._meta.model
    verbose_name = model_class._meta.verbose_name
    obj = get_object_or_404(model_class, pk=int(pk))

    next_url = reverse('dz:%s' % next)
    query_string = request.META['QUERY_STRING']
    action = ''
    if query_string:
        next_url += '?' + query_string
        action += '?' + query_string

    if request.method == 'POST':
        form = form_class(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            context = {'model_name': verbose_name.title(), 'pk': pk}
            messages.info(request, _('%(model_name)s #%(pk)s saved.') % context)
            return redirect(next_url)
    else:
        form = form_class(instance=obj)

    context = {
        'form': form,
        'action': action,
        'next_url': next_url,
        'verbose_name': verbose_name,
        'pk': pk,
        'is_admin': is_admin,
        'top_nav_links': get_top_nav_links(request),
    }
    return render(request, 'dz/tables/form.html', context)


def get_top_nav_links(request):
    allowed_models = [models.News, models.Tip]
    if request.user.has_perm('dz.is_admin'):
        allowed_models += [models.Crawl, models.User]
        if not settings.DZ_COMPAT:
            allowed_models.append(models.Schedule)

    top_nav_links = []
    for model in allowed_models:
        top_nav_links.append({
            'text': model._meta.verbose_name_plural.title(),
            'link': reverse('dz:%s-list' % model._meta.model_name),
            'name': model._meta.model_name,
        })

    if request.user.has_perm('constance.change_config'):
        top_nav_links.append({
            'text': _('Settings'),
            'link': reverse('admin:constance_config_changelist'),
            'name': 'settings',
        })

    return top_nav_links
