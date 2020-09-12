from django.urls import path
from haystack.forms import HighlightedSearchForm

from gobotany.search.views import GoBotanySearchView

urlpatterns = [
    # Search results page.
    path('search/', GoBotanySearchView(template='search.html',
        form_class=HighlightedSearchForm,
        ), name='search'),
]
