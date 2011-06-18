# -*- coding: utf-8 -*-
import string
from itertools import groupby
from operator import attrgetter, itemgetter

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.utils import simplejson

from gobotany.core import botany
from gobotany.core.models import (
    CharacterGroup, CharacterValue, Family, Genus, GlossaryTerm, Habitat,
    Pile, PileGroup, Taxon, TaxonCharacterValue,
    )
from gobotany.simplekey import partners
from gobotany.simplekey.models import Page, get_blurb, SearchSuggestion


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
    site = partners.get_site(request)
    main_heading = site.index_page_main_heading()

    blurb = get_blurb('getting_started')

    return render_to_response('simplekey/index.html', {
            'main_heading': main_heading,
            'blurb': blurb,
            }, context_instance=RequestContext(request))

def advanced_view(request):
    return render_to_response('simplekey/advanced.html', {},
            context_instance=RequestContext(request))

def map_view(request):
    return render_to_response('simplekey/map.html', {
            'pages': Page.objects.order_by('number').all(),
            }, context_instance=RequestContext(request))

def guided_search_view(request):
    return render_to_response('simplekey/guided_search.html', {
            }, context_instance=RequestContext(request))

def page_view(request, number):
    try:
        number = int(number)
    except ValueError:
        raise Http404
    page = get_object_or_404(Page, number=number)
    site = partners.get_site(request)
    return render_to_response('simplekey/page.html', {
            'partner_site': site.short_name,
            'page': page,
            'pilegroups_and_urls': [
                (pilegroup, get_simple_url(pilegroup))
                for pilegroup in page.pilegroups.order_by('id').all()
                ]
            }, context_instance=RequestContext(request))

def get_parent_page(pilegroup):
    parent_page = Page.objects.get(pilegroups=pilegroup)
    return parent_page

def pilegroup_view(request, pilegroup_slug):
    pilegroup = get_object_or_404(PileGroup, slug=pilegroup_slug)
    site = partners.get_site(request)
    parent_page = get_parent_page(pilegroup)
    return render_to_response('simplekey/pilegroup.html', {
            'partner_site': site.short_name,
            'parent_page': parent_page,
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
    site = partners.get_site(request)
    return render_to_response('simplekey/results.html', {
           'partner_site': site.short_name,
           'pilegroup': pile.pilegroup,
           'pile': pile,
           }, context_instance=RequestContext(request))


def _get_species_characteristics(pile, taxon):
    """Get the short list of characteristics that help give a quick
       impression of the plant.
    """
    characteristics = []
    # Get all the character values for this taxon.
    cvs = TaxonCharacterValue.objects.filter(taxon=taxon)
    if cvs:
        for character in pile.plant_preview_characters.all():
            i = 0
            found = False
            value = ''
            while found == False and i < len(cvs):
                if cvs[i].character_value.character.short_name == \
                   character.short_name:
                    found = True
                    if (character.value_type == 'TEXT'):
                        value = cvs[i].character_value.value_str
                    else:
                        # TODO: Properly handle numeric values and units.
                        #value = cvs[i].character_value.value_str
                        value = '%s (mm?) - %s (mm?)' % \
                            (str(cvs[i].character_value.value_min),
                            str(cvs[i].character_value.value_max))
                i = i + 1
            characteristic = {}
            characteristic['name'] = character.name
            characteristic['value'] = value
            characteristics.append(characteristic)
    return characteristics


def _format_character_value(character_value):
    """Render a character value for display."""
    character = character_value.character
    if character.value_type == 'TEXT':
        return character_value.friendly_text or character_value.value_str
    elif character.unit not in (None, '', 'NA'):
        return u'%.1f–%.1f %s' % (character_value.value_min,
                                  character_value.value_max, character.unit)
    else:
        return u'%d–%d' % (
            character_value.value_min, character_value.value_max)

def _get_all_species_characteristics(taxon, character_groups):
    """Get all characteristics for a plant, organized by character group."""

    q = CharacterValue.objects.filter(taxon_character_values__taxon=taxon)

    # Combine multiple values that belong to a single character.
    cgetter = attrgetter('character')
    cvgroups = groupby(sorted(q, key=cgetter), cgetter)
    characters = ({
        'group': character.character_group.name,
        'name': character.name,
        'value': ', '.join(_format_character_value(cv) for cv in values),
        } for character, values in cvgroups)

    # Group the characters by character-group.
    ggetter = itemgetter('group')
    cgroups = groupby(sorted(characters, key=ggetter), key=ggetter)
    groups = ({
        'name': name,
        'characters': sorted(members, key=itemgetter('name')),
        } for name, members in cgroups)
    return sorted(groups, key=itemgetter('name'))


def species_view(request, genus_slug, specific_name_slug,
                 pilegroup_slug=None, pile_slug=None):
    scientific_name = '%s %s' % (genus_slug.capitalize(), specific_name_slug)
    taxon = get_object_or_404(Taxon, scientific_name=scientific_name)

    if pile_slug and pilegroup_slug:
        pile = get_object_or_404(Pile, slug=pile_slug)
        if pile.pilegroup.slug != pilegroup_slug:
            raise Http404
    else:
        # Get the first pile from the species
        pile = taxon.piles.all()[0]
    pilegroup = pile.pilegroup

    species_images = botany.species_images(taxon)
    habitats = []
    if taxon.habitat:
        habitat_names = taxon.habitat.split('| ')
        for name in habitat_names:
            try:
                habitat = Habitat.objects.get(name__iexact=name)
                habitats.append(habitat.friendly_name)
            except Habitat.DoesNotExist:
                continue
        habitats.sort()

    character_ids = taxon.character_values.values_list(
                    'character', flat=True).distinct()
    character_groups = CharacterGroup.objects.filter(
                       character__in=character_ids).distinct()

    return render_to_response('simplekey/species.html', {
           'pilegroup': pilegroup,
           'pile': pile,
           'scientific_name': scientific_name,
           'taxon': taxon,
           'species_images': species_images,
           'habitats': habitats,
           'characteristics': _get_species_characteristics(pile, taxon),
           'all_characteristics': _get_all_species_characteristics(
                taxon, character_groups),
           'specific_epithet': specific_name_slug,
           }, context_instance=RequestContext(request))

def genus_view(request, genus_slug):
    genus = get_object_or_404(Genus, slug=genus_slug.lower())

    genus_images = genus.images.filter(image_type__name='example image')
    # If no genus images are set, use the images from a species for now.
    if not genus_images:
        species = genus.taxa.all()
        for s in species:
            genus_images = botany.species_images(s)

    genus_drawings = genus.images.filter(image_type__name='example drawing')
    return render_to_response('simplekey/genus.html', {
           'item': genus,
           'item_images': genus_images,
           'item_drawings': genus_drawings,
           }, context_instance=RequestContext(request))

def genus_redirect_view(request, genus_slug):
    return redirect('simplekey-genus', genus_slug=genus_slug)

def family_view(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug.lower())
    
    family_images = family.images.filter(image_type__name='example image')
    # If no family images are set, use the images from a species for now.
    if not family_images:
        species = family.taxa.all()
        for s in species:
            family_images = botany.species_images(s)
    
    family_drawings = family.images.filter(image_type__name='example drawing')
    return render_to_response('simplekey/family.html', {
           'item': family,
           'item_images': family_images,
           'item_drawings': family_drawings,
           }, context_instance=RequestContext(request))

def help_about_view(request):
    return render_to_response('simplekey/help_about.html', {
           'section_1_heading_blurb': get_blurb('section_1_heading'),
           'section_1_content_blurb': get_blurb('section_1_content'),
           'section_2_heading_blurb': get_blurb('section_2_heading'),
           'section_2_content_blurb': get_blurb('section_2_content'),
           'section_3_heading_blurb': get_blurb('section_3_heading'),
           'section_3_content_blurb': get_blurb('section_3_content'),
           }, context_instance=RequestContext(request))

def help_start_view(request):
    youtube_id = ''
    youtube_id_blurb = get_blurb('getting_started_youtube_id')
    if not youtube_id_blurb.startswith('[Provide text'):
        # We have an actual YouTube id defined in the database.
        youtube_id = youtube_id_blurb
    return render_to_response('simplekey/help_start.html', {
           'getting_started_blurb': get_blurb('getting_started'),
           'getting_started_youtube_id': youtube_id,
           }, context_instance=RequestContext(request))

def help_collections_view(request):
    return render_to_response('simplekey/help_collections.html', {
            'pages': Page.objects.order_by('number').all(),
            }, context_instance=RequestContext(request))

def help_glossary_view(request, letter):
    glossary = GlossaryTerm.objects.filter(visible=True).extra(
        select={'lower_term': 'lower(term)'}).order_by('lower_term')

    terms = glossary.values_list('lower_term', flat=True)
    letters_in_glossary = [term[0] for term in terms]

    # Skip any glossary terms that start with a number, and filter to the
    # desired letter.
    glossary = glossary.filter(term__gte='a', term__startswith=letter)

    return render_to_response('simplekey/help_glossary.html', {
            'this_letter': letter,
            'letters': string.ascii_lowercase,
            'letters_in_glossary': letters_in_glossary,
            'glossary': glossary,
            }, context_instance=RequestContext(request))

def help_glossary_redirect_view(request):
    return redirect('simplekey-help-glossary', letter='a')

def _get_pilegroup_youtube_id(pilegroup_name):
    pilegroup = PileGroup.objects.get(name=pilegroup_name)
    return pilegroup.youtube_id

def _get_pile_youtube_id(pile_name):
    pile = Pile.objects.get(name=pile_name)
    return pile.youtube_id
    
def _get_pilegroup_dict(pilegroup_name):
    return {'title': pilegroup_name, 
            'youtube_id': _get_pilegroup_youtube_id(pilegroup_name)}

def _get_pile_dict(pile_name):
    return {'title': pile_name, 'youtube_id': _get_pile_youtube_id(pile_name)}

def help_video_view(request):
    # The Getting Started video is first, followed by videos for the pile
    # groups and piles in the order that they are presented in the stepwise
    # pages at the beginning of plant identification.
    videos = [{'title': 'Getting Started',
               'youtube_id': get_blurb('getting_started_youtube_id')}]

    pages = Page.objects.order_by('number').all()
    for page in pages:
        for pilegroup in page.pilegroups.all():
            videos.append(_get_pilegroup_dict(pilegroup.name))
            for pile in pilegroup.piles.all():
                videos.append(_get_pile_dict(pile.name))

    return render_to_response('simplekey/help_video.html', {
           'videos': videos,
           }, context_instance=RequestContext(request))

def video_pilegroup_view(request, pilegroup_slug):
    pilegroup = get_object_or_404(PileGroup, slug=pilegroup_slug)
    return render_to_response('simplekey/video.html', {
            'pilegroup': pilegroup,
            }, context_instance=RequestContext(request))

def video_pile_view(request, pilegroup_slug, pile_slug):
    pile = get_object_or_404(Pile, slug=pile_slug)
    if pile.pilegroup.slug != pilegroup_slug:
        raise Http404
    return render_to_response('simplekey/video.html', {
           'pilegroup': pile.pilegroup,
           'pile': pile,
           }, context_instance=RequestContext(request))

def rulertest(request):
    return render_to_response('simplekey/rulertest.html', {
            }, context_instance=RequestContext(request))

def suggest_view(request):
    # Return some search suggestions for the auto-suggest feature.
    MAX_RESULTS = 10
    query = request.GET.get('q', '')
    suggestions = []
    if query != '':
        suggestions = list(SearchSuggestion.objects.filter(
            term__istartswith=query).values_list('term',
            flat=True)[:MAX_RESULTS])
    return HttpResponse(simplejson.dumps(suggestions),
                        mimetype='application/json')
