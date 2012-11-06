# -*- coding: utf-8 -*-

import json
import string

from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.views.decorators.vary import vary_on_headers

from gobotany.core import botany
from gobotany.core.models import (Family, Genus, GlossaryTerm, HomePageImage,
                                  Taxon, Video)
from gobotany.core.partner import which_partner
from gobotany.plantoftheday.models import PlantOfTheDay
from gobotany.simplekey.groups_order import ordered_pilegroups, ordered_piles
from gobotany.site.models import PlantNameSuggestion, SearchSuggestion

def per_partner_template(request, template_path):
    partner = which_partner(request)
    return '{0}/{1}'.format(partner.short_name, template_path)

# Home page

def home_view(request):
    """View for the home page of the Go Botany site."""

    home_page_images = HomePageImage.objects.all()
    # Get or generate today's Plant of the Day.
    partner = which_partner(request)
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

    return render_to_response('gobotany/home.html', {
            'home_page_images': home_page_images,
            'plant_of_the_day': plant_of_the_day_taxon,
            'plant_of_the_day_image': plant_of_the_day_image,
            }, context_instance=RequestContext(request))

# Teaching page

def teaching_view(request):
    return render_to_response('gobotany/teaching.html', {
            }, context_instance=RequestContext(request))

# About section

def about_view(request):
    return render_to_response('gobotany/about.html', {
           }, context_instance=RequestContext(request))

@vary_on_headers('Host')
def getting_started_view(request):
    youtube_id = ''
    getting_started_video = Video.objects.get(title='Getting Started')
    if getting_started_video:
        youtube_id = getting_started_video.youtube_id

    return render_to_response(
        per_partner_template(request, 'getting_started.html'), {
            'getting_started_youtube_id': youtube_id,
            }, context_instance=RequestContext(request))

def advanced_map_view(request):
    pilegroups = [(pilegroup, ordered_piles(pilegroup))
                  for pilegroup in ordered_pilegroups()]

    return render_to_response('gobotany/advanced_map.html', {
            'pilegroups': pilegroups
            }, context_instance=RequestContext(request))

def glossary_view(request, letter):
    glossary = GlossaryTerm.objects.filter(visible=True).extra(
        select={'lower_term': 'lower(term)'}).order_by('lower_term')

    terms = glossary.values_list('lower_term', flat=True)
    letters_in_glossary = [term[0] for term in terms]

    # Skip any glossary terms that start with a number, and filter to the
    # desired letter.
    glossary = glossary.filter(term__gte='a', term__startswith=letter)

    return render_to_response('gobotany/glossary.html', {
            'this_letter': letter,
            'letters': string.ascii_lowercase,
            'letters_in_glossary': letters_in_glossary,
            'glossary': glossary,
            }, context_instance=RequestContext(request))

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

    return render_to_response('gobotany/video.html', {
           'videos': videos,
           }, context_instance=RequestContext(request))


def contributors_view(request):
    return render_to_response('gobotany/contributors.html', {
       }, context_instance=RequestContext(request))

# Legal notification pages

def privacy_view(request):
    return render_to_response('gobotany/privacy.html',
            context_instance=RequestContext(request))

def terms_of_use_view(request):
    site_url = request.build_absolute_uri(reverse('site-home'))
    return render_to_response('gobotany/terms.html', {
            'site_url': site_url,
            }, context_instance=RequestContext(request))

# API calls for input suggestions (search, plant names, etc.)

def search_suggestions_view(request):
    """Return some search suggestions for search."""
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

    return HttpResponse(json.dumps(suggestions),
                        mimetype='application/json; charset=utf-8')

# Plant name suggestions API call

def plant_name_suggestions_view(request):
    """Return some suggestions for plant name input."""
    MAX_RESULTS = 10
    query = request.GET.get('q', '').lower()

    suggestions = []
    if query != '':
        # First look for suggestions that match at the start of the
        # query string.

        # This query is case-insensitive to return names as they appear
        # in the database regardless of the case of the query string.
        suggestions = list(PlantNameSuggestion.objects.filter(
            name__istartswith=query).exclude(name=query).
            order_by('name').values_list('name', flat=True)[:MAX_RESULTS])

        # If fewer than the maximum number of suggestions were found,
        # try finding some additional ones that match anywhere in the
        # query string.
        remaining_slots = MAX_RESULTS - len(suggestions)
        if remaining_slots > 0:
            more_suggestions = list(PlantNameSuggestion.objects.filter(
                name__icontains=query).exclude(name__istartswith=query).
                order_by('name').values_list('name', flat=True)[:MAX_RESULTS])
            more_suggestions = list(more_suggestions)[:remaining_slots]
            suggestions.extend(more_suggestions)

    return HttpResponse(json.dumps(suggestions),
                        mimetype='application/json; charset=utf-8')


# Maps test page

def maps_test_view(request):
    return render_to_response('gobotany/maps_test.html', {
           }, context_instance=RequestContext(request))

# Input suggest test page

def suggest_test_view(request):
    return render_to_response('gobotany/suggest_test.html', {
           }, context_instance=RequestContext(request))


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
    return render_to_response('gobotany/sitemap.txt', {
           'urls': urls,
           }, mimetype='text/plain; charset=utf-8')

def robots_view(request):
    return render_to_response('gobotany/robots.txt', {},
                              context_instance=RequestContext(request),
                              mimetype='text/plain')

