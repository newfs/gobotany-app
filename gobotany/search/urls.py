from django.conf.urls.defaults import patterns, url
from haystack.forms import HighlightedSearchForm

from gobotany.search.views import GoBotanySearchView

urlpatterns = patterns(
    '',

    # Search results page.
    url(r'^search/$', GoBotanySearchView(
            template='simplekey/search.html',
            form_class=HighlightedSearchForm,
            ),
        name='search'),
    )
