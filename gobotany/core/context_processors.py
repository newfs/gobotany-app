from gobotany import settings

def gobotany_specific_context(request):
    context_extras = {
        'in_production': settings.IN_PRODUCTION,
        'dev_features': settings.DEV_FEATURES,
        }
    return context_extras
