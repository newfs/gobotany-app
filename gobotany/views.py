from django.template.loader import get_template
from django.template import RequestContext
from django.http import HttpResponse

from gobotany import botany


def default_view(request):
    kwargs = {}
    if request.method == 'POST':
        kwargs['queried'] = True
        s = kwargs['s'] = request.POST['s'].strip()
        kwargs['query_results'] = botany.query_species(
            scientific_name=s)

    t = get_template('index.html')
    html = t.render(RequestContext(request, kwargs))
    return HttpResponse(html)
