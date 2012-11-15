"""Template tags and filters for mapping."""

from django import template

register = template.Library()

@register.inclusion_tag('_location_map.html')
def location_map(**kwargs):
    location = kwargs['location']
    width_px = kwargs['width_px']
    height_px = kwargs['height_px']
    zoom = kwargs['zoom']
    id = kwargs['id']
    return {
        'location': location,
        'width_px': width_px,
        'height_px': height_px,
        'zoom': zoom,
        'id': id
    }
