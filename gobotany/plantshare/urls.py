from django.conf.urls.defaults import patterns, url

from gobotany.plantshare import views

urlpatterns = patterns(
    '',

    # PlantShare main page
    url(r'^$', views.plantshare_view, name='ps-main'),

    )
