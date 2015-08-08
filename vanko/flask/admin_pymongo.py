import re
import sys
from flask_admin.contrib import pymongo as admin_pymongo
from flask_admin.model import filters as base_filters
from flask_admin.contrib.pymongo import filters as pymongo_filters
from flask_admin.base import expose

from .admin import ExcelExportViewMixin


def PyMongoFilter(base_type, operation):
    type_map = {str: '', unicode: '', bool: 'Boolean'}
    base_type = type_map.get(base_type,
                             getattr(base_type, '__name__', str(base_type)))
    if base_type.islower():
        base_type = base_type.title()

    op_map = {'==': 'Equal', '!=': 'NotEqual', '>': 'Greater', '<': 'Smaller'}
    operation = op_map.get(operation, operation)
    if operation.islower():
        operation = operation.title()

    filter_name = 'PyMongo%s%sFilter' % (base_type, operation)
    this_module = sys.modules[__name__]
    try:
        return getattr(this_module, filter_name)
    except AttributeError:
        pass

    if operation:
        pymongo_filter_name = 'PyMongoFilter%s' % operation
        try:
            PyMongoFilter = getattr(this_module, pymongo_filter_name)
        except AttributeError:
            BasePyMongoFilter = getattr(pymongo_filters, 'Filter' + operation)

            class PyMongoFilter(BasePyMongoFilter):
                def apply(self, query, value):
                    return super(PyMongoFilter, self).apply(query,
                                                            self.clean(value))

            setattr(this_module, pymongo_filter_name, PyMongoFilter)
    else:
        PyMongoFilter = pymongo_filters.BasePyMongoFilter

    if base_type in ('', 'str', 'Str'):
        parent_filters = (PyMongoFilter,)
    else:
        BaseFilter = getattr(base_filters, 'Base%sFilter' % base_type)
        parent_filters = (PyMongoFilter, BaseFilter)

    filter_class = type(filter_name, parent_filters, {})
    setattr(this_module, filter_name, filter_class)
    return filter_class


class PyMongoFilterGreater(pymongo_filters.FilterGreater):
    def apply(self, query, value):
        query.append({self.column: {'$gt': self.clean(value)}})
        return query


class PyMongoFilterSmaller(pymongo_filters.FilterSmaller):
    def apply(self, query, value):
        query.append({self.column: {'$lt': self.clean(value)}})
        return query


class PyMongoDateBetweenFilter(pymongo_filters.BasePyMongoFilter,
                               base_filters.BaseDateBetweenFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(PyMongoDateBetweenFilter, self).__init__(
            column, name, options, data_type=data_type or 'daterangepicker')

    def apply(self, query, value):
        start, end = self.clean(value)
        query.append({'$and': [{self.column: {'$gte': start}},
                               {self.column: {'$lte': end}}]})
        return query


class PyMongoDateStringEqualFilter(pymongo_filters.FilterEqual,
                                   base_filters.BaseDateFilter):
    def clean(self, value):
        value = super(PyMongoDateStringEqualFilter, self).clean(value)
        return value.strftime('%Y-%m-%d')

    def apply(self, query, value):
        query.append({self.column: self.clean(value)})
        return query


class PyMongoDateStringBetweenFilter(PyMongoDateBetweenFilter):
    def clean(self, value):
        start_end = super(PyMongoDateStringBetweenFilter, self).clean(value)
        return [x.strftime('%Y-%m-%d') for x in start_end]


class PyMongoModelView(admin_pymongo.ModelView, ExcelExportViewMixin):

    case_insensitive_search = False
    export_producer = None

    def _search(self, query, search_term):
        values = filter(None, search_term.split(' '))
        if not (values and self._search_fields):
            return query

        queries = []
        re_opts = re.I if self.case_insensitive_search else 0

        for value in values:
            term = admin_pymongo.tools.parse_like_term(value)
            stmt = [{field: re.compile(term, re_opts)}
                    for field in self._search_fields]
            queries.append(stmt[0] if len(stmt) == 1 else {'$or': stmt})

        queries = queries[0] if len(queries) == 1 else {'$and': queries}
        return {'$and': [query, queries]}

    @expose('/export/csv/')
    def export_csv(self, *args, **kwargs):
        if self.export_producer is None:
            return super(PyMongoModelView, self).export_csv(*args, **kwargs)
        return self.export_excel(
            producer=self.export_producer, *args, **kwargs)
