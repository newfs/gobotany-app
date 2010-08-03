from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from gobotany.simplekey.models import Collection

def index_view(request):
    return render_to_response(
        'simplekey/index.html', {},
        context_instance=RequestContext(request))

def collection_view(request, slug):
    collection = get_object_or_404(Collection, slug=slug)
    return render_to_response(
        'simplekey/index.html', {'collection': collection},
        context_instance=RequestContext(request))
