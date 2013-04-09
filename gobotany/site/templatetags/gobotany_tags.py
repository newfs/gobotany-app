"""Site-wide template tags and filters."""

from hashlib import md5

from django import template
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify, stringfilter

from gobotany import settings
from gobotany.version import get_version
from gobotany.core import models as core_models
from gobotany.dkey import models as dkey_models
from gobotany.plantshare import models as plantshare_models
from gobotany.search import models as search_models

register = template.Library()


@register.simple_tag()
def file_version(file_path):
    """Return a version string for a file path based on the file contents.
    Intended for use with auto-versioning CSS and JS files via query string.
    """
    file = ''.join([settings.PROJECT_ROOT, file_path])
    try:
        digest = md5(open(file, 'rb').read()).hexdigest()
    except:
        digest = ''
    return digest[:8]

@register.simple_tag()
def gobotany_version():
    """Return a site-wide version string suitable for displaying in
    footers, etc."""
    return get_version()

@register.filter
def url(obj):
    """Return the canonical URL in Go Botany for the given object."""

    # Core and PlantShare models.

    if isinstance(obj, core_models.Taxon):
        genus_slug = obj.genus_name().lower()
        return reverse('taxa-species', args=(genus_slug, obj.epithet))

    if isinstance(obj, core_models.Family):
        return reverse('taxa-family', args=(obj.name.lower(),))

    if isinstance(obj, core_models.Genus):
        return reverse('taxa-genus', args=(obj.name.lower(),))

    if isinstance(obj, core_models.GlossaryTerm):
        url = reverse('site-glossary', args=(obj.term[0].lower(),))
        return url + '#' + slugify(obj.term)

    if isinstance(obj, plantshare_models.Sighting):
        return reverse('ps-sighting', args=(obj.id,))

    if isinstance(obj, plantshare_models.Question):
        return '%s#q%d' % (reverse('ps-all-questions'), obj.id)

    # Pages.

    if isinstance(obj, search_models.GroupsListPage):
        return reverse('level1', args=('simple',))

    if isinstance(obj, search_models.PlainPage):
        return obj.url_path

    if isinstance(obj, search_models.SubgroupResultsPage):
        slug1 = obj.subgroup.pilegroup.slug
        slug2 = obj.subgroup.slug
        return reverse('level3', args=('simple', slug1, slug2))

    if isinstance(obj, search_models.SubgroupsListPage):
        slug = slugify(obj.title.split(':')[0])
        return reverse('level2', args=('simple', slug))

    if isinstance(obj, dkey_models.Page):
        slug = slugify(obj.title)
        return reverse('dkey_page', args=(slug,))

    raise ValueError(u'cannot construct canonical URL for %r' % (obj))


@register.filter
@stringfilter
def split(value, arg):
    '''Split a string into a list on the given character.'''
    return value.split(arg)


@register.tag
def nav_item(parser, token):
    """Return a navigation item, hyperlinked if appropriate."""
    token_parts = token.split_contents()
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
        args = ()
        if self.extra_path_item:
            args = (self.extra_path_item,)
        try:
            url_path = reverse(self.named_url, args=args)
            request = context['request']
            href = ''
            if url_path != request.path:
                href='href="%s"' % url_path
            html = '<a %s>%s</a>' % (href, self.label)
            return html
        except template.VariableDoesNotExist:
            return ''
