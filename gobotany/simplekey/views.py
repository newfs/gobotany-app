from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from gobotany.core.models import Pile
from gobotany.simplekey.models import Collection

def index_view(request):
    return render_to_response(
        'simplekey/index.html', {},
        context_instance=RequestContext(request))

def collection_view(request, slug):
    collection = get_object_or_404(Collection, slug=slug)
    choices = []
    for line in collection.contents.split('\r\n'):
        fields = line.split(None, 1)
        if fields[0] == 'pile':
            obj = get_object_or_404(Pile, name=fields[1])
            url = reverse('gobotany.simplekey.views.pile_view',
                          kwargs={'name': fields[1]})
        else:
            obj = get_object_or_404(Collection, slug=fields[1])
            url = obj.get_absolute_url()
        choices.append({ 'type': fields[0], 'target': obj, 'url': url })
    return render_to_response(
        'simplekey/collection.html',
        {'collection': collection, 'choices': choices},
        context_instance=RequestContext(request))

def pile_view(request, name):
    pile = get_object_or_404(Pile, name=name)
    return render_to_response(
        'simplekey/pile.html', {'pile': pile},
        context_instance=RequestContext(request))
