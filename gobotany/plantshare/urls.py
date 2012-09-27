from django.conf.urls.defaults import patterns, url, include

from gobotany.plantshare import views

urlpatterns = patterns(
    '',

    # PlantShare main page
    url(r'^$', views.plantshare_view, name='ps-main'),

    # Facebook login
    url(r'^facebook_connect/', include('facebook_connect.urls')),
    # Normal registration login
    url(r'^accounts/', include('gobotany.plantshare.backends.default.urls')),

    # Sightings
    url(r'^sightings/$', views.sightings_view, name='ps-sightings'),

    # Post a (new) Sighting form
    url(r'^sightings/new/$', views.new_sighting_view, name='ps-new-sighting'),

    # My Profile page
    url(r'^profile/$', views.profile_view, name='ps-profile'),
    )
