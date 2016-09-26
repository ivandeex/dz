from django.conf import settings


def dz_skin(request):
    return {'dz_skin': settings.DZ_SKIN}


def dz_compat(request):
    return {'dz_compat': settings.DZ_COMPAT}
