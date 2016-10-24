from django.shortcuts import render, redirect
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from django.db.models import Model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_safe, require_POST
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.utils.translation import ugettext_lazy as _
import django_tables2 as tables
from .. import models, helpers


# The @require_safe decorator returns 405 if request is not of GET or HEAD type.
# It can go before @login_required, because if the latter decorator redirects
# to login view and back again, the last redirect is GET as required.
@require_safe
@login_required
def list_view(request, TableClass, restricted=False, crawl_target=None):
    is_admin = helpers.user_is_admin(request)
    if restricted and not is_admin:
        return HttpResponseForbidden('Forbidden')

    Model = TableClass.Meta.model
    table = TableClass(Model.objects.all())
    table.on_request(request)  # hide selector/actions columns for non-admins
    tables.RequestConfig(request).configure(table)

    allowed_models = [models.News, models.Tip]
    if is_admin:
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

    if is_admin:
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


# The @require_POST decorator returns 405 for GET requests. It must go *after*
# @login_required because the latter decorator might redirect to login form and
# and back again. Having login form in response to POST would be confusing.
@login_required
@permission_required('dz.is_admin', raise_exception=True)
@require_POST
def crawl_action_view(request):
    model_name = request.POST.get('model_name')
    if model_name not in ('news', 'tip'):
        return HttpResponseBadRequest('Bad model')

    # add_manual_crawl() will validate crawl target
    status = models.Crawl.add_manual_crawl(request.POST.get('crawl_target', ''))
    message = models.Crawl.get_status_message(status)
    level = messages.ERROR if status in ('refused',) else messages.INFO
    messages.add_message(request, level, message)

    back_url = reverse('dz:%s-list' % model_name)
    if request.POST.get('preserved_query'):
        back_url += '?' + request.POST['preserved_query']
    return redirect(back_url)


@login_required
@permission_required('dz.is_admin', raise_exception=True)
@require_POST
def row_action_view(request):
    # Validate post parameters
    try:
        stage = 'action'
        action = request.POST.get('action')
        assert action in ('delete',)

        stage = 'ids'
        row_ids = request.POST.get('row_ids')
        assert row_ids
        # Conversion to integer can raise a ValueError.
        row_ids = map(int, row_ids.split(','))

        stage = 'model'
        model_name = request.POST.get('model_name', '')
        # We use a generic title-case check instead of hardcoded list of allowed models:
        ModelClass = getattr(models, model_name.title())
        assert ModelClass and issubclass(ModelClass, Model)

        stage = 'url'
        # Invalid model name will raise NoReverseMatch exception.
        next_url = reverse('dz:%s-list' % model_name)
        if request.POST.get('preserved_query'):
            next_url += '?' + request.POST['preserved_query']
    except (AssertionError, ValueError, AttributeError, NoReverseMatch):
        return HttpResponseBadRequest('Bad request ' + stage)

    # Perform actions
    try:
        count = 0
        for pk in row_ids:
            # Deleting records one by one to let signals emit.
            try:
                obj = ModelClass.objects.get(pk=pk)
            except ModelClass.DoesNotExist:
                continue
            if action == 'delete':
                obj.delete()
            count += 1
        messages.info(request, _('%(count)d record(s) deleted.') % {'count': count})
    except Exception as err:
        messages.error(request, _('Error deleting records: %(err)r') % {'err': err})

    return redirect(next_url)
