import django_tables2 as tables
from django_tables2.templatetags.django_tables2 import title


class RowSelectorColumn(tables.CheckBoxColumn):
    def __init__(self, *args, **kwargs):
        super(RowSelectorColumn, self).__init__(
            empty_values=(),
            *args, **kwargs
        )


class RowActionsColumn(tables.TemplateColumn):
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

    def __init__(self, *args, **kwargs):
        super(DzTable, self).__init__(*args, **kwargs)

        # Force title-cased headers on bound columns
        for bound_column in self.columns.all():
            orig_header = bound_column.header
            bound_column.column.verbose_name = title(orig_header)

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
