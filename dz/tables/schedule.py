from django import forms
from .base import DzTable
from .views import list_view
from .. import models


class ScheduleTable(DzTable):
    class Meta:
        model = models.Schedule
        order_by = 'time'

        fields = DzTable.Meta.fields + (
            'time', 'target'
        )


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = models.Schedule
        fields = '__all__'


def schedule_list_view(request):
    return list_view(request, ScheduleTable, None, 'schedule-form',
                     restricted=True)
