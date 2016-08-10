from django.http import HttpResponse
# from django.shortcuts import render
from .models import User


def index(request):
    usernames = User.objects.order_by('username').values('username')
    return HttpResponse(
        '<html><body><p>Hello %s! Welcome to %s!</p></body></html>'
        % (','.join(x['username'] for x in usernames), request.get_host()))
