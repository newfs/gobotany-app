from django.conf.urls import patterns, url
from django.views.generic import RedirectView

from gobotany.taxa import views

urlpatterns = patterns(
    '',

    url('^family/(?P<family_slug>[a-z]+)/$',
        views.family_view, name='taxa-family'),
    url('^genus/(?P<genus_slug>[a-z]+)/$',
        views.genus_view, name='taxa-genus'),
    url('^species/(?P<genus_slug>[a-z]+)/(?P<epithet>[-a-z]+)/$',
        views.species_view, name='taxa-species'),

    # Support "hackable" URL
    url('^species/(?P<genus_slug>[a-z]+)/$',
        RedirectView.as_view(url='/genus/%(genus_slug)s/')),

    # Redirections for old URLs

    (r'^families/(?P<family_slug>[a-z]+)/$',
        RedirectView.as_view(url='/family/%(family_slug)s/')),

    (r'^genera/(?P<genus_slug>[a-z]+)/$',
        RedirectView.as_view(url='/genus/%(genus_slug)s/')),

    (r'^(?P<pilegroup_slug>[-a-z]+)/(?P<pile_slug>[-a-z]+)/'
     r'(?P<genus_slug>[a-z]+)/(?P<epithet>[-a-z]+)/$', RedirectView.as_view(
         url='/species/%(genus_slug)s/%(epithet)s/?pile=%(pile_slug)s')),

    (r'^family/(?P<family_slug>[a-zA-Z]+)/$',
        views.UppercaseFamilyRedirectView.as_view()),

    (r'^genus/(?P<genus_slug>[a-zA-Z]+)/$',
        views.UppercaseGenusRedirectView.as_view()),

    (r'^species/(?P<genus_slug>[a-zA-Z]+)/(?P<epithet>[-a-z]+)/$',
        views.SpeciesUppercaseGenusRedirectView.as_view()),
    )
