from django.conf.urls import url

from gobotany.plantoftheday import views

urlpatterns = [
    url('^$', views.atom_view, name='plantoftheday-feed'),
    url('^atom.xml$', views.atom_view, name='plantoftheday-feed-atom'),
]
