import string
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from gobotany.core import botany
from gobotany.core.models import GlossaryTerm, Pile, PileGroup
from gobotany.core.models import Taxon, TaxonCharacterValue
from gobotany.simplekey.models import Page, get_blurb


def get_simple_url(item):
    """Return the URL to where `item` lives in the Simple Key navigation."""
    if isinstance(item, Page):
        return item.get_absolute_url()
    if isinstance(item, PileGroup):
        return reverse('gobotany.simplekey.views.pilegroup_view',
                       kwargs={'pilegroup_slug': item.slug})
    elif isinstance(item, Pile):
        return reverse('gobotany.simplekey.views.results_view',
                       kwargs={'pilegroup_slug': item.pilegroup.slug,
                               'pile_slug': item.slug})
    else:
        raise ValueError('the Simple Key has no URL for %r' % (item,))


def index_view(request):
    blurb = get_blurb('index_instructions')
    c = request.COOKIES.get('skip_getting_started', '')
    skip_getting_started = (c == 'skip')
    if skip_getting_started and request.GET.get('skip') != 'no':
        return redirect('1/')
    return render_to_response('simplekey/index.html', {
            'blurb': blurb,
            'skip_getting_started': skip_getting_started,
            }, context_instance=RequestContext(request))


def map_view(request):
    return render_to_response('simplekey/map.html', {
            'pages': Page.objects.order_by('number').all(),
            }, context_instance=RequestContext(request))


def glossary_view(request, letter):
    glossary = GlossaryTerm.objects.filter(visible=True).extra(
        select={'lower_term': 'lower(term)'}).order_by('lower_term')
    if letter == '1':
        # All terms whose names start with a number.
        glossary = glossary.filter(term__gte='1', term__lte='9z')
    else:
        glossary = glossary.filter(term__startswith=letter)
    # Case-insensitive sort
    return render_to_response('simplekey/glossary.html', {
            'this_letter': letter,
            'letters': '1' + string.ascii_lowercase,
            'glossary': glossary,
            }, context_instance=RequestContext(request))


def page_view(request, number):
    try:
        number = int(number)
    except ValueError:
        raise Http404
    page = get_object_or_404(Page, number=number)
    return render_to_response('simplekey/page.html', {
            'page': page,
            'pilegroups_and_urls': [
                (pilegroup, get_simple_url(pilegroup))
                for pilegroup in page.pilegroups.order_by('id').all()
                ]
            }, context_instance=RequestContext(request))


def pilegroup_view(request, pilegroup_slug):
    pilegroup = get_object_or_404(PileGroup, slug=pilegroup_slug)
    return render_to_response('simplekey/pilegroup.html', {
            'pilegroup': pilegroup,
            'piles_and_urls': [
                (pile, get_simple_url(pile))
                for pile in pilegroup.piles.order_by('slug').all()
                ]
            }, context_instance=RequestContext(request))


def results_view(request, pilegroup_slug, pile_slug):
    pile = get_object_or_404(Pile, slug=pile_slug)
    if pile.pilegroup.slug != pilegroup_slug:
        raise Http404
    return render_to_response('simplekey/results.html', {
           'pilegroup': pile.pilegroup,
           'pile': pile,
           }, context_instance=RequestContext(request))


def _get_states_status(taxon):
    DEFAULT_STATUS = 'absent'
    STATES = ['CT', 'MA', 'ME', 'NH', 'RI', 'VT']
    status = dict().fromkeys(STATES, DEFAULT_STATUS)
    # If the taxon is present in a state, set its status as such.
    distribution = []
    if taxon.distribution:
        distribution = taxon.distribution.replace(' ', '').split('|')
    for state in distribution:
        if status.has_key(state):
            status[state] = 'present'
    # Add any conservation status information for each state.
    for state in STATES:
        # Check the appropriate taxon field.
        status_field_name = 'conservation_status_%s' % state.lower()
        conservation_status = getattr(taxon, status_field_name)
        if conservation_status:
            if conservation_status == 'E':
                conservation_status = 'endangered'
            elif conservation_status == 'T':
                conservation_status = 'threatened'
            # TODO: handle remaining status codes (what do they mean?)
            status[state] = conservation_status
    # Add any invasive status information.
    invasive_states = []
    if taxon.invasive_in_states:
        invasive_states = taxon.invasive_in_states.replace(' ', '').split('|')
    for state in invasive_states:
        if status.has_key(state):
            status[state] = 'invasive'
    # Add any sale-prohibited status information, which trumps invasive
    # status that may have just been set.
    sale_prohibited_states = []
    if taxon.sale_prohibited_in_states:
        sale_prohibited_states = \
            taxon.sale_prohibited_in_states.replace(' ', '').split('|')
    for state in sale_prohibited_states:
        if status.has_key(state):
            status[state] = 'sale prohibited'
    return status


def _get_species_characteristics(pile, taxon):
    characteristics = []
    # Get all the character values for this taxon.
    cvs = TaxonCharacterValue.objects.filter(taxon=taxon)
    if cvs:
        for filter in pile.default_filters.all():
            i = 0
            found = False
            value = ''
            while found == False and i < len(cvs):
                if cvs[i].character_value.character.short_name == \
                   filter.short_name:
                    found = True
                    value = cvs[i].character_value.value_str
                    # TODO: Add support for numeric values too.
                i = i + 1
            characteristic = {}
            characteristic['name'] = filter.name
            characteristic['value'] = value
            characteristics.append(characteristic)
    return characteristics


def species_view(request, pilegroup_slug, pile_slug, genus_slug,
                 specific_epithet_slug):
    pile = get_object_or_404(Pile, slug=pile_slug)
    if pile.pilegroup.slug != pilegroup_slug:
        raise Http404
    scientific_name = '%s %s' % (genus_slug.capitalize(), 
                                 specific_epithet_slug)
    taxa = Taxon.objects.filter(scientific_name=scientific_name)
    if not taxa:
        raise Http404
    taxon = taxa[0]
    species_images = botany.species_images(taxon)
    states_status = _get_states_status(taxon)
    habitats = []
    if taxon.habitat:
        habitats = taxon.habitat.split('|')
    return render_to_response('simplekey/species.html', {
           'pilegroup': pile.pilegroup,
           'pile': pile,
           'scientific_name': scientific_name,
           'taxon': taxon,
           'species_images': species_images,
           'states_status': states_status,
           'habitats': habitats,
           'characteristics': _get_species_characteristics(pile, taxon),
           }, context_instance=RequestContext(request))


def help_about(request):
    return render_to_response('simplekey/about.html')
