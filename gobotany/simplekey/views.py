# -*- coding: utf-8 -*-
import hashlib
import re

from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.http import etag
from django.views.decorators.vary import vary_on_headers

from gobotany.core import models
from gobotany.core.models import (
        CopyrightHolder, Family, Genus, Pile, PileGroup, Taxon
    )
from gobotany.core.partner import which_partner
from gobotany.simplekey.groups_order import ordered_pilegroups, ordered_piles
from gobotany.simplekey.models import (GroupsListPage,
                                       SubgroupResultsPage,
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

    # For Issue #254, Full Key, mock up a possible solution
    if key.lower() == 'full':
        piles.append(piles[1])  # Duplicate the last pile

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
        }, context_instance=RequestContext(request))

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
    return redirect('/simple' + request.path, permanent=True)

def redirect_pile_to_simple(request, pilegroup_slug, pile_slug):
    pile = get_object_or_404(Pile, slug=pile_slug)
    if pile.pilegroup.slug != pilegroup_slug:
        raise Http404
    return redirect('/simple' + request.path, permanent=True)
