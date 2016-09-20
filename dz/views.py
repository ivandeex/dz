from django.template.response import TemplateResponse


def index(request):
    return TemplateResponse(request, 'dz/welcome.html', {})
