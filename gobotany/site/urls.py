from django.urls import path, re_path
from django.views.generic.base import RedirectView

from gobotany.site import views

urlpatterns = [
    # Home page
    path('', views.home_view, name='site-home'),

    # Sitemap and robots.txt files for search engines
    path('sitemap.txt', views.sitemap_view, name='sitemap'),
    path('robots.txt', views.robots_view, name='robots'),

    # Teaching page
    path('teaching/', views.teaching_view, name='site-teaching'),

    # Help section
    path('help/', views.help_view, name='site-help'),
    path('help/dkey/', views.help_dkey_view, name='site-help-dkey'),
    path('updates/family/', views.updates_family_view,
        name='site-updates-family'),
    path('updates/', views.updates_date_view, name='site-updates-date'),
    path('start/', views.getting_started_view, name='site-getting-started'),
    path('video/', views.video_view, name='site-video'),
    path('map/', views.advanced_map_view, name='site-advanced-map'),
    re_path(r'^glossary/(?P<letter>[1a-z])/$', views.glossary_view,
        name='site-glossary'),
    path('glossary/', views.glossary_main_view, name='site-glossary-main'),
    path('advanced/', views.placeholder_view,
        {'template': 'gobotany/advanced.html'}, name='advanced-id-tools'),
    path('requirements/', views.system_requirements_view,
        name='site-system-requirements'),
    path('about/', views.about_view, name='site-about'),
    path('contributors/', views.contributors_view, name='site-contributors'),
    path('privacy/', views.privacy_view, name='site-privacy'),
    path('terms-of-use/', views.terms_of_use_view, name='site-terms-of-use'),
    path('contact/', views.contact_view, name='site-contact'),

    # "Species List" page, linked to from the About | Advanced Map page
    path('list/', views.species_list_view, name='species-list'),
    # API calls for input suggestions
    path('search-suggestions/', views.search_suggestions_view,
        name='site-search-suggestions'),
    path('plant-name-suggestions/', views.plant_name_suggestions_view,
        name='site-plant-name-suggestions'),

    # Redirects for old and "higher-level" URLs
    path('teaching-tools/', RedirectView.as_view(url='/teaching/',
        permanent=True)),
    path('help/about/', RedirectView.as_view(url='/about/',
        permanent=True)),
    path('help/start/', RedirectView.as_view(url='/start/',
        permanent=True)),
    path('help/map/', RedirectView.as_view(url='/map/',
        permanent=True)),
    re_path('^help/glossary/(?P<letter>[1a-z])/$',
        RedirectView.as_view(url='/glossary/%(letter)s/',
            permanent=True)),
    path('help/glossary/', RedirectView.as_view(url='/glossary/',
        permanent=True)),
    path('help/video/', RedirectView.as_view(url='/video/',
        permanent=True)),
    path('help/contributors/', RedirectView.as_view(url='/contributors/',
        permanent=True)),
    path('legal/privacy-policy/', RedirectView.as_view(url='/privacy/',
        permanent=True)),
    path('legal/terms-of-use/', RedirectView.as_view(url='/terms-of-use/',
        permanent=True)),
    path('advanced/full-key/', RedirectView.as_view(url='/full/',
        permanent=True)),
    path('advanced/dich-key/', RedirectView.as_view(url='/dkey/',
        permanent=True)),

    # Unlinked pages for development and testing: even though unlinked,
    # comment out at release time anyway

    # Unlinked page for some checks that can be verified via functional test
    #path('checkup/', views.checkup_view, name='checkup'),

    # Temporary, for testing
    #path('maps-test/', views.maps_test_view, name='site-maps-test'),
]