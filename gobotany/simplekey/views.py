# -*- coding: utf-8 -*-
import hashlib
import re
import string
import urllib2

from datetime import date
from itertools import groupby
from operator import attrgetter, itemgetter

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.utils import simplejson
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.http import etag
from django.views.decorators.vary import vary_on_headers

from gobotany.core import botany
from gobotany.core import models
from gobotany.core.models import (
    CharacterGroup, CharacterValue, CopyrightHolder, Family, Genus,
    GlossaryTerm, Habitat, HomePageImage, Pile, PileGroup,
    PlantPreviewCharacter, Taxon, Video
    )
from gobotany.core.partner import which_partner
from gobotany.core.pile_suffixes import pile_suffixes
from gobotany.plantoftheday.models import PlantOfTheDay
from gobotany.simplekey.groups_order import ordered_pilegroups, ordered_piles
from gobotany.simplekey.models import (GroupsListPage,
                                       SearchSuggestion, SubgroupResultsPage,
                                       SubgroupsListPage)

# Character short names common to all piles (but no suffix)
COMMON_CHARACTERS = ['habitat', 'habitat_general', 'state_distribution']

#

def per_partner_template(request, template_path):
    partner = which_partner(request)
    if partner and partner.short_name != 'gobotany':
        return '{0}/{1}'.format(partner.short_name, template_path)
    else:
        return template_path

#

def get_simple_url(pilegroup, pile=None):
    """Return the URL to where `item` lives in the Simple Key navigation."""
    if pile is None:
        return reverse('gobotany.simplekey.views.pilegroup_view',
                       kwargs={'pilegroup_slug': pilegroup.slug})
    else:
        return reverse('gobotany.simplekey.views.results_view',
                       kwargs={'pilegroup_slug': pilegroup.slug,
                               'pile_slug': pile.slug})

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
            'home_page_images': home_page_images,
            'plant_of_the_day': plant_of_the_day_taxon,
            'plant_of_the_day_image': plant_of_the_day_image,
            }, context_instance=RequestContext(request))

def advanced_view(request):
    return render_to_response('simplekey/advanced.html', {},
            context_instance=RequestContext(request))

def _partner_short_name(partner):
    short_name = None
    if partner:
        short_name = partner.short_name
    return short_name

@vary_on_headers('Host')
@cache_control(max_age=60 * 60)
@cache_page(60 * 60)
def simple_key_view(request):
    partner = which_partner(request)
    short_name = _partner_short_name(partner)
    groups_list_page = GroupsListPage.objects.get()

    pilegroups = []
    for pilegroup in ordered_pilegroups():
        images = _images_with_copyright_holders(
            models.ContentImage.objects.filter(
                pilegroupimage__pile_group=pilegroup)
            .select_related('image_type'))
        pilegroups.append((pilegroup, images, get_simple_url(pilegroup)))

    return render_to_response('simplekey/simple.html', {
            'partner_site': short_name,
            'groups_list_page': groups_list_page,
            'pilegroups': pilegroups
            }, context_instance=RequestContext(request))

@vary_on_headers('Host')
@cache_control(max_age=60 * 60)
@cache_page(60 * 60)
def pilegroup_view(request, pilegroup_slug):
    pilegroup = get_object_or_404(PileGroup, slug=pilegroup_slug)

    partner = which_partner(request)
    short_name = _partner_short_name(partner)
    subgroups_list_page = SubgroupsListPage.objects.get(group=pilegroup)

    piles = []
    for pile in ordered_piles(pilegroup):
        images = _images_with_copyright_holders(
            models.ContentImage.objects.filter(pileimage__pile=pile)
            .select_related('image_type'))
        piles.append((pile, images, get_simple_url(pilegroup, pile)))

    return render_to_response('simplekey/pilegroup.html', {
            'partner_site': short_name,
            'subgroups_list_page': subgroups_list_page,
            'pilegroup': pilegroup,
            'piles': piles
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
            NUM_FORMAT = u'%.9g'
            if character.unit not in (None, '', 'NA'):
                minstr = ('Anything' if character_value.value_min is None
                          else NUM_FORMAT % character_value.value_min)
                maxstr = ('Anything' if character_value.value_max is None
                          else NUM_FORMAT % character_value.value_max)
                if minstr == maxstr:
                    return u'%s %s' % (minstr, character.unit)
                else:
                    return u'%s–%s %s' % (minstr, maxstr, character.unit)
            else:
                minstr = ('?' if character_value.value_min is None
                          else NUM_FORMAT % character_value.value_min)
                maxstr = ('?' if character_value.value_max is None
                          else NUM_FORMAT % character_value.value_max)
                if minstr == maxstr:
                    return u'%s' % (minstr)
                else:
                    return u'%s–%s' % (minstr, maxstr)
    else:
        return ''


def _get_characters(taxon, character_groups, pile, partner):
    """Get all characteristics for a plant, organized by character group."""

    pile_suffix_dict = dict((v.lower(), k.lower())
                            for (k, v) in pile_suffixes.iteritems())

    # Ensure the query is ordered so the character values can
    # successfully be grouped.
    q = (CharacterValue.objects.filter(taxon_character_values__taxon=taxon)
                               .order_by('character'))

    # Get the set of preview characteristics and sort order
    plant_preview_characters = dict([
        (ppc.character_id, ppc.order)
        for ppc in PlantPreviewCharacter.objects.filter(
            pile=pile, partner_site=partner)
        ])

    # Screen out any character values that do not belong to this pile.
    pile_suffix = '_%s' % pile_suffix_dict[pile.name.lower()]
    q = [cv for cv in q if (cv.character.short_name.endswith(pile_suffix) or
         cv.character.short_name in COMMON_CHARACTERS)]

    # Combine multiple values that belong to a single character.
    cgetter = attrgetter('character')
    cvgroups = groupby(q, key=cgetter)
    characters = ({
        'group': character.character_group.name,
        'name': character.friendly_name,
        'values': sorted(_format_character_value(cv) for cv in values),
        'in_preview': character.id in plant_preview_characters,
        'preview_order': plant_preview_characters.get(character.id, -1),
        } for character, values in cvgroups)

    # Group the characters by character-group.
    ggetter = itemgetter('group')
    cgroups = groupby(sorted(characters, key=ggetter), key=ggetter)
    groups = ({
        'name': name,
        'characters': sorted(members, key=itemgetter('name')),
        } for name, members in cgroups)
    return sorted(groups, key=itemgetter('name'))


def _images_with_copyright_holders(images):
    # Reduce a live query object to a list to only run it once.
    if not isinstance(images, list):
        images = images.all()

    # Get the copyright holders for this set of images.
    codes = set(image.creator for image in images)
    chdict = dict((ch.coded_name, ch) for ch in CopyrightHolder.objects.filter(
            coded_name__in=codes))

    for image in images:

        # Associate each image with its copyright holder, adding the
        # copyright holder information as extra attributes.

        copyright_holder = chdict.get(image.creator)
        if copyright_holder:
            image.copyright_holder_name = copyright_holder.expanded_name
            image.copyright = copyright_holder.copyright
            image.source = copyright_holder.source

        # Grab each image's "scientific name" - or whatever string is
        # preceded by a ":" at the start of its alt text!

        image.scientific_name = (image.alt or '').split(':', 1)[0]

    return images


def _native_to_north_america_status(taxon):
    native_to_north_america = ''
    if taxon.north_american_native == True:
        native_to_north_america = 'Yes'
        if taxon.north_american_introduced == True:
            # This is for plants that are native to N. America but are
            # also native elsewhere or have introduced varieties.
            native_to_north_america += ' and no (some introduced)'
    elif taxon.north_american_native == False:
        native_to_north_america = 'No'
    return native_to_north_america


def species_view(request, genus_slug, specific_name_slug,
                 pilegroup_slug=None, pile_slug=None):

    COMPACT_MULTIVALUE_CHARACTERS = ['Habitat', 'New England state',
                                     'Specific Habitat']

    scientific_name = '%s %s' % (genus_slug.capitalize(), specific_name_slug)
    scientific_name_short = '%s. %s' % (scientific_name[0],
                                        specific_name_slug)
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
    images = _images_with_copyright_holders(species_images)

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
    characters_by_group = _get_characters(taxon, character_groups, pile,
                                          partner)
    preview_characters = sorted([
        character
            for group in characters_by_group
                for character in group['characters']
                    if character['in_preview']
        ], key=itemgetter('preview_order'))

    last_plant_id_url = request.COOKIES.get('last_plant_id_url', None)
    if last_plant_id_url:
        last_plant_id_url = urllib2.unquote(last_plant_id_url)

    native_to_north_america = _native_to_north_america_status(taxon)

    return render_to_response('simplekey/species.html', {
           'pilegroup': pilegroup,
           'pile': pile,
           'scientific_name': scientific_name,
           'scientific_name_short': scientific_name_short,
           'taxon': taxon,
           'images': images,
           'partner_heading': partner_species.species_page_heading
               if partner_species else None,
           'partner_blurb': partner_species.species_page_blurb
               if partner_species else None,
           'habitats': habitats,
           'compact_multivalue_characters': COMPACT_MULTIVALUE_CHARACTERS,
           'brief_characteristics': preview_characters,
           'all_characteristics': characters_by_group,
           'specific_epithet': specific_name_slug,
           'last_plant_id_url': last_plant_id_url,
           'in_simple_key': partner_species.simple_key,
           'native_to_north_america': native_to_north_america
           }, context_instance=RequestContext(request))

def _get_plants():
    plants = Taxon.objects.values(
        'scientific_name', 'common_names__common_name', 'family__name',
        'distribution', 'north_american_native',
        'north_american_introduced', 'wetland_indicator_code',
        'piles__pilegroup__friendly_title',
        'piles__friendly_title'
        ).order_by('scientific_name')
    return plants

def _compute_plants_etag(request):
    """Generate an ETag for allowing caching of the species list page.
    This requires querying for the plants upon every page request but
    saves much response bandwidth and keeps everything up-to-date
    automatically.
    """
    plants = _get_plants()
    h = hashlib.md5()
    h.update(str(list(plants)))
    return h.hexdigest()

@etag(_compute_plants_etag)
def species_list_view(request):
    return render_to_response('simplekey/species_list.html', {
        'plants': _get_plants()
        })


def genus_view(request, genus_slug):
    genus = get_object_or_404(Genus, slug=genus_slug.lower())

    # If it is decided that common names will not be required, change the
    # default below to None so the template will omit the name if missing.
    DEFAULT_COMMON_NAME = 'common name here'
    common_name = genus.common_name or DEFAULT_COMMON_NAME

    genus_drawings = genus.images.filter(image_type__name='example drawing')
    if not genus_drawings:
        # No example drawings for this genus were specified. Including
        # drawings here was planned early on but not finished for the
        # initial release. In the meantime, the first two species
        # images from the genus are shown.
        species = genus.taxa.all()
        for s in species:
            species_images = botany.species_images(s)
            if len(species_images) > 1:
                genus_drawings = species_images[0:2]
                break
    genus_drawings = _images_with_copyright_holders(genus_drawings)

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
        # No example drawings for this family were specified. Including
        # drawings here was planned early on but not finished for the
        # initial release. In the meantime, the first two species
        # images from the family are shown.
        species = family.taxa.all()
        for s in species:
            species_images = botany.species_images(s)
            if len(species_images) > 1:
                family_drawings = species_images[0:2]
                break
    family_drawings = _images_with_copyright_holders(family_drawings)

    pile = family.taxa.all()[0].piles.all()[0]
    pilegroup = pile.pilegroup

    return render_to_response('simplekey/family.html', {
           'family': family,
           'common_name': common_name,
           'family_drawings': family_drawings,
           'pilegroup': pilegroup,
           'pile': pile,
           }, context_instance=RequestContext(request))

def legal_redirect_view(request):
    return redirect('privacy-policy')

def privacy_policy_view(request):
    return render_to_response('simplekey/privacy.html',
            context_instance=RequestContext(request))

def terms_of_use_view(request):
    site_url = request.build_absolute_uri(reverse('simplekey-index'))
    return render_to_response('simplekey/terms.html',
            { 'site_url' : site_url },
            context_instance=RequestContext(request))

def help_redirect_view(request):
    return redirect('simplekey-help-start')

def help_about_view(request):
    return render_to_response('simplekey/help_about.html', {
           }, context_instance=RequestContext(request))

@vary_on_headers('Host')
def help_start_view(request):
    youtube_id = ''
    getting_started_video = Video.objects.get(title='Getting Started')
    if getting_started_video:
        youtube_id = getting_started_video.youtube_id

    return render_to_response(
        per_partner_template(request, 'simplekey/help_start.html'), {
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

def _get_video_dict(title, video):
    youtube_id = ''
    if video:
        youtube_id = video.youtube_id
    return {
        'title': title,
        'youtube_id': youtube_id
    }

def help_video_view(request):
    # The Getting Started video is first, followed by videos for the pile
    # groups and piles in the order that they are presented in the stepwise
    # pages at the beginning of plant identification.
    videos = []
    getting_started_video = Video.objects.get(title='Getting Started')
    if getting_started_video:
        videos.append({'title': getting_started_video.title,
                       'youtube_id': getting_started_video.youtube_id});

    for pilegroup in ordered_pilegroups():
        videos.append(_get_video_dict(pilegroup.name, pilegroup.video))
        for pile in ordered_piles(pilegroup):
            videos.append(_get_video_dict(pile.name, pile.video))

    return render_to_response('simplekey/help_video.html', {
           'videos': videos,
           }, context_instance=RequestContext(request))

def suggest_view(request):
    # Return some search suggestions for the auto-suggest feature.
    MAX_RESULTS = 10
    query = request.GET.get('q', '').lower()
    suggestions = []
    if query != '':
        # This query is case-sensitive for better speed than using a
        # case-insensitive query. The database field is also case-
        # sensitive, so it is important that all SearchSuggestion
        # records be lowercased before import to ensure that they
        # can be reached.
        suggestions = list(SearchSuggestion.objects.filter(
            term__startswith=query).order_by('term').values_list('term',
            flat=True)[:MAX_RESULTS * 2])   # Fetch extra in case of
                                            # case-sensitive duplicates
        # Remove any duplicates due to case-sensitivity and pare down to
        # the desired number of results.
        suggestions = list(sorted(set([suggestion.lower()
            for suggestion in suggestions])))[:MAX_RESULTS]

    return HttpResponse(simplejson.dumps(suggestions),
                        mimetype='application/json')

def sitemap_view(request):
    host = request.get_host()
    plant_names = Taxon.objects.values_list('scientific_name', flat=True)
    families = Family.objects.values_list('name', flat=True)
    genera = Genus.objects.values_list('name', flat=True)
    urls = ['http://%s/species/%s/' % (host,
                                       plant_name.lower().replace(' ', '/'))
            for plant_name in plant_names]
    urls.extend(['http://%s/families/%s/' % (host, family_name.lower())
                 for family_name in families])
    urls.extend(['http://%s/genera/%s/' % (host, genus_name.lower())
                 for genus_name in genera])
    return render_to_response('simplekey/sitemap.txt', {
           'urls': urls,
           }, mimetype='text/plain; charset=utf-8')

def robots_view(request):
    return render_to_response('simplekey/robots.txt', {},
                              context_instance=RequestContext(request),
                              mimetype='text/plain')

def checkup_view(request):

    # Do some checks that can be presented on an unlinked page to be
    # verified either manually or by an automated functional test.

    # Check the number of images that have valid copyright holders.
    total_images = models.ContentImage.objects.count()
    copyright_holders = CopyrightHolder.objects.values_list('coded_name',
                                                            flat=True)
    images_without_copyright = []
    images = models.ContentImage.objects.all()
    for image in images:
        image_url = image.image.url
        copyright_holder = image_url.split('.')[-2]
        if re.search('-[a-z0-9]?$', copyright_holder):
            copyright_holder = copyright_holder[:-2]
        copyright_holder = copyright_holder.split('-')[-1]
        if copyright_holder not in copyright_holders:
            images_without_copyright.append(image_url)
            # To see which images do not have valid copyright holders,
            # temporarily enable this statement:
            #print 'Copyright holder %s not found: %s' % (copyright_holder,
            #                                             image_url)
    images_copyright = total_images - len(images_without_copyright)

    return render_to_response('simplekey/checkup.html', {
            'images_copyright': images_copyright,
            'total_images': total_images,
        }, context_instance=RequestContext(request))


def teaching_tools_view(request, template):
    return render_to_response(template, {
            }, context_instance=RequestContext(request))


# Placeholder views
# This generic view basically does the same thing as direct_to_template,
# but I wanted to be more explicit so placeholders would be obvious when it
# was time to replace them (e.g. delete this view and any placeholder not yet
# replaced will become an error).
def placeholder_view(request, template):
    return render_to_response(template, {
            }, context_instance=RequestContext(request))

