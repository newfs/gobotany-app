from gobotany import settings

def gobotany_specific_context(request):
    context_extras = {
        'in_production': settings.IN_PRODUCTION,
        }
    if settings.DEBUG_DOJO:
        context_extras['debug_dojo'] = True
    return context_extras
