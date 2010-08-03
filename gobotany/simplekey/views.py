from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from gobotany.core.models import Pile, PileGroup
from gobotany.simplekey.models import Collection, get_blurb


def get_simple_url(item):
    """Return the URL to where `item` lives in the Simple Key navigation."""
    if isinstance(item, Collection):
        return item.get_absolute_url()
    elif isinstance(item, Pile):
        return reverse('gobotany.simplekey.views.pile_view',
                       kwargs={'name': item.name})
    else:
        raise ValueError('the Simple Key has no URL for %r' % (item,))


def create_subway(item=None):
    """Create a subway map based at the Collection or Pile `item`."""
    if item is None:
        item = Collection.objects.get(slug='start')
    yield { 'item': item, 'url': get_simple_url(item) }
    if hasattr(item, 'get_children'):
        children = item.get_children()
        if children:
            yield 'indent'
            for child in children:
                for thing in create_subway(child['object']):
                    yield thing
            yield 'dedent'


def index_view(request):
    blurb = get_blurb('index_instructions')
    return render_to_response(
        'simplekey/index.html', {'blurb': blurb},
        context_instance=RequestContext(request))


def viewify(cdict):
    """Supplement a {'kind': k, 'object': o} dictionary with more info."""
    thing = cdict['object']
    cdict['class'] = thing.__class__.__name__.lower()
    cdict['url'] = get_simple_url(thing)
    if isinstance(thing, Collection):
        cdict['friendly_name'] = thing.name
    elif isinstance(thing, Pile):
        cdict['friendly_name'] = thing.friendly_name or thing.name
    return cdict


def collection_view(request, slug):
    collection = get_object_or_404(Collection, slug=slug)
    children = [ viewify(cdict) for cdict in collection.get_children() ]
    return render_to_response(
        'simplekey/collection.html', {
            'collection': collection,
            'children': children,
            'subway': create_subway(),
            }, context_instance=RequestContext(request))


def pile_view(request, name):
    pile = get_object_or_404(Pile, name=name)
    return render_to_response(
        'simplekey/pile.html',
        {'pile': pile, 'subway': create_subway()},
        context_instance=RequestContext(request))


def results_view(request, pile_group_name=None, pile_name=None):
    data = {}
    if pile_group_name:
        pile_group = get_object_or_404(PileGroup, name=pile_group_name)
        data['pile_group'] = pile_group
    if pile_name:
        pile = get_object_or_404(Pile, name=pile_name)
        data['pile'] = pile
    return render_to_response('simplekey/results.html', data,
        context_instance=RequestContext(request))
