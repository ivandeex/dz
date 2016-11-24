from django.shortcuts import render, redirect
from django.conf import settings


def index(request):
    if settings.DEBUG:
        return render(request, 'dz/welcome.html')
    else:
        return redirect('dz:news-list')
