from django.conf.urls.defaults import patterns, url

from gobotany.site import views

urlpatterns = patterns(
    '',
    url(r'^about/', views.about_view, name='site-about'),
    url(r'^getting-started/', views.getting_started_view,
        name='site-getting-started'),
    )
