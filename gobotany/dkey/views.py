from django.shortcuts import get_object_or_404, render_to_response
from gobotany.dkey.models import Couplet

def index(request):
    return render_to_response('dkey/index.html')

def couplet(request, slug):
    title = slug.replace('-', ' ')
    couplet = get_object_or_404(Couplet, title=title)
    return render_to_response('dkey/couplet.html', {
            'couplet': couplet,
            })
