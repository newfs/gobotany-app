"""Site-wide template tags and filters."""

import re

from hashlib import md5

from django import template
from django.core.urlresolvers import NoReverseMatch, reverse
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


@register.filter
@stringfilter
def italicize_if_scientific(plant_name):
    """Italicize a plant name if it appears to be a scientific name."""
    genus_suffix_pattern = re.compile('^[a-z]*(aba|aca|ace|aea|aga|ago|ala|ale|ana|ans|apa|ari|asa|ata|aya|bar|bea|bes|bia|bis|boa|bum|bus|cca|cea|cer|che|cia|cio|cis|cos|cum|cus|dea|des|dia|dix|don|dra|dum|dus|eca|eda|ega|eja|ela|ema|ena|ene|ens|era|eta|eum|eza|fia|gea|gia|gma|gon|gus|har|hea|hes|hia|hin|his|hne|hoe|hra|hum|hus|hys|ias|ica|ida|ier|ies|ila|ile|ina|ine|ion|ios|ipa|ira|isa|ita|ium|ius|iva|iza|jas|jum|kea|kia|lax|lea|les|lex|lia|lis|lla|loa|lon|los|lox|lpa|lum|lus|lva|mba|mbo|mex|mia|mis|mma|mna|mon|mos|mum|mus|nax|nca|nda|nia|nis|nna|nos|num|nus|nya|oca|oce|oda|oea|oga|ola|oma|one|opa|ops|ora|osa|ota|oua|ous|oxa|pha|pia|ps|poa|pon|pos|ppa|pso|pta|pum|pus|ras|rba|rca|rda|rea|rex|ria|ris|rix|rma|roa|ron|ros|rta|rum|rus|rya|rys|ses|sia|sis|sma|spi|ssa|sta|sum|sus|tea|ter|tes|tha|the|tia|tis|ton|tra|tum|tus|tys|uca|uga|ugo|uja|ula|una|ura|usa|uta|uus|ver|via|vum|wia|xia|xis|xon|xus|xys|yia|yle|yma|yos|zia|zea|zus)$', re.IGNORECASE)

    first_word = plant_name.split(' ')[0].lower()

    # Start with checking the suffix of the first word to see if it
    # looks like a genus.
    is_scientific_name = genus_suffix_pattern.match(first_word)

    # Disqualify some false positives.
    if (first_word.find('-') > -1 or
        first_word.find('\'') > -1 or
        first_word in ['alpine', 'ambiguous', 'bitter', 'bulbous', 'button',
                       'california', 'canada', 'carolina', 'chile',
                       'cinnamon', 'common', 'dioecious', 'dragon', 'fragile',
                       'georgia', 'glaucous', 'greater', 'himalaya',
                       'herbaceous', 'hops', 'india', 'jasmine', 'korea',
                       'kousa', 'lace', 'lemon', 'limestone', 'london',
                       'mugo', 'necklace', 'oklahoma', 'opium', 'osier',
                       'pagoda', 'pale', 'pennsylvania', 'pine', 'porcupine',
                       'proliferous', 'rhodes', 'river', 'rufous', 'russia',
                       'sago', 'saline', 'sandbar', 'scabrous', 'seneca',
                       'serpentine', 'spearscale', 'silkvine', 'silver',
                       'sweetgale', 'taravine', 'tifton', 'tuberous',
                       'tundra', 'turion', 'umbrella', 'vanilla', 'virginia',
                       'washington', 'water', 'watermelon', 'wine', 'winter',
                       'woodbine',
                      ] or
        plant_name.lower() in ['anemone meadow-rue', # Anemone is also a genus
                              ]):
        is_scientific_name = False

    if is_scientific_name:
        CONNECTING_TERMS = ['subsp.', 'ssp.', 'var.', 'subvar.', 'f.',
                            'forma', 'subf.']
        words = []
        for word in plant_name.split(' '):
            if word not in CONNECTING_TERMS:
                words.append('<i>%s</i>' % word)
            else:
                words.append(word)
        return ' '.join(words)
    else:
        return plant_name


@register.tag
def nav_item(parser, token):
    """Return a navigation item, hyperlinked if appropriate."""
    token_parts = token.split_contents()
    label = token_parts[1]
    named_url = None
    if len(token_parts) > 2:
        named_url = token_parts[2]
    extra_path_item = None
    if len(token_parts) > 3:
        extra_path_item = token_parts[3]
    return NavigationItemNode(label, named_url,
                              extra_path_item=extra_path_item)

class NavigationItemNode(template.Node):
    def __init__(self, label, named_url, extra_path_item=None):
        self.label = template.Variable(label)
        self.named_url = None
        if named_url:
            self.named_url = named_url
        self.extra_path_item = None
        if extra_path_item:
            self.extra_path_item = extra_path_item[1:-1]

    def render(self, context):
        # Handle either a variable or a string as the label.
        try:
            label_from_variable = self.label.resolve(context)
            self.label = label_from_variable
        except template.VariableDoesNotExist:
            # Treat the label as a string: trim quotes.
            self.label = self.label.tostring()[1:-1]

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
        except NoReverseMatch:
            # No matching URL exists yet, so display just the text.
            return '<span>%s</span>' % self.label
        else:
            return ''
