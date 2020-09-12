from django.urls import path
from django.views.generic import RedirectView

from gobotany.taxa import views

urlpatterns = [
    path('family/<slug:family_slug>/', views.family_view,
        name='taxa-family'),
    path('genus/<slug:genus_slug>/', views.genus_view,
        name='taxa-genus'),
    path('species/<slug:genus_slug>/<slug:epithet>/', views.species_view,
        name='taxa-species'),

    # Support "hackable" URL
    path('species/<slug:genus_slug>/', RedirectView.as_view(
        url='/genus/%(genus_slug)s/', permanent=True)),

    # Redirections for old URLs

    path('families/<slug:family_slug>/', RedirectView.as_view(
        url='/family/%(family_slug)s/', permanent=True)),

    path('genera/<slug:genus_slug>/', RedirectView.as_view(
        url='/genus/%(genus_slug)s/', permanent=True)),

    path('<slug:pilegroup_slug>/<slug:pile_slug>/'
        '<slug:genus_slug>/<slug:epithet>/', RedirectView.as_view(
        url='/species/%(genus_slug)s/%(epithet)s/?pile=%(pile_slug)s',
        permanent=True)),

    path('family/<slug:family_slug>/',
        views.UppercaseFamilyRedirectView.as_view()),

    path('genus/<slug:genus_slug>/',
        views.UppercaseGenusRedirectView.as_view()),

    path('species/<slug:genus_slug>/<slug:epithet>/',
        views.SpeciesUppercaseGenusRedirectView.as_view()),
]