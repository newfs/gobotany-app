from django.conf.urls import url
from haystack.forms import HighlightedSearchForm

from gobotany.search.views import GoBotanySearchView

urlpatterns = [
    # Search results page.
    url(r'^search/$', GoBotanySearchView(template='search.html',
        form_class=HighlightedSearchForm,
        ), name='search'),
]
