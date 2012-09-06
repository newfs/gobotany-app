"""Site-wide template tags and filters."""

from django import template
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from gobotany.core import models
from gobotany.simplekey import models as simple_models

register = template.Library()

@register.filter
def url(obj):
    """Return the canonical URL in Go Botany for the given object."""

    # Core models.

    if isinstance(obj, models.Taxon):
        genus_slug = obj.genus_name().lower()
        return reverse('simplekey-species', args=(genus_slug, obj.epithet))

    if isinstance(obj, models.Family):
        return reverse('simplekey-family', args=(obj.name.lower(),))

    if isinstance(obj, models.Genus):
        return reverse('simplekey-genus', args=(obj.name.lower(),))

    if isinstance(obj, models.GlossaryTerm):
        url = reverse('site-glossary', args=(obj.term[0].lower(),))
        return url + '#' + slugify(obj.term)

    # Pages.

    if isinstance(obj, simple_models.GroupsListPage):
        return reverse('level1', args=('simple',))

    if isinstance(obj, simple_models.PlainPage):
        return obj.url_path

    if isinstance(obj, simple_models.SubgroupResultsPage):
        slug1 = obj.subgroup.pilegroup.slug
        slug2 = obj.subgroup.slug
        return reverse('level3', args=('simple', slug1, slug2))

    if isinstance(obj, simple_models.SubgroupsListPage):
        slug = slugify(obj.title.split(':')[0])
        return reverse('level2', args=('simple', slug))

    raise ValueError(u'cannot construct canonical URL for %r' % (obj))
