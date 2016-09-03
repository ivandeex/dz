from django.template.response import TemplateResponse
from . import models


def index(request):
    usernames = models.User.objects.order_by('username').values('username')
    context = {
        'csv_usernames': ', '.join(x['username'] for x in usernames),
        'server_name': request.get_host(),
    }
    return TemplateResponse(request, 'dz/welcome.html', context)
