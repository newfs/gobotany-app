from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from gobotany.core.models import Pile, PileGroup
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


def create_subway(item=None):
    """Create a subway map based at the Page, PileGroup, or Pile `item`."""
    if item is None:
        item = Page.objects.get(number=1)
    yield { 'item': item, 'url': get_simple_url(item) }

    if isinstance(item, Page):
        children = item.pilegroups.all()
    elif isinstance(item, PileGroup):
        children = item.piles.all()
    else:
        children = ()

    if children:
        yield 'indent'
        for child in children:
            for thing in create_subway(child):
                yield thing
        yield 'dedent'

    if isinstance(item, Page) and item.next_page is not None:
        for thing in create_subway(item.next_page):
            yield thing


def index_view(request):
    blurb = get_blurb('index_instructions')
    return render_to_response(
        'simplekey/index.html', {'blurb': blurb},
        context_instance=RequestContext(request))


def page_view(request, number):
    try:
        number = int(number)
    except ValueError:
        raise Http404
    page = get_object_or_404(Page, number=number)
    return render_to_response('simplekey/page.html', {
            'page': page,
            'subway': create_subway(),
            'pilegroups_and_urls': [
                (pilegroup, get_simple_url(pilegroup))
                for pilegroup in page.pilegroups.order_by('id').all()
                ]
            }, context_instance=RequestContext(request))


def pilegroup_view(request, pilegroup_slug):
    pilegroup = get_object_or_404(PileGroup, slug=pilegroup_slug)
    return render_to_response('simplekey/pilegroup.html', {
            'pilegroup': pilegroup,
            'subway': create_subway(),
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
           'subway': create_subway(),
           }, context_instance=RequestContext(request))
