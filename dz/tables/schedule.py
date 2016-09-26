from .common import DzTable, list_view
from .. import models


class ScheduleTable(DzTable):
    class Meta:
        model = models.Schedule
        fields = ('time', 'target')
        order_by = 'time'


def schedule_list_view(request):
    return list_view(request, ScheduleTable)
