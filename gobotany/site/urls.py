from django.conf.urls.defaults import patterns, url

from gobotany.site import views

urlpatterns = patterns(
    '',
    url(r'^about/', views.about_view, name='site-help'),
    )
