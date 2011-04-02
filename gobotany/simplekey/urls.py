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

    # Hidden test pages.
    url('^_rulertest/$', views.rulertest),
    
    # Auto-suggestions for search
    url('^suggest/$', views.suggest_view, name='simplekey-search-suggest'),

    # Site pages
    url('^$', views.index_view, name='simplekey-index'),
    url('^advanced/$', views.advanced_view, name='advanced-id-tools'),
    url('^help/$', views.help_about_view, name='simplekey-help-about'),
    url('^help/start/$', views.help_start_view, name='simplekey-help-start'),
    url('^help/collections/$', views.help_collections_view,
        name='simplekey-help-collections'),
    url('^help/glossary/(?P<letter>[1a-z])/$', views.help_glossary_view,
        name='simplekey-help-glossary'),
    url('^help/glossary/$', views.help_glossary_redirect_view, 
        name='simplekey-help-glossary0'),
    url('^help/video/$', views.help_video_view, name='simplekey-help-video'),
    url('^help/video/(?P<pilegroup_slug>[^/]*)/$',
        views.video_pilegroup_view, name='simplekey-help-video-pilegroup'),
    url('^help/video/(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.video_pile_view, name='simplekey-help-video-pile'),
    url('^map/$', views.map_view),
    url('^guided-search/$', views.guided_search_view),
    url('^families/(?P<family_slug>[^/]*)/$',
        views.family_view, name='simplekey-family'),
    url('^genera/(?P<genus_slug>[^/]*)/$',
        views.genus_view, name='simplekey-genus'),
    url('^species/(?P<genus_slug>[^/]*)/(?P<specific_epithet_slug>[^/]*)/$',
        views.species_view, name='simplekey-species'),
    url('^species/(?P<genus_slug>[^/]*)/$',
        views.genus_redirect_view, name='simplekey-genus-redirect'),
    url('^(?P<number>\d+)/$', views.page_view, name='simplekey-page'),
    url('^(?P<pilegroup_slug>[^/]*)/$',
        views.pilegroup_view, name='simplekey-pilegroup'),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.results_view, name='simplekey-pile'),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/' \
        '(?P<genus_slug>[^/]*)/(?P<specific_epithet_slug>[^/]*)/$',
        views.species_view, name='simplekey-pile-species'),
    )
