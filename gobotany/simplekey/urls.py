from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

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

    # Temporary placeholder pages, to eventually be replaced with new 
    # features / apps rather than flat views
    url('^plantshare/$', views.placeholder_view, 
        {'template' : 'simplekey/plantshare_placeholder.html'},
        name='plantshare-placeholder'),
    url('^advanced/full-key/$', views.placeholder_view, 
        {'template' : 'simplekey/full_key_placeholder.html'},
        name='full-key-placeholder'),
    url('^advanced/dich-key/$', views.placeholder_view, 
        {'template' : 'simplekey/dich_key_placeholder.html'},
        name='dich-key-placeholder'),

    url('^teaching/$', views.teaching_view,
        {'template': 'simplekey/teaching.html'}, name='teaching'),
    url('^teaching-tools/$', views.teaching_redirect,
        name='teaching-redirect'),   # redirect old URL

    # Legal notification pages
    url('^legal/$', views.legal_redirect_view, name='legal'),
    url('^legal/privacy-policy/$', views.privacy_policy_view, name='privacy-policy'),
    url('^legal/terms-of-use/$', views.terms_of_use_view, name='terms-of-use'),

    # Auto-suggestions for search
    url('^suggest/$', views.suggest_view, name='simplekey-search-suggest'),

    # Sitemap and robots.txt files for search engines
    url('^sitemap.txt$', views.sitemap_view, name='sitemap'),
    url('^robots.txt$', views.robots_view, name='robots'),

    # Unlinked page for some checks that can be verified via functional test
    url('^checkup/$', views.checkup_view, name='checkup'),

    # Site pages
    url('^advanced/$', views.advanced_view, name='advanced-id-tools'),
    url('^list/$', views.species_list_view, name='species-list'),
    url('^family/(?P<family_slug>[a-z]+)/$',
        views.family_view, name='simplekey-family'),
    url('^genus/(?P<genus_slug>[a-z]+)/$',
        views.genus_view, name='simplekey-genus'),
    url('^species/(?P<genus_slug>[a-z]+)/(?P<epithet>[-a-z]+)/$',
        views.species_view, name='simplekey-species'),
    url('^species/(?P<genus_slug>[a-z]+)/$',
        redirect_to, {'url': '/genus/%(genus_slug)s/'}),
    url('^simple/$', views.simple_key_view, name='simplekey'),

    # Legacy redirections.

    (r'^families/(?P<family_slug>[a-z]+)/$',
     redirect_to, {'url': '/family/%(family_slug)s/'}),
    (r'^genera/(?P<genus_slug>[a-z]+)/$',
     redirect_to, {'url': '/genus/%(genus_slug)s/'}),

    (r'^(?P<pilegroup_slug>[-a-z]+)/(?P<pile_slug>[-a-z]+)/'
     r'(?P<genus_slug>[a-z]+)/(?P<epithet>[-a-z]+)/$', redirect_to,
     {'url': '/species/%(genus_slug)s/%(epithet)s/?pile=%(pile_slug)s'}),

    # If these were under /simplekey/ they would not have to go last.

    url('^(?P<pilegroup_slug>[^/]*)/$',
        views.pilegroup_view, name='simplekey-pilegroup'),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.results_view, name='simplekey-pile'),
    )
