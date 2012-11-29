"""Template tags and filters for search"""

from django import template

import gobotany.dkey.models as dkey_models

register = template.Library()

@register.inclusion_tag('_search_text_info_from_flora.txt')
def search_text_info_from_flora(**kwargs):
    scientific_name = kwargs['scientific_name']

    dkey_pages = dkey_models.Page.objects.filter(title=scientific_name)
    dkey_page = dkey_pages[0] if dkey_pages else None

    return {
        'dkey_page': dkey_page
    }
