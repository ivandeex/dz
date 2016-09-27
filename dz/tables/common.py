from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
import django_tables2 as tables
from django_tables2.tables import DeclarativeColumnsMetaclass
from django_tables2.templatetags.django_tables2 import title
from .. import models


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


@login_required
def list_view(request, Table):
    Model = Table.Meta.model
    table = Table(Model.objects.all())
    tables.RequestConfig(request).configure(table)

    allowed_models = [models.News, models.Tip]
    if request.user.dz_user.is_admin:
        allowed_models += [models.Crawl, models.User]
        if not settings.DZ_COMPAT:
            allowed_models.append(models.Schedule)
    top_nav_links = [(m._meta.verbose_name_plural.title(),
                      reverse('dz:%s-list' % m._meta.model_name))
                     for m in allowed_models]

    context = {
        'table': table,
        # wrap _meta because django templates prohibits underscored property names
        'model_name': Model._meta.model_name,
        'verbose_name_plural': Model._meta.verbose_name_plural,
        'top_nav_links': top_nav_links,
    }

    return render(request, 'dz/tables/list.html', context)
