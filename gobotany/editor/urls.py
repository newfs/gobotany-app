from django.conf.urls.defaults import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^cv/$', views.piles_view),
    url(r'^cv/([^/]+)-characters/$', views.pile_characters),
    url(r'^cv/([^/]+)-characters/([^/]+)/$', views.edit_pile_character),
    url(r'^cv/([^/]+)-taxa/$', views.pile_taxa),
    url(r'^cv/([^/]+)-taxa/([^/]+)/$', views.edit_pile_taxon),
    url(r'^.*', views.e404),  # prevent fall-through to wildcard rewrite URL
    )
