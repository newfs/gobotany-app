from django.conf.urls.defaults import patterns, url, include

from gobotany.plantshare import views

urlpatterns = patterns(
    '',

    # PlantShare main page
    url(r'^$', views.plantshare_view, name='ps-main'),

    url(r'^join/$', views.join_view, name='ps-join'),

    # Facebook login
    url(r'^facebook_connect/', include('facebook_connect.urls')),
    # Normal registration login
    url(r'^accounts/', include('registration.backends.default.urls')),
    )
