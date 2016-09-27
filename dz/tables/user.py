from .common import DzTable, list_view
from .. import models


class UserTable(DzTable):
    class Meta:
        model = models.User
        fields = ('username', 'is_admin', 'can_follow')
        order_by = 'username'


def user_list_view(request):
    return list_view(request, UserTable)
