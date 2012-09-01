"""Site-wide template tags and filters."""

from django import template
from django.core.urlresolvers import reverse
from haystack.models import SearchResult

from gobotany.core import models

register = template.Library()

@register.filter
def url(obj):
    """Return the canonical URL in Go Botany for the given object."""

    if isinstance(obj, SearchResult):
        obj = obj.object

    if isinstance(obj, models.Taxon):
        genus_slug = obj.genus_name().lower()
        return reverse('simplekey-species', args=(genus_slug, obj.epithet))

    raise ValueError(u'cannot construct canonical URL for %r' % (obj))
