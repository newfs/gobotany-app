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
    url(r'^sightings/locator/$', views.sightings_locator_view,
        name='ps-sightings-locator'),
    url(r'^sightings/(?P<sighting_id>[0-9]+)/$', views.sighting_view,
        name='ps-sighting'),

    # Post a (new) Sighting form
    url(r'^sightings/new/$', views.new_sighting_view, name='ps-new-sighting'),
    url(r'^sightings/new/done/$', views.new_sighting_done_view,
        name='ps-new-sighting-done'),

    # My Profile page
    url(r'^profile/$', views.profile_view, name='ps-profile'),

    # Staff-Only area urls
    url(r'^staff/images$', views.screen_images, name='ps-screen-images'),

    # AJAX urls
    url(r'^api/edit-profile$', views.ajax_profile_edit,
        name='ps-ajax-profile-edit'),
    url(r'^api/image-upload$', views.ajax_image_upload,
        name='ps-ajax-image-upload'),
    url(r'^api/sightings/$', views.ajax_sightings, name='ps-ajax-sightings'),
    )
