# -*- coding: utf-8 -*-

import json
import re
import string

from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.decorators.vary import vary_on_headers

from gobotany.core import botany
from gobotany.core.models import (
    CommonName, ConservationStatus, ContentImage, CopyrightHolder,
    Family, Genus, GlossaryTerm, HomePageImage, PartnerSite, PartnerSpecies,
    Pile, Taxon, Video,
    )
from gobotany.core.partner import (which_partner, partner_short_name,
                                   per_partner_template,
                                   render_to_response_per_partner)
from gobotany.plantoftheday.models import PlantOfTheDay
from gobotany.simplekey.groups_order import ordered_pilegroups, ordered_piles
from gobotany.site.models import PlantNameSuggestion, SearchSuggestion
from gobotany.site.utils import query_regex

# Home page

@vary_on_headers('Host')
def home_view(request):
    """View for the home page of the Go Botany site."""

    partner = which_partner(request)

    # Get home page images for the partner
    home_page_images = HomePageImage.objects.filter(partner_site=partner)

    # Get or generate today's Plant of the Day, if appropriate.
    plant_of_the_day = PlantOfTheDay.get_by_date.for_day(
        date.today(), partner.short_name)
    plant_of_the_day_taxon = None
    if plant_of_the_day:
        # Get the Taxon record of the Plant of the Day.
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

    return render_to_response_per_partner('home.html', {
            'home_page_images': home_page_images,
            'plant_of_the_day': plant_of_the_day_taxon,
            'plant_of_the_day_image': plant_of_the_day_image,
            }, request)

# Teaching page

@vary_on_headers('Host')
def teaching_view(request):
    return render_to_response_per_partner('teaching.html', {
            }, request)

# Help section

@vary_on_headers('Host')
def help_view(request):
    return render_to_response_per_partner('help.html', {
           }, request)

@vary_on_headers('Host')
def help_dkey_view(request):
    return render_to_response_per_partner('help_dkey.html', {
           }, request)

@vary_on_headers('Host')
def about_view(request):
    return render_to_response_per_partner('about.html', {
           }, request)

@vary_on_headers('Host')
def getting_started_view(request):
    youtube_id = ''
    getting_started_video = Video.objects.get(title='Getting Started')
    if getting_started_video:
        youtube_id = getting_started_video.youtube_id

    return render_to_response_per_partner('getting_started.html', {
            'getting_started_youtube_id': youtube_id,
            }, request)

@vary_on_headers('Host')
def advanced_map_view(request):
    pilegroups = [(pilegroup, ordered_piles(pilegroup))
                  for pilegroup in ordered_pilegroups()]

    return render_to_response_per_partner('advanced_map.html', {
            'pilegroups': pilegroups
            }, request)

@vary_on_headers('Host')
def glossary_view(request, letter):
    glossary = GlossaryTerm.objects.filter(visible=True).extra(
        select={'lower_term': 'lower(term)'}).order_by('lower_term')

    terms = glossary.values_list('lower_term', flat=True)
    letters_in_glossary = [term[0] for term in terms]

    # Skip any glossary terms that start with a number, and filter to the
    # desired letter.
    glossary = glossary.filter(term__gte='a', term__startswith=letter)

    return render_to_response_per_partner('glossary.html', {
            'this_letter': letter,
            'letters': string.ascii_lowercase,
            'letters_in_glossary': letters_in_glossary,
            'glossary': glossary,
            }, request)

def glossary_main_view(request):
    return redirect('site-glossary', letter='a')

def _get_video_dict(title, video):
    """Return a dictionary with a video title and the YouTube ID. This
    is to handle plant group and subgroup videos which are still missing
    from the database: at least their titles will appear on the page.
    """
    youtube_id = ''
    if video:
        youtube_id = video.youtube_id
    return {
        'title': title,
        'youtube_id': youtube_id
    }

@vary_on_headers('Host')
def video_view(request):
    # The Getting Started video is first, followed by videos for the pile
    # groups and piles in the order that they are presented in the stepwise
    # pages at the beginning of plant identification.
    videos = []
    getting_started_video = Video.objects.get(title='Getting Started')
    if getting_started_video:
        videos.append({'title': getting_started_video.title,
                       'youtube_id': getting_started_video.youtube_id});

    for pilegroup in ordered_pilegroups():
        videos.append(_get_video_dict(pilegroup.friendly_title,
                                      pilegroup.video))
        for pile in ordered_piles(pilegroup):
            videos.append(_get_video_dict(pile.friendly_title, pile.video))

    return render_to_response_per_partner('video.html', {
           'videos': videos,
           }, request)

@vary_on_headers('Host')
def contributors_view(request):
    return render_to_response_per_partner('contributors.html', {
       }, request)

def contact_view(request):
    return render_to_response_per_partner('contact.html', {}, request)

@vary_on_headers('Host')
def privacy_view(request):
    return render_to_response_per_partner('privacy.html', {}, request)

@vary_on_headers('Host')
def terms_of_use_view(request):
    site_url = request.build_absolute_uri(reverse('site-home'))
    return render_to_response_per_partner('terms.html', {
            'site_url': site_url,
            }, request)

# API calls for input suggestions (search, plant names, etc.)

def search_suggestions_view(request):
    """Return some search suggestions for search."""
    MAX_RESULTS = 10
    query = request.GET.get('q', '').lower()
    suggestions = []
    if query != '':
        regex = query_regex(query)

        # Make a variation for checking at the start of the string.
        regex_at_start = '^%s' % regex

        # First look for suggestions that match at the start of the
        # query string.

        # This query is case-sensitive for better speed than using a
        # case-insensitive query. The database field is also case-
        # sensitive, so it is important that all SearchSuggestion
        # records be lowercased before import to ensure that they
        # can be reached.
        suggestions = list(SearchSuggestion.objects.filter(
            term__iregex=regex_at_start).exclude(term=query).
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
                term__iregex=regex).exclude(term__iregex=regex_at_start).
                order_by('term').values_list('term', flat=True)
                [:MAX_RESULTS * 2])
            more_suggestions = list(sorted(set([suggestion.lower()
                for suggestion in  more_suggestions])))[:remaining_slots]
            suggestions.extend(more_suggestions)

    return HttpResponse(json.dumps(suggestions),
                        mimetype='application/json; charset=utf-8')

# Plant name suggestions API call

def plant_name_suggestions_view(request):
    """Return some suggestions for plant name input."""
    MAX_RESULTS = 10
    query = request.GET.get('q', '').lower()

    suggestions = []
    if query != '':
        regex = query_regex(query)

        # Make a variation for checking at the start of the string.
        regex_at_start = '^%s' % regex

        # First look for suggestions that match at the start of the
        # query string.
        suggestions = list(PlantNameSuggestion.objects.filter(
            name__iregex=regex_at_start).exclude(name=query).
            order_by('name').values_list('name', flat=True)[:MAX_RESULTS])

        # If fewer than the maximum number of suggestions were found,
        # try finding some additional ones that match anywhere in the
        # query string.
        remaining_slots = MAX_RESULTS - len(suggestions)
        if remaining_slots > 0:
            more_suggestions = list(PlantNameSuggestion.objects.filter(
                name__iregex=regex).exclude(name__iregex=regex_at_start).
                order_by('name').values_list('name', flat=True)[:MAX_RESULTS])
            more_suggestions = list(more_suggestions)[:remaining_slots]
            suggestions.extend(more_suggestions)

    return HttpResponse(json.dumps(suggestions),
                        mimetype='application/json; charset=utf-8')


# Maps test page

@vary_on_headers('Host')
def maps_test_view(request):
    return render_to_response_per_partner('maps_test.html', {
           }, request)


# Placeholder views
# This generic view basically does the same thing as direct_to_template,
# but I wanted to be more explicit so placeholders would be obvious when it
# was time to replace them (e.g. delete this view and any placeholder not yet
# replaced will become an error).
def placeholder_view(request, template):
    return render_to_response(template, {
            }, context_instance=RequestContext(request))


# Sitemap.txt and robots.txt views

def sitemap_view(request):
    URL_FORMAT = '%s://%s%s'
    PROTOCOL = 'http'   # TODO: change when moving to https
    host = request.get_host()

    partner_name = partner_short_name(request)
    partner_site = PartnerSite.objects.get(short_name=partner_name)
    partner_species = PartnerSpecies.objects.filter(
        partner=partner_site).values_list('species__scientific_name',
                                          'species__family__name',
                                          'species__genus__name')
    plant_names = sorted([species.lower()
                          for (species, family, genus) in partner_species])
    families = sorted(set([family.lower()
                           for (species, family, genus) in partner_species]))
    genera = sorted(set([genus.lower()
                         for (species, family, genus) in partner_species]))
    urls = [URL_FORMAT % (
                PROTOCOL,
                host,
                reverse('taxa-species', args=(plant_name.split(' '))))
            for plant_name in plant_names]
    urls.extend([URL_FORMAT % (PROTOCOL,
                               host,
                               reverse('taxa-family', args=([family_name])))
                 for family_name in families])
    urls.extend([URL_FORMAT % (PROTOCOL,
                               host,
                               reverse('taxa-genus', args=([genus_name])))
                 for genus_name in genera])
    return render_to_response('gobotany/sitemap.txt', {
            'urls': urls,
            },
            context_instance=RequestContext(request),
            content_type='text/plain; charset=utf-8')

def robots_view(request):
    return render_to_response('gobotany/robots.txt', {},
                              context_instance=RequestContext(request),
                              content_type='text/plain')


@vary_on_headers('Host')
def checkup_view(request):

    # Do some checks that can be presented on an unlinked page to be
    # verified either manually or by an automated functional test.

    # Check the number of images that have valid copyright holders.
    total_images = ContentImage.objects.count()
    copyright_holders = CopyrightHolder.objects.values_list('coded_name',
                                                            flat=True)
    images_without_copyright = []
    images = ContentImage.objects.all()
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

    return render_to_response_per_partner('checkup.html', {
            'images_copyright': images_copyright,
            'total_images': total_images,
        }, request)


@vary_on_headers('Host')
def species_list_view(request):
    partner = which_partner(request)

    plants_list = list(PartnerSpecies.objects.values(
            'species__id', 'species__scientific_name',
            'species__family__name', 'species__north_american_native',
            'species__north_american_introduced',
            'species__wetland_indicator_code',
        ).filter(partner=partner).order_by('species__scientific_name'))

    # Strip off the species__ prefix from the list's dictionary keys.
    for plant in plants_list:
        for key in plant:
            if '__' in key:
                new_key = key.replace('species__', '')
                plant[new_key] = plant.pop(key)

    # We build these three related lists manually instead of tempting
    # _get_plants() to return N * M copies of each plant.

    for plantdict in plants_list:
        plantdict['common_names'] = []
        plantdict['pile_titles'] = []
        plantdict['pilegroup_titles'] = []
        plantdict['states'] = set()

        scientific_name = plantdict['scientific_name']
        plantdict['genus'], plantdict['epithet'] = scientific_name.split()[:2]
        plantdict['lowgenus'] = plantdict['genus'].lower()

    plantmap = {
        plantdict['id']: plantdict for plantdict in plants_list
    }

    q = CommonName.objects.values_list('common_name', 'taxon_id')
    for common_name, taxon_id in q:
        if taxon_id in plantmap:
            plantmap[taxon_id]['common_names'].append(common_name)

    q = ConservationStatus.objects.filter(label='present').values_list(
        'taxon_id', 'region',
        )
    for taxon_id, region in q:
        if taxon_id in plantmap:
            plantmap[taxon_id]['states'].add(region)

    q = Pile.species.through.objects.values_list(
        'taxon_id', 'pile__friendly_title', 'pile__pilegroup__friendly_title',
        )
    for taxon_id, pile_title, pilegroup_title in q:
        if taxon_id in plantmap:
            # Skip adding the "big Remaining Non-Monocots" pile's title,
            # since that pile has been split from the user's standpoint.
            # (Once the pile is fully split in the database, this check
            # can be removed.) 
            if pile_title != 'All other herbaceous, flowering dicots':
                plantmap[taxon_id]['pile_titles'].append(pile_title)
                plantmap[taxon_id]['pilegroup_titles'].append(pilegroup_title)

    for plantdict in plants_list:
        plantdict['states'] = ' '.join(sorted(plantdict['states'])).upper()

    return render_to_response_per_partner('species_list.html', {
        'plants': plants_list,
        }, request)
