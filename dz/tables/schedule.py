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


def schedule_list_view(request):
    return list_view(request, ScheduleTable, restricted=True)
