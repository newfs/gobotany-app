# -*- coding: utf-8 -*-
import hashlib
import re
import string

from datetime import date
from itertools import groupby
from operator import itemgetter

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
    CopyrightHolder, Family, Genus,
    GlossaryTerm, Habitat, HomePageImage, Pile, PileGroup,
    PlantPreviewCharacter, Taxon, Video
    )
from gobotany.core.partner import which_partner
from gobotany.dkey import models as dkey_models
from gobotany.plantoftheday.models import PlantOfTheDay
from gobotany.simplekey.groups_order import ordered_pilegroups, ordered_piles
from gobotany.simplekey.models import (GroupsListPage,
                                       SearchSuggestion, SubgroupResultsPage,
                                       SubgroupsListPage)

# Character short names common to all piles (but no suffix)
COMMON_CHARACTERS = ['habitat', 'habitat_general', 'state_distribution']

#

def add_query_string(request, url):
    full = request.get_full_path()
    i = full.find('?')
    return url if (i == -1) else url + full[i:]

#

def per_partner_template(request, template_path):
    partner = which_partner(request)
    if partner and partner.short_name != 'gobotany':
        return '{0}/{1}'.format(partner.short_name, template_path)
    else:
        return template_path

#

def get_simple_url(key, pilegroup, pile=None):
    if pile is None:
        return reverse('gobotany.simplekey.views.level2',
                       kwargs={'key': key,
                               'pilegroup_slug': pilegroup.slug})
    else:
        return reverse('gobotany.simplekey.views.level3',
                       kwargs={'key': key,
                               'pilegroup_slug': pilegroup.slug,
                               'pile_slug': pile.slug})

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
def level1(request, key):
    partner = which_partner(request)
    short_name = _partner_short_name(partner)
    groups_list_page = GroupsListPage.objects.get()

    pilegroups = []
    for pilegroup in ordered_pilegroups():
        images = _images_with_copyright_holders(
            models.ContentImage.objects.filter(
                pilegroupimage__pile_group=pilegroup)
            .select_related('image_type'))
        pilegroups.append((pilegroup, images, get_simple_url(key, pilegroup)))

    return render_to_response('simplekey/simple.html', {
            'partner_site': short_name,
            'groups_list_page': groups_list_page,
            'key': key,
            'pilegroups': pilegroups
            }, context_instance=RequestContext(request))

@vary_on_headers('Host')
@cache_control(max_age=60 * 60)
@cache_page(60 * 60)
def level2(request, key, pilegroup_slug):
    pilegroup = get_object_or_404(PileGroup, slug=pilegroup_slug)

    partner = which_partner(request)
    short_name = _partner_short_name(partner)
    subgroups_list_page = SubgroupsListPage.objects.get(group=pilegroup)

    piles = []
    for pile in ordered_piles(pilegroup):
        images = _images_with_copyright_holders(
            models.ContentImage.objects.filter(pileimage__pile=pile)
            .select_related('image_type'))
        piles.append((pile, images, get_simple_url(key, pilegroup, pile)))

    return render_to_response('simplekey/pilegroup.html', {
            'partner_site': short_name,
            'subgroups_list_page': subgroups_list_page,
            'key': key,
            'pilegroup': pilegroup,
            'piles': piles
            }, context_instance=RequestContext(request))

def level3(request, key, pilegroup_slug, pile_slug):
    pile = get_object_or_404(Pile, slug=pile_slug)
    if pile.pilegroup.slug != pilegroup_slug:
        raise Http404

    partner = which_partner(request)
    short_name = _partner_short_name(partner)
    subgroup_results_page = SubgroupResultsPage.objects.get(subgroup=pile)

    return render_to_response('simplekey/results.html', {
           'key': key,
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


def _images_with_copyright_holders(images):
    # Reduce a live query object to a list to only run it once.
    if not isinstance(images, list):
        images = images.select_related('image_type').all()

    # Get the copyright holders for this set of images.
    codes = set(image.creator for image in images)
    chdict = {ch.coded_name: ch for ch
              in CopyrightHolder.objects.filter(coded_name__in=codes)}

    for image in images:
        # Grab each image's "scientific name" - or whatever string is
        # preceded by a ":" at the start of its alt text!

        image.scientific_name = (image.alt or '').split(':', 1)[0]

        # Associate each image with its copyright holder, adding the
        # copyright holder information as extra attributes.

        copyright_holder = chdict.get(image.creator)
        if not copyright_holder:
            continue
        image.copyright_holder_name = copyright_holder.expanded_name
        image.copyright = copyright_holder.copyright
        image.source = copyright_holder.source

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


def species_view(request, genus_slug, epithet):

    COMPACT_MULTIVALUE_CHARACTERS = ['Habitat', 'New England state',
                                     'Specific Habitat']

    genus_name = genus_slug.capitalize()
    scientific_name = '%s %s' % (genus_name, epithet)
    taxon = get_object_or_404(Taxon, scientific_name=scientific_name)

    scientific_name_short = '%s. %s' % (scientific_name[0], epithet)

    pile_slug = request.GET.get('pile')
    if pile_slug:
        pile = get_object_or_404(Pile, slug=pile_slug)
    else:
        # Randomly grab the first pile from the species
        pile = taxon.piles.order_by('id')[0]
    pilegroup = pile.pilegroup

    partner = which_partner(request)
    partner_species = None
    if partner:
        rows = models.PartnerSpecies.objects.filter(
            species=taxon, partner=partner).all()
        if rows:
            partner_species = rows[0]

    key = request.GET.get('key')
    if key == 'dichotomous':
        dkey_page = dkey_models.Page.objects.get(title=scientific_name)
    else:
        dkey_page = None
        key = ''  # prevent illegal value from reaching template

    species_images = botany.species_images(taxon)
    images = _images_with_copyright_holders(species_images)

    if taxon.habitat:
        habitat_names = taxon.habitat.split('| ')
        habitats = list(Habitat.objects.filter(name__in=habitat_names))
        habitats.sort()
    else:
        habitats = []

    # Get the set of preview characteristics.

    plant_preview_characters = {
        ppc.character_id: ppc.order for ppc in
        PlantPreviewCharacter.objects.filter(pile=pile, partner_site=partner)
        }

    # Select ALL character values for this taxon.

    character_values = list(taxon.character_values.select_related(
            'character', 'character__character_group'))

    # Throw away values for characters that are not part of this pile.

    pile_ids = (None, pile.id)  # things like Habitat have pile_id = None
    character_values = [ v for v in character_values
                         if v.character.pile_id in pile_ids ]

    # Create a tree of character groups, characters, and values.

    get_group_name = lambda v: v.character.character_group.name
    get_character_name = lambda v: v.character.friendly_name

    character_values.sort(key=get_character_name)
    character_values.sort(key=get_group_name)

    all_characteristics = []
    for group_name, seq1 in groupby(character_values, get_group_name):
        characters = []

        for character_name, seq2 in groupby(seq1, get_character_name):
            seq2 = list(seq2)
            character = seq2[0].character  # arbitrary; all look the same
            characters.append({
                'group': character.character_group.name,
                'name': character.friendly_name,
                'values': sorted(_format_character_value(v) for v in seq2),
                'in_preview': character.id in plant_preview_characters,
                'preview_order': plant_preview_characters.get(character.id, -1),
                })

        all_characteristics.append({
            'name': group_name,
            'characters': characters
            })

    # Pick out the few preview characters for separate display.

    preview_characters = sorted((
        character
        for group in all_characteristics
        for character in group['characters']
        if character['in_preview']
        ), key=itemgetter('preview_order'))

    native_to_north_america = _native_to_north_america_status(taxon)

    return render_to_response('simplekey/species.html', {
           'pilegroup': pilegroup,
           'pile': pile,
           'scientific_name': scientific_name,
           'scientific_name_short': scientific_name_short,
           'taxon': taxon,
           'key': key,
           'common_names': taxon.common_names.all(),  # view uses this 3 times
           'dkey_page': dkey_page,
           'images': images,
           'key': 'simple' if partner_species.simple_key else 'full',
           'partner_heading': partner_species.species_page_heading
               if partner_species else None,
           'partner_blurb': partner_species.species_page_blurb
               if partner_species else None,
           'habitats': habitats,
           'compact_multivalue_characters': COMPACT_MULTIVALUE_CHARACTERS,
           'brief_characteristics': preview_characters,
           'all_characteristics': all_characteristics,
           'epithet': epithet,
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

    genus_name = genus_slug.capitalize()
    genus = get_object_or_404(Genus, name=genus_name)

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


def family_view(request, family_slug):

    family_name = family_slug.capitalize()
    family = get_object_or_404(Family, name=family_name)

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

def suggest_view(request):
    # Return some search suggestions for the auto-suggest feature.
    MAX_RESULTS = 10
    query = request.GET.get('q', '').lower()
    suggestions = []
    if query != '':
        # First look for suggestions that match at the start of the
        # query string.

        # This query is case-sensitive for better speed than using a
        # case-insensitive query. The database field is also case-
        # sensitive, so it is important that all SearchSuggestion
        # records be lowercased before import to ensure that they
        # can be reached.
        suggestions = list(SearchSuggestion.objects.filter(
            term__startswith=query).exclude(term=query).
            order_by('term').values_list('term', flat=True)
            [:MAX_RESULTS * 2])   # Fetch extra to handle case-sensitive dups
        # Remove any duplicates due to case-sensitivity and pare down to
        # the desired number of results.
        suggestions = list(sorted(set([suggestion.lower()
            for suggestion in suggestions])))[:MAX_RESULTS]

        # If fewer than the maximum number of suggestions were found,
        # try finding some additional ones that match anywhere in the
        # query string.
        remaining_slots = MAX_RESULTS - len(suggestions)
        if remaining_slots > 0:
            more_suggestions = list(SearchSuggestion.objects.filter(
                term__contains=query).exclude(term__startswith=query).
                order_by('term').values_list('term', flat=True)
                [:MAX_RESULTS * 2])
            more_suggestions = list(sorted(set([suggestion.lower()
                for suggestion in  more_suggestions])))[:remaining_slots]
            suggestions.extend(more_suggestions)

    return HttpResponse(simplejson.dumps(suggestions),
                        mimetype='application/json')

def sitemap_view(request):
    host = request.get_host()
    plant_names = Taxon.objects.values_list('scientific_name', flat=True)
    families = Family.objects.values_list('name', flat=True)
    genera = Genus.objects.values_list('name', flat=True)
    urls = ['http://%s/species/%s/' % (host, plant_name.replace(' ', '/'))
            for plant_name in plant_names]
    urls.extend(['http://%s/families/%s/' % (host, family_name)
                 for family_name in families])
    urls.extend(['http://%s/genera/%s/' % (host, genus_name)
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


# Placeholder views
# This generic view basically does the same thing as direct_to_template,
# but I wanted to be more explicit so placeholders would be obvious when it
# was time to replace them (e.g. delete this view and any placeholder not yet
# replaced will become an error).
def placeholder_view(request, template):
    return render_to_response(template, {
            }, context_instance=RequestContext(request))

# We have moved the 2nd and 3rd level Simple Key pages beneath /simple/
# so we need these redirections in place for a while.

def redirect_pilegroup_to_simple(request, pilegroup_slug):
    get_object_or_404(PileGroup, slug=pilegroup_slug)
    return redirect('/simple' + request.path)

def redirect_pile_to_simple(request, pilegroup_slug, pile_slug):
    pile = get_object_or_404(Pile, slug=pile_slug)
    if pile.pilegroup.slug != pilegroup_slug:
        raise Http404
    return redirect('/simple' + request.path)
