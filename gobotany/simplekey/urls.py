from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

from gobotany.simplekey import views

urlpatterns = patterns(
    '',

    # Sitemap and robots.txt files for search engines
    url('^sitemap.txt$', views.sitemap_view, name='sitemap'),
    url('^robots.txt$', views.robots_view, name='robots'),

    # Unlinked page for some checks that can be verified via functional test
    url('^checkup/$', views.checkup_view, name='checkup'),

    # Site pages
    url('^list/$', views.species_list_view, name='species-list'),
    url('^(?P<key>simple|full)/$', views.level1, name='level1'),
    url('^(?P<key>simple|full)/(?P<pilegroup_slug>[^/]*)/$',
        views.level2, name='level2'),
    url('^(?P<key>simple|full)/(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.level3, name='level3'),

    # Old URLs at which the Simple Key 2nd and 3rd-level pages once lived.

    url('^(?P<pilegroup_slug>[^/]*)/$',
        views.redirect_pilegroup_to_simple),
    url('^(?P<pilegroup_slug>[^/]*)/(?P<pile_slug>[^/]*)/$',
        views.redirect_pile_to_simple),
    )
