from django.conf.urls import patterns, url

from gobotany.plantoftheday import views

urlpatterns = patterns(
    '',

    url('^$', views.atom_view, name='plantoftheday-feed'),
    url('^atom.xml$', views.atom_view, name='plantoftheday-feed-atom'),
)
