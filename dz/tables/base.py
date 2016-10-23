import django_tables2 as tables
from .. import helpers


class AdminOnlyColumnMixin(object):
    pass


class RowSelectorColumn(tables.CheckBoxColumn, AdminOnlyColumnMixin):
    def __init__(self, *args, **kwargs):
        super(RowSelectorColumn, self).__init__(
            empty_values=(),
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

    # HACK:
    # Selector and actions columns must be hidden if user is not admin.
    # We need a `request` object to find out user permissions, but `Table`
    # doesn't provide a trigger. We use the fact that the `render_table` tag
    # sets `table.context` before rendering, and hook on the context setter.
    def _set_context(self, value):
        self._context = value
        self._on_request(self._context['request'])

    def _get_context(self):
        return self._context

    def _del_context(self):
        del self._context

    context = property(_get_context, _set_context, _del_context)

    # This hook triggers on a new request. It hides selector
    # and actions columns if requesting user is not admin.
    def _on_request(self, request):
        is_admin = helpers.user_is_admin(request)
        for column in self.base_columns.values():
            if isinstance(column, AdminOnlyColumnMixin):
                # We are safe to directly modify column properties, because
                # Table constructor creates their local copies on the table.
                column.visible = is_admin
