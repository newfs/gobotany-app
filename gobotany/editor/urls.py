from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^cv/$', views.piles_view),
    url(r'^cv/([^/]+)-characters/$', views.pile_characters),
    url(r'^cv/([^/]+)-characters/([^/]+)/$', views.edit_pile_character),
    url(r'^cv/([^/]+)-taxa/$', views.pile_taxa),
    url(r'^cv/([^/]+)-taxa/([^/]+)/$', views.edit_pile_taxon),
    url(r'^cv/lit-sources/([.0-9]+)/$', views.edit_lit_sources),
    url(r'^partner/(\d+)/plants/$', views.partner_plants),
    url(r'^partner/(\d+)/plants/upload/$', views.partner_plants_upload),
    url(r'^partner(\d+)-plants.csv$', views.partner_plants_csv),
    url(r'^.*', views.e404),  # prevent fall-through to wildcard rewrite URL
]
