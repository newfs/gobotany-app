# -*- coding: utf-8 -*-
import string
import urllib2

from datetime import date
from itertools import chain, groupby
from operator import attrgetter, itemgetter

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.utils import simplejson
from django.views.decorators.vary import vary_on_headers

from gobotany.core import botany
from gobotany.core import models
from gobotany.core.models import (
    CharacterGroup, CharacterValue, DefaultFilter, Family, Genus,
    GlossaryTerm, Habitat, HomePageImage, Pile, PileGroup,
    PlantPreviewCharacter, Taxon,
    )
from gobotany.core.partner import which_partner
from gobotany.plantoftheday.models import PlantOfTheDay
from gobotany.simplekey.groups_order import ORDERED_GROUPS
from gobotany.simplekey.models import (get_blurb, GroupsListPage,
                                       SearchSuggestion, SubgroupResultsPage,
                                       SubgroupsListPage)

#

def per_partner_template(request, template_path):
    partner = which_partner(request)
    if partner and partner.short_name != 'gobotany':
        return '{0}/{1}'.format(partner.short_name, template_path)
    else:
        return template_path

#

def get_simple_url(item):
    """Return the URL to where `item` lives in the Simple Key navigation."""
    if isinstance(item, PileGroup):
        return reverse('gobotany.simplekey.views.pilegroup_view',
                       kwargs={'pilegroup_slug': item.slug})
    elif isinstance(item, Pile):
        return reverse('gobotany.simplekey.views.results_view',
                       kwargs={'pilegroup_slug': item.pilegroup.slug,
                               'pile_slug': item.slug})
    else:
        raise ValueError('the Simple Key has no URL for %r' % (item,))


def ordered_pilegroups():
    """Return all pile groups in display order."""
    return [PileGroup.objects.get(slug=group.keys()[0])
            for group in ORDERED_GROUPS]


def ordered_piles(pilegroup):
    """Return all piles for a pile group in display order."""
    return [
        pile for pile in [
            Pile.objects.get(slug=pile_slug) for pile_slug in
            list(chain(*[group.values()[0] for group in ORDERED_GROUPS]))
        ]
        if pile in pilegroup.piles.all()
    ]


def index_view(request):
    """View for the main page of the Go Botany site.

    Note: The "main heading" variable was used to demo early
    capabilities for partner sites before the visual design was
    implemented. Currently the value of this variable does not get
    displayed on the page, but the code is left in place pending our
    eventual earnest customizations for specific partner sites.
    """
    main_heading = 'Simple Key: Getting Started'
    partner = which_partner(request)
    if partner:
        if partner.short_name == 'montshire':
            main_heading = 'Montshire %s' % main_heading

    blurb = get_blurb('getting_started')

    home_page_images = HomePageImage.objects.order_by('order')

    # Get or generate today's Plant of the Day.
    plant_of_the_day = PlantOfTheDay.get_by_date.for_day(
        date.today(), partner.short_name)
    # Get the Taxon record of the Plant of the Day.
    plant_of_the_day_taxon = None
    try:
        plant_of_the_day_taxon = Taxon.objects.get(
            scientific_name=plant_of_the_day.scientific_name)
    except ObjectDoesNotExist:
        pass

    plant_of_the_day_image = None
    species_images = botany.species_images(plant_of_the_day_taxon)
    if species_images:
        plant_of_the_day_image = botany.species_images(
            plant_of_the_day_taxon)[0]

    return render_to_response('simplekey/index.html', {
            'main_heading': main_heading,
            'blurb': blurb,
            'home_page_images': home_page_images,
            'plant_of_the_day': plant_of_the_day_taxon,
            'plant_of_the_day_image': plant_of_the_day_image,
            }, context_instance=RequestContext(request))

def advanced_view(request):
    return render_to_response('simplekey/advanced.html', {},
            context_instance=RequestContext(request))

def guided_search_view(request):
    return render_to_response('simplekey/guided_search.html', {
            }, context_instance=RequestContext(request))

def _partner_short_name(partner):
    short_name = None
    if partner:
        short_name = partner.short_name
    return short_name

def simple_key_view(request):
    partner = which_partner(request)
    short_name = _partner_short_name(partner)
    groups_list_page = GroupsListPage.objects.all()[0]

    return render_to_response('simplekey/simple.html', {
            'partner_site': short_name,
            'groups_list_page': groups_list_page,
            'pilegroups': [
                (pilegroup, pilegroup.pilegroupimage_set.all(),
                 get_simple_url(pilegroup))
                for pilegroup in ordered_pilegroups()
                ]
            }, context_instance=RequestContext(request))

def pilegroup_view(request, pilegroup_slug):
    pilegroup = get_object_or_404(PileGroup, slug=pilegroup_slug)

    partner = which_partner(request)
    short_name = _partner_short_name(partner)
    subgroups_list_page = SubgroupsListPage.objects.get(group=pilegroup)

    return render_to_response('simplekey/pilegroup.html', {
            'partner_site': short_name,
            'subgroups_list_page': subgroups_list_page,
            'pilegroup': pilegroup,
            'piles': [
                (pile, pile.pileimage_set.all(), get_simple_url(pile))
                for pile in ordered_piles(pilegroup)
                ]
            }, context_instance=RequestContext(request))

def results_view(request, pilegroup_slug, pile_slug):
    pile = get_object_or_404(Pile, slug=pile_slug)
    if pile.pilegroup.slug != pilegroup_slug:
        raise Http404

    partner = which_partner(request)
    short_name = _partner_short_name(partner)
    subgroup_results_page = SubgroupResultsPage.objects.get(subgroup=pile)

    return render_to_response('simplekey/results.html', {
           'partner_site': short_name,
           'subgroup_results_page': subgroup_results_page,
           'pilegroup': pile.pilegroup,
           'pile': pile,
           }, context_instance=RequestContext(request))


def _format_character_value(character_value):
    """Render a character value for display."""
    if character_value:
        character = character_value.character
        if character.value_type == 'TEXT':
            return (character_value.friendly_text or
                    character_value.value_str or u'')
        else:
            if character.unit not in (None, '', 'NA'):
                minstr = ('Anything' if character_value.value_min is None
                          else u'%.3g' % character_value.value_min)
                maxstr = ('Anything' if character_value.value_max is None
                          else u'%.3g' % character_value.value_max)
                return u'%s–%s %s' % (minstr, maxstr, character.unit)
            else:
                minstr = ('?' if character_value.value_min is None
                          else u'%.3g' % character_value.value_min)
                maxstr = ('?' if character_value.value_max is None
                          else u'%.3g' % character_value.value_max)
                return u'%s–%s' % (minstr, maxstr)
    else:
        return ''


def _get_all_characteristics(taxon, character_groups):
    """Get all characteristics for a plant, organized by character group."""

    # Ensure the query is ordered so the character values can
    # successfully be grouped.
    q = (CharacterValue.objects.filter(taxon_character_values__taxon=taxon)
                               .order_by('character'))

    # Combine multiple values that belong to a single character.
    cgetter = attrgetter('character')
    cvgroups = groupby(q, key=cgetter)
    characters = ({
        'group': character.character_group.name,
        'name': character.friendly_name,
        'value': \
            u', '.join(sorted(_format_character_value(cv) for cv in values)),
        } for character, values in cvgroups)

    # Group the characters by character-group.
    ggetter = itemgetter('group')
    cgroups = groupby(sorted(characters, key=ggetter), key=ggetter)
    groups = ({
        'name': name,
        'characters': sorted(members, key=itemgetter('name')),
        } for name, members in cgroups)
    return sorted(groups, key=itemgetter('name'))


def _get_brief_characteristics(all_characteristics, pile, partner):
    """Get the short list of characteristics that help give a quick
       impression of the plant.
       Like the plant preview popups on the filtering page, this is a
       combination of plant preview characters and some of the pile's
       default filters.
    """
    plant_preview_character_names = [
        ppc.character.friendly_name
        for ppc in PlantPreviewCharacter.objects.filter(
            pile=pile, partner_site=partner)
        ]

    brief_characteristics = []
    for character_group in all_characteristics:
        for character in character_group['characters']:
            if character['name'] in plant_preview_character_names:
                brief_characteristics.append(character)
    return sorted(brief_characteristics, key=itemgetter('name'))


def species_view(request, genus_slug, specific_name_slug,
                 pilegroup_slug=None, pile_slug=None):
    scientific_name = '%s %s' % (genus_slug.capitalize(), specific_name_slug)
    scientific_name_short = '%s. %s' % (scientific_name[0], specific_name_slug)
    taxon = get_object_or_404(Taxon, scientific_name=scientific_name)

    if pile_slug and pilegroup_slug:
        pile = get_object_or_404(Pile, slug=pile_slug)
        if pile.pilegroup.slug != pilegroup_slug:
            raise Http404
    else:
        # Get the first pile from the species
        pile = taxon.piles.all()[0]
    pilegroup = pile.pilegroup

    partner = which_partner(request)
    partner_species = None
    if partner:
        rows = models.PartnerSpecies.objects.filter(
            species=taxon, partner=partner).all()
        if rows:
            partner_species = rows[0]

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

    all_characteristics = _get_all_characteristics(taxon, character_groups)

    last_plant_id_url = request.COOKIES.get('last_plant_id_url', None)
    if last_plant_id_url:
        last_plant_id_url = urllib2.unquote(last_plant_id_url)

    return render_to_response('simplekey/species.html', {
           'pilegroup': pilegroup,
           'pile': pile,
           'scientific_name': scientific_name,
           'scientific_name_short': scientific_name_short,
           'taxon': taxon,
           'species_images': species_images,
           'partner_heading': partner_species.species_page_heading
               if partner_species else None,
           'partner_blurb': partner_species.species_page_blurb
               if partner_species else None,
           'habitats': habitats,
           'brief_characteristics': _get_brief_characteristics(
                all_characteristics, pile, which_partner(request)),
           'all_characteristics': all_characteristics,
           'specific_epithet': specific_name_slug,
           'last_plant_id_url': last_plant_id_url,
           }, context_instance=RequestContext(request))

def genus_view(request, genus_slug):
    genus = get_object_or_404(Genus, slug=genus_slug.lower())

    # If it is decided that common names will not be required, change the
    # default below to None so the template will omit the name if missing.
    DEFAULT_COMMON_NAME = 'common name here'
    common_name = genus.common_name or DEFAULT_COMMON_NAME

    genus_drawings = genus.images.filter(image_type__name='example drawing')
    if not genus_drawings:
        # Prepare some dummy drawings with dummy captions to try and
        # make it obvious that the images aren't the final ones.
        species = genus.taxa.all()
        for s in species:
            species_images = botany.species_images(s)
            if len(species_images) > 2:
                genus_drawings = species_images[0:3]
                break
        for drawing in genus_drawings:
            drawing.alt = 'Placeholder image'

    pile = genus.taxa.all()[0].piles.all()[0]
    pilegroup = pile.pilegroup

    return render_to_response('simplekey/genus.html', {
           'genus': genus,
           'common_name': common_name,
           'genus_drawings': genus_drawings,
           'pilegroup': pilegroup,
           'pile': pile,
           }, context_instance=RequestContext(request))

def genus_redirect_view(request, genus_slug):
    return redirect('simplekey-genus', genus_slug=genus_slug)


def family_view(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug.lower())

    # If it is decided that common names will not be required, change the
    # default below to None so the template will omit the name if missing.
    DEFAULT_COMMON_NAME = 'common name here'
    common_name = family.common_name or DEFAULT_COMMON_NAME

    family_drawings = (family.images.filter(
                       image_type__name='example drawing'))
    if not family_drawings:
        # Prepare some dummy drawings with dummy captions to try and
        # make it obvious that the images aren't the final ones.
        species = family.taxa.all()
        for s in species:
            species_images = botany.species_images(s)
            if len(species_images) > 2:
                family_drawings = species_images[0:3]
                break
        for drawing in family_drawings:
            drawing.alt = 'Placeholder image'

    pile = family.taxa.all()[0].piles.all()[0]
    pilegroup = pile.pilegroup

    return render_to_response('simplekey/family.html', {
           'family': family,
           'common_name': common_name,
           'family_drawings': family_drawings,
           'pilegroup': pilegroup,
           'pile': pile,
           }, context_instance=RequestContext(request))


def help_redirect_view(request):
    return redirect('simplekey-help-start')

def help_about_view(request):
    return render_to_response('simplekey/help_about.html', {
           'section_1_heading_blurb': get_blurb('section_1_heading'),
           'section_1_content_blurb': get_blurb('section_1_content'),
           'section_2_heading_blurb': get_blurb('section_2_heading'),
           'section_2_content_blurb': get_blurb('section_2_content'),
           'section_3_heading_blurb': get_blurb('section_3_heading'),
           'section_3_content_blurb': get_blurb('section_3_content'),
           }, context_instance=RequestContext(request))

@vary_on_headers('Host')
def help_start_view(request):
    youtube_id = ''
    youtube_id_blurb = get_blurb('getting_started_youtube_id')
    if not youtube_id_blurb.startswith('[Provide text'):
        # We have an actual YouTube id defined in the database.
        youtube_id = youtube_id_blurb
    return render_to_response(
        per_partner_template(request, 'simplekey/help_start.html'), {
            'getting_started_blurb': get_blurb('getting_started'),
            'getting_started_youtube_id': youtube_id,
            }, context_instance=RequestContext(request))

def help_map_view(request):
    pilegroups = [(pilegroup, ordered_piles(pilegroup))
                  for pilegroup in ordered_pilegroups()]

    return render_to_response('simplekey/help_map.html', {
            'pilegroups': pilegroups
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

def _get_pilegroup_dict(pilegroup_name):
    pilegroup = PileGroup.objects.get(name=pilegroup_name)
    return {
        'title': pilegroup.friendly_title,
        'youtube_id': pilegroup.youtube_id
    }

def _get_pile_dict(pile_name):
    pile = Pile.objects.get(name=pile_name)
    return {
        'title': pile.friendly_title,
        'youtube_id': pile.youtube_id
    }

def help_video_view(request):
    # The Getting Started video is first, followed by videos for the pile
    # groups and piles in the order that they are presented in the stepwise
    # pages at the beginning of plant identification.
    videos = [{'title': 'Getting Started',
               'youtube_id': get_blurb('getting_started_youtube_id')}]

    for pilegroup in ordered_pilegroups():
        videos.append(_get_pilegroup_dict(pilegroup.name))
        for pile in ordered_piles(pilegroup):
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

def maptest(request):
    return render_to_response('simplekey/maptest.html', {
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
        # This query is case-insensitive while the database field is
        # case-sensitive. By querying case-insensitively here, if
        # the import process did not screen duplicates, then duplicate
        # suggestions will be returned. However, this is better than
        # querying case-sensitively and potentially missing a bunch
        # of valid suggestion results because cases didn't match.
        suggestions = list(SearchSuggestion.objects.filter(
            term__istartswith=query).values_list('term',
            flat=True)[:MAX_RESULTS * 2])
        # Remove any duplicates due to case-sensitivity and pare down to
        # the desired number of results.
        suggestions = list(set(
            [suggestion.lower() for suggestion in suggestions]))[:MAX_RESULTS]
    return HttpResponse(simplejson.dumps(suggestions),
                        mimetype='application/json')
