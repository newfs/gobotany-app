"""Site-wide template tags and filters."""

import os

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


@register.tag
def nav_item(parser, token):
    """Return a navigation item, hyperlinked if appropriate."""
    token_parts = token.split_contents()
    print 'token_parts:', token_parts
    label = token_parts[1]
    named_url = token_parts[2]
    extra_path_item = None
    if len(token_parts) > 3:
        extra_path_item = token_parts[3]
    return NavigationItemNode(label, named_url,
                              extra_path_item=extra_path_item)

class NavigationItemNode(template.Node):
    def __init__(self, label, named_url, extra_path_item=None):
        self.label = label[1:-1]
        self.named_url = named_url
        self.extra_path_item = None
        if extra_path_item:
            self.extra_path_item = extra_path_item[1:-1]

    def render(self, context):
        try:
            if not self.extra_path_item:
                url_path = reverse(self.named_url)
            else:
                url_path = reverse(self.named_url,
                                   args=(self.extra_path_item,))
            request = context['request']
            href = ''
            if url_path != request.path:
                href='href="%s"' % url_path
            html = '<a %s>%s</a>' % (href, self.label)
            return html
        except template.VariableDoesNotExist:
            return ''
