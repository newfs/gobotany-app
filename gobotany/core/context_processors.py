from gobotany import settings


def dojo(request):
    context_extras = {}
    if settings.DEBUG_DOJO:
        context_extras['debug_dojo'] = True
    return context_extras
