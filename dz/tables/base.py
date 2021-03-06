import functools
import operator
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.core.cache import cache
from django.conf import settings
import django_tables2 as tables
import django_filters as filters
from .. import helpers


class AdminOnlyColumnMixin(object):
    pass


class RowSelectorColumn(tables.CheckBoxColumn, AdminOnlyColumnMixin):
    def __init__(self, *args, **kwargs):
        super(RowSelectorColumn, self).__init__(
            empty_values=(),
            checked=None,
            accessor='pk',
            attrs={'td__input': {'class': 'dz-row-selector'}},
            *args, **kwargs
        )


class RowActionsColumn(tables.TemplateColumn, AdminOnlyColumnMixin):
    def __init__(self, *args, **kwargs):
        super(RowActionsColumn, self).__init__(
            verbose_name='',
            orderable=False,
            empty_values=(),
            template_name='dz/tables/_row-actions.html',
            *args, **kwargs
        )


class DzTable(tables.Table):

    row_selector = RowSelectorColumn()
    row_actions = RowActionsColumn()

    class Meta:
        fields = ('row_selector', 'row_actions')

    def get_column_class_names(self, classes_set, bound_column):
        '''
        Returns a set of HTML class names for cells (both td and th) of a **bound column**
        in this table. By default this is class names from attributes plus the *plain*
        bound column's name. This results in problems. For example, column named `success`
        takes the bootstrap's success color. As a solution, we prepend 'col-' to the name.
        Please note that super() is *not* chanined *intentionally*.
        '''
        classes_set.add('col-' + bound_column.name)
        return classes_set

    # This hook should be called once with a new request.
    # It hides selector and actions columns if requesting user is not admin.
    def on_request(self, request):
        self.is_admin = helpers.user_is_admin(request)
        for column in self.base_columns.values():
            if isinstance(column, AdminOnlyColumnMixin):
                # We are safe to directly modify column properties, because
                # Table constructor creates their local copies on the table.
                column.visible = self.is_admin


class DzArchivedFilter(filters.ChoiceFilter):
    CHOICES = (
        ('fresh', _('Fresh')),
        ('archived', _('Archived')),
        ('all', _('All')),        # The "All" choice is not default
    )

    def __init__(self, *args, **user_kwargs):
        kwargs = {
            'name': 'archived',
            'choices': self.CHOICES,
            'label': _('archive (filter)').title(),
        }
        kwargs.update(user_kwargs)
        super(DzArchivedFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        # When filter is not set, we get `value` as an empty string,
        # which is equivalent to 'fresh'.
        if value in ('', 'fresh', 'archived'):
            qs = qs.filter(archived=(value == 'archived'))
        return qs


class AllValuesCachingFilter(filters.ChoiceFilter):
    empty_label = _('All')
    cache_timeout = settings.CHOICES_CACHE_TIMEOUT

    def __init__(self, *args, **kwargs):
        self.empty_label = kwargs.pop('empty_label', type(self).empty_label)
        self.cache_timeout = kwargs.pop('cache_timeout', type(self).cache_timeout)
        super(AllValuesCachingFilter, self).__init__(*args, **kwargs)

    def _make_choices(self):
        qs = self.model._default_manager.distinct().order_by(self.name)
        choices = [(val, val) for val in qs.values_list(self.name, flat=True)
                   if val not in (None, '')]
        if self.empty_label is not None:
            choices.insert(0, (None, self.empty_label))
        return choices

    @property
    def field(self):
        cache_key = 'filter-choices::%(app)s:%(model)s.%(field)s' % {
            'app': 'dz', 'model': self.model._meta.model_name, 'field': self.name
        }
        choices = cache.get_or_set(cache_key, self._make_choices, self.cache_timeout)
        self.extra['choices'] = choices
        return super(AllValuesCachingFilter, self).field


class FilterSetWithSearch(filters.FilterSet):
    def filter_search(self, queryset, name, value):
        value = value.strip()
        if value:
            fields = name if isinstance(name, (list, tuple)) else name.split()
            for term in value.split():
                or_queries = [Q(**{'%s__icontains' % field: term}) for field in fields]
                queryset = queryset.filter(functools.reduce(operator.or_, or_queries))
        return queryset
