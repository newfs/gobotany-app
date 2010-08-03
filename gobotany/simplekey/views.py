from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from gobotany.core.models import Pile, PileGroup
from gobotany.simplekey.models import Collection, get_blurb

def get_map():
    """Return the hierarchy of collections and piles."""
    


def index_view(request):
    blurb = get_blurb('index_instructions')
    return render_to_response(
        'simplekey/index.html', {'blurb': blurb},
        context_instance=RequestContext(request))


def collection_view(request, slug):
    collection = get_object_or_404(Collection, slug=slug)
    print collection.get_children()
    return render_to_response(
        'simplekey/collection.html',
        {'collection': collection, 'map': get_map()},
        context_instance=RequestContext(request))


def pile_view(request, name):
    pile = get_object_or_404(Pile, name=name)
    return render_to_response(
        'simplekey/pile.html', {'pile': pile},
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
