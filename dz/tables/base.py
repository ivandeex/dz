import django_tables2 as tables
from django_tables2.tables import DeclarativeColumnsMetaclass
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


class FixColumnsMetaclass(DeclarativeColumnsMetaclass):
    '''
    DeclarativeColumnsMetaclass set column headers of Table's base_columns
    at the time class is instantiated. This is wrong because does not take
    into account current request locale.
    This metaclass resets verbose names to None, so that they are correctly
    retireved from queryset by bound columns with correct locale.
    Also we add row_selector and row_actions columns.
    '''
    def __new__(mcs, name, bases, attrs):
        # prepend two default columns
        attrs['row_selector'] = RowSelectorColumn()
        attrs['row_actions'] = RowActionsColumn()

        # make default columns the first
        Meta = attrs.get('Meta', None)
        if hasattr(Meta, 'fields') and 'row_selector' not in Meta.fields:
            Meta.fields = ('row_selector', 'row_actions') + tuple(Meta.fields)
        if hasattr(Meta, 'sequence') and 'row_selector' not in Meta.sequence:
            Meta.sequence = ('row_selector', 'row_actions') + tuple(Meta.sequence)

        cls = super(FixColumnsMetaclass, mcs).__new__(mcs, name, bases, attrs)

        # remove column headers derived with incorrect locale
        for field, column in cls.base_columns.items():
            if not column._explicit and column.verbose_name is not None:
                column.verbose_name = None

        return cls


TableFixColumns = FixColumnsMetaclass(str('TableFixColumns'), (tables.Table,), {})


class DzTable(TableFixColumns):
    def __init__(self, *args, **kwargs):
        super(DzTable, self).__init__(*args, **kwargs)

        # Force title-cased headers on bound columns
        for bound_column in self.columns.all():
            orig_header = bound_column.header
            bound_column.column.verbose_name = title(orig_header)
