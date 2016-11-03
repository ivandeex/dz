from django.utils.translation import ugettext_lazy as _
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
        is_admin = helpers.user_is_admin(request)
        for column in self.base_columns.values():
            if isinstance(column, AdminOnlyColumnMixin):
                # We are safe to directly modify column properties, because
                # Table constructor creates their local copies on the table.
                column.visible = is_admin


class DzArchivedFilter(filters.ChoiceFilter):
    CHOICES = (
        ('fresh', _('Fresh')),
        ('archived', _('Archived')),
        ('all', _('All')),        # The "All" choice is not default
    )

    def __init__(self, *args, **user_kwargs):
        kwargs = {
            'name':'archived',
            'choices': self.CHOICES,
            'label': _('archive (filter)'),
        }
        kwargs.update(user_kwargs)
        super(DzArchivedFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        # When filter is not set, we get `value` as an empty string,
        # which is equivalent to 'fresh'.
        if value in ('', 'fresh', 'archived'):
            qs = qs.filter(archived=(value == 'archived'))
        return qs
