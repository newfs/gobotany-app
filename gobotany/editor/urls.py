from django.urls import path, re_path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('cv/', views.piles_view),
    re_path(r'^cv/([^/]+)-characters/$', views.pile_characters),
    re_path(r'^cv/([^/]+)-characters/([^/]+)/$', views.edit_pile_character),
    re_path(r'^cv/([^/]+)-taxa/$', views.pile_taxa),
    re_path(r'^cv/([^/]+)-taxa/([^/]+)/$', views.edit_pile_taxon),
    re_path(r'^cv/lit-sources/([.0-9]+)/$', views.edit_lit_sources),
    re_path(r'^partner/(\d+)/plants/$', views.partner_plants),
    re_path(r'^partner/(\d+)/plants/upload/$', views.partner_plants_upload),
    re_path(r'^partner(\d+)-plants.csv$', views.partner_plants_csv),
    path('dkey/', views.dkey),
    path('dkey/<slug:slug>/', views.dkey),
    re_path(r'^.*', views.e404), # prevent fall-thru to wildcard rewrite URL
]
