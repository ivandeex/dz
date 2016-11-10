import os
import time
import threading
from urlparse import urljoin
from StringIO import StringIO
from datetime import datetime
from xlsxwriter import Workbook
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_safe
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils.safestring import SafeData
from django.utils.encoding import force_text
from django.utils.html import strip_tags
from django_tables2 import RequestConfig
from ..templatetags.dz_extras import strip_cut_tags
from .base import AdminOnlyColumnMixin
from .views import FILTER_QUERY_PREFIX


@require_safe
@login_required
def export_view(request, TableClass, FiltersClass):
    Model = TableClass.Meta.model
    filters = FiltersClass(request.GET, Model.objects.all(), prefix=FILTER_QUERY_PREFIX)
    table = TableClass(filters.qs)
    table.on_request(request)  # hide selector/actions columns for non-admins
    RequestConfig(request).configure(table)

    mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    filename = '%(name)s_%(stamp)s.xlsx' % {
        'name': Model._meta.model_name,
        'stamp': datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    }

    if settings.NGINX_SENDFILE_URL and settings.NGINX_SENDFILE_ROOT:
        if not os.path.exists(settings.NGINX_SENDFILE_ROOT):
            os.mkdir(settings.NGINX_SENDFILE_ROOT)
        filepath = os.path.join(settings.NGINX_SENDFILE_ROOT, filename)
        output = open(filepath, 'w')
    else:
        filepath = None
        output = StringIO()

    book = Workbook(output, {'constant_memory': True})
    fmt_head = book.add_format(dict(
        bold=1, align='center', left=1, right=1, top=2, bottom=2))
    fmt_left = book.add_format(dict(
        align='left', border=1, valign='top'))
    fmt_wrap = book.add_format(dict(
        align='left', text_wrap=1, border=1, valign='top'))

    sheet = book.add_worksheet()
    context = RequestContext(request, {})
    context.update({'table': table})
    table.context = context

    col = -1
    for column in table.columns:
        if isinstance(column.column, AdminOnlyColumnMixin):
            continue
        col += 1
        sheet.write_string(0, col, column.header.title(), fmt_head)

    row = 0
    for table_row in table.rows:
        row += 1
        col = -1
        for column, cell in table_row.items():
            if isinstance(column.column, AdminOnlyColumnMixin):
                continue
            col += 1
            if isinstance(cell, SafeData):
                cell = force_text(cell).replace('&hellip;', '...')
                cell = strip_cut_tags(strip_tags(cell)).strip()
            else:
                cell = force_text(cell)
            fmt = fmt_wrap if '\n' in cell else fmt_left
            sheet.write_string(row, col, cell, fmt)

    del table.context
    context.pop()
    book.close()

    if filepath:
        def _unlink_later(filepath):
            time.sleep(3)  # delete in 3 seconds
            os.unlink(filepath)
        threading.Thread(target=_unlink_later, args=(filepath,)).start()

        output.close()
        response = HttpResponse(content_type=mimetype)
        response['X-Accel-Redirect'] = urljoin(settings.NGINX_SENDFILE_URL, filename)
    else:
        output.seek(0)
        response = HttpResponse(output.read(), content_type=mimetype)
        output.close()
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response
