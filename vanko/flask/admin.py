import os
import re

from tempfile import gettempdir
from datetime import datetime

from wtforms.form import Form
from werkzeug import secure_filename
from jinja2 import Markup
from flask import redirect
from flask_admin.helpers import get_redirect_target
from flask_admin._compat import iteritems

from .utils import send_file2
from ..excel import produce_excel
from ..utils.misc import delayed_unlink


DEF_UNLINK_DELAY = 2.0
DEF_TEMP_DIR = os.path.join(gettempdir(), '.flask_admin')


class AppForm(Form):
    pass


class LinkFormatter(object):
    def __init__(self, text=None, field=None,
                 rel='nofollow', target='_blank', encoding='utf-8'):
        # flask_admin's csv export wants func.__name__
        self.__name__ = type(self).__name__
        self.text = text
        self.field = field
        self.rel = rel
        self.target = target
        self.encoding = encoding

    def __call__(self, view, context, model, name):
        if isinstance(model, dict):
            value = self.text or model[name]
            link = model.get(self.field or name, '')
        else:
            value = self.text or getattr(model, name)
            link = getattr(model, self.field or name, '')

        try:
            value = unicode(value)
        except UnicodeDecodeError:
            value = value.decode(self.encoding, 'replace')
        value = value.strip()

        if link and re.match(r'https?://', link):
            return Markup('<a href="{}" target="{}" rel="{}">{}</a>'
                          .format(link, self.target, self.rel, value))
        return value


class ExcelExportViewMixin(object):
    def export_excel(self, producer=None, tempdir=None, *args, **kwargs):
        # Macros in column_formatters are not supported.
        # Macros will have a function name 'inner'
        # This causes non-macro functions named 'inner' not work.
        for col, func in iteritems(self.column_formatters):
            if getattr(func, '__name__', '') == 'inner':
                raise NotImplementedError(
                    'Macros not implemented. Override with '
                    'column_formatters_export. Column: %s' % (col,)
                )

        # Grab parameters from URL
        view_args = self._get_list_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(view_args.sort)
        sort_column = None if sort_column is None else sort_column[0]

        count, data = self.get_list(0, sort_column, view_args.sort_desc,
                                    view_args.search, view_args.filters,
                                    page_size=self.export_max_rows)

        tempdir = tempdir or DEF_TEMP_DIR
        filename = '%s_%s' % (self.name,
                              datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        filepath = os.path.join(tempdir, filename)

        filepath = produce_excel(
            keys=list(range(count)), get_item=lambda db, table, key: data[key],
            producer=producer, filepath=filepath, title_case=True,
            fields=[col[0] for col in self._export_columns],
            format=getattr(self, 'column_format_excel', None))

        unlink_delay = getattr(self, 'unlink_delay', DEF_UNLINK_DELAY)
        delayed_unlink(filepath, unlink_delay)
        return send_file2(
            filepath, as_attachment=True,
            attachment_filename=secure_filename(os.path.basename(filepath)))

    def redirect_back(self, endpoint='.index_view'):
        return redirect(get_redirect_target() or self.get_url(endpoint))
