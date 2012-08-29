from gobotany import settings

def gobotany_specific_context(request):
    context_extras = {
        'in_production': settings.IN_PRODUCTION,
        }
    return context_extras
