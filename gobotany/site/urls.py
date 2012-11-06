from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

from gobotany.site import views

urlpatterns = patterns(
    '',

    # Home page
    url(r'^$', views.home_view, name='site-home'),

    # Sitemap and robots.txt files for search engines
    url('^sitemap.txt$', views.sitemap_view, name='sitemap'),
    url('^robots.txt$', views.robots_view, name='robots'),

    # Teaching page
    url('^teaching/$', views.teaching_view, name='site-teaching'),

    # About section
    url(r'^about/$', views.about_view, name='site-about'),
    url(r'^start/$', views.getting_started_view, name='site-getting-started'),
    url(r'^map/$', views.advanced_map_view, name='site-advanced-map'),
    url(r'^glossary/(?P<letter>[1a-z])/$', views.glossary_view,
        name='site-glossary'),
    url(r'^glossary/$', views.glossary_main_view, name='site-glossary-main'),
    url(r'^video/$', views.video_view, name='site-video'),
    url(r'^contributors/$', views.contributors_view,
        name='site-contributors'),

    # Legal notification pages
    url('^privacy/$', views.privacy_view, name='site-privacy'),
    url('^terms-of-use/$', views.terms_of_use_view, name='site-terms-of-use'),

    # API calls for input suggestions
    url(r'^search-suggestions/', views.search_suggestions_view,
        name='site-search-suggestions'),
    url(r'^plant-name-suggestions/', views.plant_name_suggestions_view,
        name='site-plant-name-suggestions'),

    # Temporary placeholder pages for unreleased features
    url('^plantshare/$', views.placeholder_view,
        {'template': 'gobotany/plantshare_placeholder.html'},
        name='plantshare-placeholder'),   # TODO: Use this URL at release
    # TODO: redirect these URLs at release
    url('^advanced/$', views.placeholder_view,
        {'template': 'gobotany/advanced.html'},
        name='advanced-id-tools'),
    url('^advanced/full-key/$', views.placeholder_view,
        {'template': 'gobotany/full_key_placeholder.html'},
        name='full-key-placeholder'),
    url('^advanced/dich-key/$', views.placeholder_view,
        {'template': 'gobotany/dich_key_placeholder.html'},
        name='dich-key-placeholder'),

    # Redirects for old URLs
    url('^teaching-tools/$', redirect_to, {'url': '/teaching/'}),
    url(r'^help/about/$', redirect_to, {'url': '/about/'}),
    url(r'^help/start/$', redirect_to, {'url': '/start/'}),
    url('^help/map/$', redirect_to, {'url': '/map/'}),
    url('^help/glossary/(?P<letter>[1a-z])/$', redirect_to,
        {'url': '/glossary/%(letter)s/'}),
    url('^help/glossary/$', redirect_to, {'url': '/glossary/'}),
    url('^help/video/$', redirect_to, {'url': '/video/'}),
    url('^help/contributors/$', redirect_to, {'url': '/contributors/'}),
    url('^legal/privacy-policy/$', redirect_to, {'url': '/privacy/'}),
    url('^legal/terms-of-use/$', redirect_to, {'url': '/terms/'}),

    # Temporary, for testing
    url('^maps-test/$', views.maps_test_view, name='site-maps-test'),
    url('^suggest-test/$', views.suggest_test_view, name='site-suggest-test'),
    )
