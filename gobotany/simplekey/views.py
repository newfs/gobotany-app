# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.vary import vary_on_headers

from gobotany.core.models import ContentImage, Pile, PileGroup
from gobotany.core.partner import (partner_short_name,
                                   render_to_response_per_partner)
from gobotany.search.models import (GroupsListPage,
                                    SubgroupResultsPage,
                                    SubgroupsListPage)
from gobotany.simplekey.groups_order import ordered_pilegroups, ordered_piles
from gobotany.taxa.views import _images_with_copyright_holders

#

def add_query_string(request, url):
    full = request.get_full_path()
    i = full.find('?')
    return url if (i == -1) else url + full[i:]

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



def level3_test_links(request):
    '''Temporary page for Level 3 page user testing on smartphones.'''
    piles = []
    for pilegroup in ordered_pilegroups():
        for pile in ordered_piles(pilegroup):
            piles.append((pile, get_simple_url('simple', pilegroup, pile)))
    return render_to_response('level3_test_links.html', {
            'piles': piles
        })


@vary_on_headers('Host')
@cache_control(max_age=60 * 60)
@cache_page(60 * 60)
def level1(request, key):
    short_name = partner_short_name(request)
    groups_list_page = GroupsListPage.objects.get()

    pilegroups = []
    for pilegroup in ordered_pilegroups():
        images = _images_with_copyright_holders(
            ContentImage.objects.filter(
                pilegroupimage__pile_group=pilegroup)
            .select_related('image_type'))
        pilegroups.append((pilegroup, images, get_simple_url(key, pilegroup)))

    return render_to_response_per_partner('simple.html', {
                'partner_site': short_name,
                'groups_list_page': groups_list_page,
                'key': key,
                'pilegroups': pilegroups
                }, request)

@vary_on_headers('Host')
@cache_control(max_age=60 * 60)
@cache_page(60 * 60)
def level2(request, key, pilegroup_slug):
    pilegroup = get_object_or_404(PileGroup, slug=pilegroup_slug)

    short_name = partner_short_name(request)
    subgroups_list_page = SubgroupsListPage.objects.get(group=pilegroup)

    piles = []
    for pile in ordered_piles(pilegroup):
        images = _images_with_copyright_holders(
            ContentImage.objects.filter(pileimage__pile=pile)
            .select_related('image_type'))
        piles.append((pile, images, get_simple_url(key, pilegroup, pile)))

    return render_to_response_per_partner('pilegroup.html', {
                'partner_site': short_name,
                'subgroups_list_page': subgroups_list_page,
                'key': key,
                'pilegroup': pilegroup,
                'piles': piles
                }, request)

@vary_on_headers('Host')
def level3(request, key, pilegroup_slug, pile_slug):
    pile = get_object_or_404(Pile, slug=pile_slug)
    if pile.pilegroup.slug != pilegroup_slug:
        raise Http404

    short_name = partner_short_name(request)
    subgroup_results_page = SubgroupResultsPage.objects.get(subgroup=pile)

    return render_to_response_per_partner('results.html', {
                'dev_flag': 1 if request.GET.has_key('dev') else 0,
                'key': key,
                'partner_site': short_name,
                'subgroup_results_page': subgroup_results_page,
                'pilegroup': pile.pilegroup,
                'pile': pile,
                }, request)


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
