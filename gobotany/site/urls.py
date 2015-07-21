from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

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

    # Help section
    url(r'^help/$', views.help_view, name='site-help'),
    url(r'^help/dkey/$', views.help_dkey_view, name='site-help-dkey'),
    url(r'^start/$', views.getting_started_view, name='site-getting-started'),
    url(r'^video/$', views.video_view, name='site-video'),
    url(r'^map/$', views.advanced_map_view, name='site-advanced-map'),
    url(r'^glossary/(?P<letter>[1a-z])/$', views.glossary_view,
        name='site-glossary'),
    url(r'^glossary/$', views.glossary_main_view, name='site-glossary-main'),
    url('^advanced/$', views.placeholder_view,
        {'template': 'gobotany/advanced.html'}, name='advanced-id-tools'),
    url(r'^requirements/', views.system_requirements_view,
        name='site-system-requirements'),
    url(r'^about/$', views.about_view, name='site-about'),
    url(r'^contributors/$', views.contributors_view,
        name='site-contributors'),
    url('^privacy/$', views.privacy_view, name='site-privacy'),
    url('^terms-of-use/$', views.terms_of_use_view, name='site-terms-of-use'),
    url('^contact/$', views.contact_view, name='site-contact'),

    # "Species List" page, linked to from the About | Advanced Map page
    url('^list/$', views.species_list_view, name='species-list'),
    # API calls for input suggestions
    url(r'^search-suggestions/', views.search_suggestions_view,
        name='site-search-suggestions'),
    url(r'^plant-name-suggestions/', views.plant_name_suggestions_view,
        name='site-plant-name-suggestions'),

    # Redirects for old URLs
    url('^teaching-tools/$', RedirectView.as_view(url='/teaching/',
        permanent=True)),
    url(r'^help/about/$', RedirectView.as_view(url='/about/',
        permanent=True)),
    url(r'^help/start/$', RedirectView.as_view(url='/start/',
        permanent=True)),
    url('^help/map/$', RedirectView.as_view(url='/map/',
        permanent=True)),
    url('^help/glossary/(?P<letter>[1a-z])/$',
        RedirectView.as_view(url='/glossary/%(letter)s/',
            permanent=True)),
    url('^help/glossary/$', RedirectView.as_view(url='/glossary/',
        permanent=True)),
    url('^help/video/$', RedirectView.as_view(url='/video/',
        permanent=True)),
    url('^help/contributors/$', RedirectView.as_view(url='/contributors/',
        permanent=True)),
    url('^legal/privacy-policy/$', RedirectView.as_view(url='/privacy/',
        permanent=True)),
    url('^legal/terms-of-use/$', RedirectView.as_view(url='/terms-of-use/',
        permanent=True)),
    url('^advanced/full-key/$', RedirectView.as_view(url='/full/',
        permanent=True)),
    url('^advanced/dich-key/$', RedirectView.as_view(url='/dkey/',
        permanent=True)),

    # Unlinked pages for development and testing: even though unlinked,
    # comment out at release time anyway

    # Unlinked page for some checks that can be verified via functional test
    #url('^checkup/$', views.checkup_view, name='checkup'),

    # Temporary, for testing
    url('^maps-test/$', views.maps_test_view, name='site-maps-test'),
    )
