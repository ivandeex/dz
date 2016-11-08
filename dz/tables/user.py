from django import forms
import django_filters as filters
from .base import DzTable
from .views import list_view
from .. import models


class UserTable(DzTable):
    class Meta:
        model = models.User
        order_by = 'username'

        fields = DzTable.Meta.fields + (
            'username', 'is_admin', 'can_follow'
        )


class UserFilters(filters.FilterSet):
    class Meta:
        model = models.User
        fields = ('is_admin', 'can_follow')


class UserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = '__all__'


def user_list_view(request):
    return list_view(request, UserTable, UserFilters, 'user-form',
                     restricted=True)
