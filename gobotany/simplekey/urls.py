from django.conf.urls.defaults import patterns, url
from haystack.forms import SearchForm
from haystack.query import SearchQuerySet
from haystack.views import SearchView
from gobotany.simplekey import views

urlpatterns = patterns(
    '',

    # Custom index page.
    url(r'^search/$', SearchView(
            template='simplekey/search.html',
            searchqueryset=SearchQuerySet(),
            form_class=SearchForm,
            ),
        name='simplekey_search'),

    # Simple key navigation
    url('^$', views.index_view),
    url('^(?P<number>[0-9]+)/$', views.page_view),
    url('^(?P<pilegroup_slug>[^/]*)/$', views.pilegroup_view),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.results_view),
    )
