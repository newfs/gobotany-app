from django.conf.urls.defaults import patterns, url

from haystack.forms import HighlightedSearchForm

from gobotany.search.views import GoBotanySearchView
from gobotany.simplekey import views

urlpatterns = patterns(
    '',

    # Search results page.
    url(r'^search/$', GoBotanySearchView(
            template='simplekey/search.html',
            form_class=HighlightedSearchForm,
            ),
        name='search'),

    # Hidden test pages.
    url('^_maptest/$', views.maptest),

    # Temporary placeholder pages, to eventually be replaced with new 
    # features / apps rather than flat views
    url('^plantshare/$', views.placeholder_view, 
        {'template' : 'simplekey/plantshare_placeholder.html'},
        name='plantshare-placeholder'),
    url('^teaching-tools/$', views.placeholder_view, 
        {'template' : 'simplekey/teaching_placeholder.html'},
        name='teaching-tools-placeholder'),
    url('^advanced/full-key/$', views.placeholder_view, 
        {'template' : 'simplekey/full_key_placeholder.html'},
        name='full-key-placeholder'),
    url('^advanced/dich-key/$', views.placeholder_view, 
        {'template' : 'simplekey/dich_key_placeholder.html'},
        name='dich-key-placeholder'),

    # Legal notification pages
    url('^legal/$', views.legal_redirect_view, name='legal'),
    url('^legal/privacy-policy/$', views.privacy_policy_view, name='privacy-policy'),
    url('^legal/terms-of-use/$', views.terms_of_use_view, name='terms-of-use'),

    # Auto-suggestions for search
    url('^suggest/$', views.suggest_view, name='simplekey-search-suggest'),

    # Site pages
    url('^$', views.index_view, name='simplekey-index'),
    url('^advanced/$', views.advanced_view, name='advanced-id-tools'),
    url('^help/$', views.help_redirect_view, name='simplekey-help'),
    url('^help/start/$', views.help_start_view, name='simplekey-help-start'),
    url('^help/about/$', views.help_about_view, name='simplekey-help-about'),
    url('^help/map/$', views.help_map_view, name='simplekey-help-map'),
    url('^help/glossary/(?P<letter>[1a-z])/$', views.help_glossary_view,
        name='simplekey-help-glossary'),
    url('^help/glossary/$', views.help_glossary_redirect_view,
        name='simplekey-help-glossary0'),
    url('^help/video/$', views.help_video_view, name='simplekey-help-video'),
    url('^help/video/(?P<pilegroup_slug>[^/]*)/$',
        views.video_pilegroup_view, name='simplekey-help-video-pilegroup'),
    url('^help/video/(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.video_pile_view, name='simplekey-help-video-pile'),
    url('^guided-search/$', views.guided_search_view),
    url('^families/(?P<family_slug>[^/]*)/$',
        views.family_view, name='simplekey-family'),
    url('^genera/(?P<genus_slug>[^/]*)/$',
        views.genus_view, name='simplekey-genus'),
    url('^species/(?P<genus_slug>[^/]*)/(?P<specific_name_slug>[^/]*)/$',
        views.species_view, name='simplekey-species'),
    url('^species/(?P<genus_slug>[^/]*)/$',
        views.genus_redirect_view, name='simplekey-genus-redirect'),
    url('^simple/$', views.simple_key_view, name='simplekey'),
    url('^(?P<pilegroup_slug>[^/]*)/$',
        views.pilegroup_view, name='simplekey-pilegroup'),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.results_view, name='simplekey-pile'),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/' \
        '(?P<genus_slug>[^/]*)/(?P<specific_name_slug>[^/]*)/$',
        views.species_view, name='simplekey-pile-species'),
    )
