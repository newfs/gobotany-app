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
    url('^(?P<key>simple|full)/$', views.level1, name='level1'),
    url('^(?P<key>simple|full)/(?P<pilegroup_slug>[^/]*)/$',
        views.level2, name='level2'),
    url('^(?P<key>simple|full)/(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.level3, name='level3'),

    # Legacy redirections.

    (r'^families/(?P<family_slug>[a-z]+)/$',
     redirect_to, {'url': '/family/%(family_slug)s/'}),
    (r'^genera/(?P<genus_slug>[a-z]+)/$',
     redirect_to, {'url': '/genus/%(genus_slug)s/'}),

    (r'^(?P<pilegroup_slug>[-a-z]+)/(?P<pile_slug>[-a-z]+)/'
     r'(?P<genus_slug>[a-z]+)/(?P<epithet>[-a-z]+)/$', redirect_to,
     {'url': '/species/%(genus_slug)s/%(epithet)s/?pile=%(pile_slug)s'}),

    # Old URLs at which the Simple Key 2nd and 3rd-level pages once lived.

    url('^(?P<pilegroup_slug>[^/]*)/$',
        views.redirect_pilegroup_to_simple),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.redirect_pile_to_simple),
    )
