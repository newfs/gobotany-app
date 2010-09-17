from django.conf.urls.defaults import patterns, url
from haystack.forms import HighlightedSearchForm
from haystack.views import SearchView
from gobotany.simplekey import views

urlpatterns = patterns(
    '',

    # Custom index page.
    url(r'^search/$', SearchView(
            template='simplekey/search.html',
            form_class=HighlightedSearchForm,
            ),
        name='simplekey_search'),

    # Simple key navigation
    url('^$', views.index_view),
    url('^glossary/(?P<letter>[1a-z])/$',
        views.glossary_view, name='simplekey-glossary'),
    url('^map/$', views.map_view),
    url('^(?P<number>[0-9]+)/$', views.page_view),
    url('^(?P<pilegroup_slug>[^/]*)/$',
        views.pilegroup_view, name='simplekey-pilegroup'),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.results_view, name='simplekey-pile'),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/' \
        '(?P<genus_slug>[^/]*)/(?P<specific_epithet_slug>[^/]*)/$',
        views.species_view, name='simplekey-species'),
    )
