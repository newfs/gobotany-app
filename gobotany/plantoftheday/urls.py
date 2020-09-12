from django.urls import path

from gobotany.plantoftheday import views

urlpatterns = [
    path('', views.atom_view, name='plantoftheday-feed'),
    path('atom.xml', views.atom_view, name='plantoftheday-feed-atom'),
]
