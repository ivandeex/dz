from django.conf import settings


def dz_skin(request):
    return {'dz_skin': settings.DZ_SKIN}
